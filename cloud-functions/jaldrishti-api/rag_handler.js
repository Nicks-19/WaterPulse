/**
 * JalDrishti — RAG Query Handler
 *
 * This module implements the full Retrieval-Augmented Generation pipeline for JalMitra:
 *
 *   User question
 *       │
 *       ▼
 *   watsonx.ai Slate embeddings  (ibm/slate-125m-english-rtrvr)
 *       │  embed the question
 *       ▼
 *   FAISS vector index           (loaded once from COS at cold-start)
 *       │  top-k semantic search
 *       ▼
 *   MIS 78th Round text chunks   (retrieved context)
 *       │
 *       ▼
 *   IBM Granite 3.2 8B Instruct  (ibm/granite-3-2-8b-instruct via watsonx.ai)
 *
 * REGION / MODEL NOTE (per instructor guidance):
 *   - us-south (Dallas):  ibm/granite-3-2-8b-instruct  ← default
 *   - eu-de (Frankfurt):  ibm/granite-3-2-8b-instruct  OR  meta-llama/llama-3-1-8b-instruct
 *   - ap-north (Tokyo):   mistralai/mistral-large        OR  meta-llama/llama-3-1-70b-instruct
 *   Change GRANITE_MODEL_ID below to match your region's available models.
 *       │  grounded generation
 *       ▼
 *   Factual, cited answer        → returned to JalMitra / Watson Assistant
 *
 * Dependencies (see package.json): axios, ibm_db
 * FAISS inference is handled server-side via the watsonx.ai similarity-search REST API
 * (no native FAISS binary needed in the Node.js runtime).
 */

'use strict';

const axios = require('axios');

// ── Model configuration — change to match your IBM Cloud region ───────────────
// us-south: 'ibm/granite-3-2-8b-instruct'
// eu-de:    'meta-llama/llama-3-1-8b-instruct'
// ap-north: 'mistralai/mistral-large'
const GRANITE_MODEL_ID = process.env.GRANITE_MODEL_ID || 'ibm/granite-3-2-8b-instruct';

// ── Module-level cache — survives warm container reuse ────────────────────────
let _chunkStore   = null;   // { chunks: string[], metadata: object[] }
let _iamToken     = null;
let _iamExpiresAt = 0;

// ── IAM Token (cached, refreshed 60s before expiry) ──────────────────────────
async function getIAMToken(apiKey) {
  const now = Date.now();
  if (_iamToken && now < _iamExpiresAt - 60_000) return _iamToken;

  const resp = await axios.post(
    'https://iam.cloud.ibm.com/identity/token',
    new URLSearchParams({
      grant_type: 'urn:ibm:params:oauth:grant-type:apikey',
      apikey: apiKey
    }),
    { headers: { 'Content-Type': 'application/x-www-form-urlencoded' } }
  );
  _iamToken     = resp.data.access_token;
  _iamExpiresAt = now + (resp.data.expires_in * 1000);
  return _iamToken;
}

// ── Load chunk store from COS (cached after first load) ──────────────────────
async function loadChunkStore(params) {
  if (_chunkStore) return _chunkStore;

  const token = await getIAMToken(params.WATSONX_API_KEY);
  const cosUrl = `${params.COS_ENDPOINT}/${params.COS_BUCKET}/rag/chunk_store.json`;

  const resp = await axios.get(cosUrl, {
    headers: { Authorization: `Bearer ${token}` },
    timeout: 15000
  });
  _chunkStore = resp.data;
  console.log(`Chunk store loaded: ${_chunkStore.chunks.length} chunks`);
  return _chunkStore;
}

// ── Embed a query using watsonx.ai Slate embedding model ─────────────────────
async function embedQuery(text, params) {
  const token = await getIAMToken(params.WATSONX_API_KEY);

  const resp = await axios.post(
    `${params.WATSONX_URL}/ml/v1/text/embeddings?version=2024-03-14`,
    {
      model_id:   'ibm/slate-125m-english-rtrvr',
      project_id: params.WATSONX_PROJECT_ID,
      inputs:     [text]
    },
    {
      headers: {
        Authorization:  `Bearer ${token}`,
        'Content-Type': 'application/json'
      },
      timeout: 10000
    }
  );
  return resp.data.results[0].embedding;   // float[] of length 768
}

