/**
 * JalDrishti — IBM Cloud Functions Handler  (v2.0 — Granite RAG Edition)
 * Platform: IBM Cloud Functions (Lite: 400,000 GB-s/month, 5M invocations free)
 *
 * Actions:
 *   1. getStateStats      — Query Db2 for state-level water access metrics
 *   2. getPrediction      — Call watsonx.ai scoring endpoint for SDG risk prediction
 *   3. listPriorityStates — Return top-N at-risk states sorted by sdg_risk_flag
 *   4. getNLQuery         — RAG pipeline: embed → FAISS retrieve → IBM Granite generate
 *                           (replaces previous hardcoded string responses)
 *
 * New in v2.0:
 *   - getNLQuery() powered by IBM Granite 3.2 8B Instruct via watsonx.ai
 *   - Retrieval-Augmented Generation using FAISS + Slate-125M embeddings
 *   - Chunk store loaded from COS at cold-start, cached across warm invocations
 */

'use strict';

const ibmdb     = require('ibm_db');
const axios     = require('axios');
const { ragQuery } = require('./rag_handler');

// ── Shared IAM Token Helper ────────────────────────────────────────────────────
async function getIAMToken(apiKey) {
  const resp = await axios.post(
    'https://iam.cloud.ibm.com/identity/token',
    new URLSearchParams({
      grant_type: 'urn:ibm:params:oauth:grant-type:apikey',
      apikey: apiKey
    }),
    { headers: { 'Content-Type': 'application/x-www-form-urlencoded' } }
  );
  return resp.data.access_token;
}

// ── Db2 Connection Helper ─────────────────────────────────────────────────────
function getDb2Connection(params) {
  return new Promise((resolve, reject) => {
    const dsn = [
      `DATABASE=${params.DB2_DATABASE || 'BLUDB'}`,
      `HOSTNAME=${params.DB2_HOST}`,
      `PORT=${params.DB2_PORT || 30376}`,
      `PROTOCOL=TCPIP`,
      `UID=${params.DB2_UID}`,
      `PWD=${params.DB2_PWD}`,
      `SECURITY=SSL`
    ].join(';');

    ibmdb.open(dsn, (err, conn) => {
      if (err) reject(err);
      else resolve(conn);
    });
  });
}

// ════════════════════════════════════════════════════════════════════════════
// ACTION 1: getStateStats
// GET /api/states/{stateCode}?year=2023
// Returns: state water metrics from Db2
// ════════════════════════════════════════════════════════════════════════════
async function getStateStats(params) {
  const { stateCode, year = 2023 } = params;

  if (!stateCode) {
    return { statusCode: 400, body: { error: 'stateCode is required' } };
  }

  let conn;
  try {
    conn = await getDb2Connection(params);

    const query = `
      SELECT state_name, year, rural_pct, urban_pct, total_pct,
             equity_gap, sdg61_proxy, yoy_change, sdg_risk_flag,
             cook_rural_pct, cook_urban_pct, migration_rate
      FROM JALDRISHTI.STATE_WATER_METRICS
      WHERE state_code = ?
        AND year = ?
      FETCH FIRST 1 ROW ONLY
    `;

    const rows = await new Promise((resolve, reject) => {
      conn.query(query, [parseInt(stateCode), parseInt(year)], (err, data) => {
        if (err) reject(err);
        else resolve(data);
      });
    });

    conn.close(() => {});

    if (!rows || rows.length === 0) {
      return { statusCode: 404, body: { error: `No data for state ${stateCode} in ${year}` } };
    }

    const r = rows[0];
    return {
      statusCode: 200,
      headers: { 'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*' },
      body: {
        state_name:       r.STATE_NAME,
        year:             r.YEAR,
        rural_pct:        parseFloat(r.RURAL_PCT),
        urban_pct:        parseFloat(r.URBAN_PCT),
        total_pct:        parseFloat(r.TOTAL_PCT),
        equity_gap:       parseFloat(r.EQUITY_GAP),
        sdg61_proxy:      parseFloat(r.SDG61_PROXY),
        yoy_change:       parseFloat(r.YOY_CHANGE),
        sdg_risk_flag:    parseInt(r.SDG_RISK_FLAG),
        cook_rural_pct:   parseFloat(r.COOK_RURAL_PCT),
        cook_urban_pct:   parseFloat(r.COOK_URBAN_PCT),
        migration_rate:   parseFloat(r.MIGRATION_RATE),
        sdg_status:       parseInt(r.SDG_RISK_FLAG) === 0 ? 'On Track' : 'At Risk'
      }
    };

  } catch (err) {
    if (conn) conn.close(() => {});
    return { statusCode: 500, body: { error: err.message } };
  }
}

// ════════════════════════════════════════════════════════════════════════════
// ACTION 2: getPrediction
// POST /api/predict
// Body: { rural_pct, urban_pct, equity_gap, cook_rural_pct, cook_urban_pct,
//         migration_rate, net_migration_000s, yoy_change }
// Returns: WML model prediction (risk label + probability)
// ════════════════════════════════════════════════════════════════════════════
async function getPrediction(params) {
  const {
    rural_pct, urban_pct, equity_gap,
    cook_rural_pct, cook_urban_pct,
    migration_rate, net_migration_000s, yoy_change,
    WML_API_KEY, WML_SCORING_URL
  } = params;

  const features = [rural_pct, urban_pct, equity_gap,
                    cook_rural_pct, cook_urban_pct,
                    migration_rate, net_migration_000s, yoy_change];

  if (features.some(f => f === undefined || f === null)) {
    return { statusCode: 400, body: { error: 'All 8 feature values are required' } };
  }

  try {
    const token = await getIAMToken(WML_API_KEY);

    const payload = {
      input_data: [{
        fields: [
          'rural_pct','urban_pct','equity_gap',
          'cook_rural_pct','cook_urban_pct',
          'migration_rate','net_migration_000s','yoy_change'
        ],
        values: [features.map(Number)]
      }]
    };

    const resp = await axios.post(WML_SCORING_URL, payload, {
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type':  'application/json'
      },
      timeout: 10000
    });

    const predictions = resp.data.predictions[0];
    const label       = predictions.values[0][0];
    const probabilities = predictions.values[0][1];

    return {
      statusCode: 200,
      headers: { 'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*' },
      body: {
        prediction:     label,
        sdg_status:     label === 0 ? 'On Track' : 'At Risk',
        confidence:     probabilities[label],
        risk_score:     parseFloat((probabilities[1] * 100).toFixed(1)),
        interpretation: label === 1
          ? 'This state requires urgent intervention to meet SDG 6.1 by 2030'
          : 'This state is on track. Continue current programs.'
      }
    };

  } catch (err) {
    return { statusCode: 500, body: { error: err.message } };
  }
}

// ════════════════════════════════════════════════════════════════════════════
// ACTION 3: listPriorityStates
// GET /api/priority?topN=10&year=2023
// Returns top-N at-risk states sorted by sdg61_proxy ASC
// ════════════════════════════════════════════════════════════════════════════
async function listPriorityStates(params) {
  const { topN = 10, year = 2023 } = params;

  let conn;
  try {
    conn = await getDb2Connection(params);

    const query = `
      SELECT state_name, rural_pct, urban_pct, equity_gap,
             sdg61_proxy, sdg_risk_flag, migration_rate
      FROM JALDRISHTI.STATE_WATER_METRICS
      WHERE year = ?
      ORDER BY sdg61_proxy ASC
      FETCH FIRST ${parseInt(topN)} ROWS ONLY
    `;

    const rows = await new Promise((resolve, reject) => {
      conn.query(query, [parseInt(year)], (err, data) => {
        if (err) reject(err);
        else resolve(data);
      });
    });

    conn.close(() => {});

    const states = (rows || []).map((r, idx) => ({
      rank:           idx + 1,
      state_name:     r.STATE_NAME,
      rural_pct:      parseFloat(r.RURAL_PCT),
      urban_pct:      parseFloat(r.URBAN_PCT),
      equity_gap:     parseFloat(r.EQUITY_GAP),
      sdg61_proxy:    parseFloat(r.SDG61_PROXY),
      sdg_risk_flag:  parseInt(r.SDG_RISK_FLAG),
      migration_rate: parseFloat(r.MIGRATION_RATE),
      priority_level: parseFloat(r.SDG61_PROXY) < 60
        ? 'CRITICAL' : parseFloat(r.SDG61_PROXY) < 75
        ? 'HIGH' : 'MEDIUM'
    }));

    return {
      statusCode: 200,
      headers: { 'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*' },
      body: { year, priority_states: states, total: states.length }
    };

  } catch (err) {
    if (conn) conn.close(() => {});
    return { statusCode: 500, body: { error: err.message } };
  }
}