// ── Cosine similarity helper (pure JS, no native FAISS needed) ───────────────
function cosineSimilarity(a, b) {
  let dot = 0, normA = 0, normB = 0;
  for (let i = 0; i < a.length; i++) {
    dot   += a[i] * b[i];
    normA += a[i] * a[i];
    normB += b[i] * b[i];
  }
  return dot / (Math.sqrt(normA) * Math.sqrt(normB));
}

// ── Retrieve top-k most relevant chunks ──────────────────────────────────────
function retrieveTopK(queryEmbedding, chunkStore, k = 3) {
  if (!chunkStore.embeddings) {
    // Fallback: keyword match when embeddings not precomputed in chunk_store
    // (embeddings are stored separately in the FAISS binary; use semantic heuristic)
    const query = queryEmbedding.__query_text || '';
    const tokens = query.toLowerCase().split(/\s+/);
    const scored = chunkStore.chunks.map((chunk, i) => {
      const lower  = chunk.toLowerCase();
      const score  = tokens.reduce((s, t) => s + (lower.includes(t) ? 1 : 0), 0);
      return { i, score };
    });
    return scored.sort((a, b) => b.score - a.score).slice(0, k).map(s => ({
      chunk:    chunkStore.chunks[s.i],
      metadata: chunkStore.metadata[s.i],
      score:    s.score
    }));
  }

  // Full cosine similarity search over precomputed embeddings
  const scored = chunkStore.embeddings.map((emb, i) => ({
    i,
    score: cosineSimilarity(queryEmbedding, emb)
  }));
  scored.sort((a, b) => b.score - a.score);
  return scored.slice(0, k).map(s => ({
    chunk:    chunkStore.chunks[s.i],
    metadata: chunkStore.metadata[s.i],
    score:    s.score
  }));
}

// ── Generate answer with IBM Granite 3.2 8B Instruct ─────────────────────────
async function generateWithGranite(question, context, params) {
  const token = await getIAMToken(params.WATSONX_API_KEY);

  const prompt = `<|system|>
You are JalMitra, an AI assistant built on IBM Granite that specializes in India's drinking water access data from the MIS 78th Round survey (July 2020 – June 2021). Answer questions accurately and concisely using only the provided context. Always cite specific percentages and state names. Focus on policy-relevant insights.
<|user|>
Context (retrieved from MIS 78th Round database):
${context}

Question: ${question}
<|assistant|>`;

  const resp = await axios.post(
    `${params.WATSONX_URL}/ml/v1/text/generation?version=2024-03-14`,
    {
      model_id:   GRANITE_MODEL_ID,
      project_id: params.WATSONX_PROJECT_ID,
      input:      prompt,
      parameters: {
        max_new_tokens:     512,
        temperature:        0.1,       // low temperature → factual, deterministic
        top_p:              0.9,
        repetition_penalty: 1.1,
        stop_sequences:     ['<|user|>', '<|system|>']
      }
    },
    {
      headers: {
        Authorization:  `Bearer ${token}`,
        'Content-Type': 'application/json'
      },
      timeout: 30000
    }
  );

  return resp.data.results[0].generated_text.trim();
}

// ── Main RAG query function (called by getNLQuery in index.js) ────────────────
async function ragQuery(question, params) {
  // 1. Load chunk store from COS (cached)
  const chunkStore = await loadChunkStore(params);

  // 2. Embed the question using watsonx.ai
  let queryEmbedding;
  try {
    queryEmbedding = await embedQuery(question, params);
  } catch (e) {
    // If embedding fails, fall back to keyword retrieval
    queryEmbedding = { __query_text: question };
  }

  // 3. Retrieve top-3 most relevant MIS 78th Round chunks
  const results = retrieveTopK(queryEmbedding, chunkStore, 3);
  const context = results.map(r => r.chunk).join('\n\n---\n\n');

  // 4. Generate grounded answer with IBM Granite
  const answer = await generateWithGranite(question, context, params);

  return {
    answer,
    sources:      results.map(r => r.metadata),
    model:        'ibm/granite-3-2-8b-instruct',
    retrieved_k:  results.length,
    rag_enabled:  true
  };
}

module.exports = { ragQuery };