// ════════════════════════════════════════════════════════════════════════════
// ACTION 4: getNLQuery — IBM Granite RAG-powered JalMitra handler  (v2.0)
//
// Pipeline:
//   User question (free-form natural language)
//       ↓
//   watsonx.ai Slate embedding (ibm/slate-125m-english-rtrvr)
//       ↓
//   FAISS semantic search over MIS 78th Round state chunks (top-3)
//       ↓
//   IBM Granite 3.2 8B Instruct (ibm/granite-3-2-8b-instruct)
//       ↓
//   Grounded, factual answer with cited state data
//
// Required params (set as Cloud Functions action params or .env.json):
//   WATSONX_API_KEY, WATSONX_URL, WATSONX_PROJECT_ID
//   COS_ENDPOINT, COS_BUCKET
// ════════════════════════════════════════════════════════════════════════════
async function getNLQuery(params) {
  // Validate required watsonx.ai params
  if (!params.WATSONX_API_KEY || !params.WATSONX_PROJECT_ID) {
    return {
      statusCode: 500,
      body: {
        response_text: 'JalMitra RAG is not configured. WATSONX_API_KEY and WATSONX_PROJECT_ID are required.',
        rag_enabled: false
      }
    };
  }

  // Build a natural-language question from Watson Assistant intent + entities
  // (also accepts a raw free-form `question` param from dashboard direct calls)
  const { intent, entities = [], question, input_text } = params;

  let naturalQuestion = question || input_text || '';

  if (!naturalQuestion) {
    // Reconstruct question from Watson Assistant intent + entity
    const stateName = entities.find(e => e.entity === 'state_name')?.value || '';
    const sector    = entities.find(e => e.entity === 'sector')?.value || '';

    const intentQuestions = {
      'query_water_access':           `What is the drinking water access situation in ${stateName} ${sector}?`,
      'query_equity_gap':             `What is the rural-urban water access equity gap in ${stateName}?`,
      'query_priority_states':        'Which states in India require the most urgent intervention for drinking water access?',
      'query_sdg_status':             `Is ${stateName} on track to meet SDG 6.1 (universal water access) by 2030?`,
      'query_cooking_fuel_correlation':'How does clean cooking fuel access relate to rural drinking water access across Indian states?',
      'query_migration':              `How does migration relate to water access in ${stateName || 'Indian states'}?`,
    };

    naturalQuestion = intentQuestions[intent]
      || `Tell me about drinking water access${stateName ? ' in ' + stateName : ' across Indian states'}.`;
  }

  try {
    // ── Full RAG pipeline ─────────────────────────────────────────────────────
    const ragResult = await ragQuery(naturalQuestion, {
      WATSONX_API_KEY:    params.WATSONX_API_KEY,
      WATSONX_URL:        params.WATSONX_URL || 'https://us-south.ml.cloud.ibm.com',
      WATSONX_PROJECT_ID: params.WATSONX_PROJECT_ID,
      COS_ENDPOINT:       params.COS_ENDPOINT || 'https://s3.us-south.cloud-object-storage.appdomain.cloud',
      COS_BUCKET:         params.COS_BUCKET   || 'jaldrishti-raw-data'
    });

    return {
      statusCode: 200,
      headers: { 'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*' },
      body: {
        response_text: ragResult.answer,
        question:      naturalQuestion,
        intent:        intent || 'direct_query',
        sources:       ragResult.sources,
        model:         ragResult.model,
        retrieved_k:   ragResult.retrieved_k,
        rag_enabled:   true
      }
    };

  } catch (err) {
    // Graceful fallback: return error details without crashing Watson Assistant
    return {
      statusCode: 500,
      headers: { 'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*' },
      body: {
        response_text: 'I encountered an issue retrieving water data. Please try again shortly.',
        error:         err.message,
        rag_enabled:   false
      }
    };
  }
}

// ── IBM Cloud Functions entry point (router) ───────────────────────────────────
async function main(params) {
  const action = params.__ow_path || params.action || 'getStateStats';

  switch (action) {
    case '/stats':
    case 'getStateStats':
      return getStateStats(params);
    case '/predict':
    case 'getPrediction':
      return getPrediction(params);
    case '/priority':
    case 'listPriorityStates':
      return listPriorityStates(params);
    case '/nlquery':
    case 'getNLQuery':
      return getNLQuery(params);
    default:
      return {
        statusCode: 200,
        body: {
          service: 'JalDrishti API',
          version: '1.0.0',
          endpoints: ['/stats','/predict','/priority','/nlquery']
        }
      };
  }
}

module.exports.main = main;
