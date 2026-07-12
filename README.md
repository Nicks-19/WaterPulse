# 💧 NeerNiti — नीरनीति
## AI-Driven Analytics Platform for Equitable Access to Improved Drinking Water Sources in India

> **Neer** (नीर) = Water · **Niti** (नीति) = Policy / Wisdom  
> **Dataset:** MIS 78th Round — Multiple Indicator Survey (AI Kosh / NSSO)  
> **Platform:** IBM Cloud Lite (Always-Free Tier Only)  
> **Submission:** Edunet Foundation Problem Statement #38

---

## IBM Cloud Services Used

| Component | IBM Service | Lite Limit |
|---|---|---|
| Raw + Cleaned Data | Cloud Object Storage | 25 GB free |
| Structured Analytics DB | Db2 on Cloud | 200 MB, 5 tables |
| ETL + ML Notebooks | Watson Studio | 50 CU/month |
| Model Deployment + Granite LLM | watsonx.ai (Watson Machine Learning) | 20 deployments |
| Serverless REST API | IBM Cloud Functions | 5M invocations/month |
| JalMitra Chatbot | Watson Assistant | 10,000 messages/month |
| Dashboard + Node-RED | Cloud Foundry | 256 MB / app |

---

## Repository Structure

```
jaldrishti/
├── notebooks/
│   ├── 01_etl_cleaning.ipynb          # COS → Db2 ETL, equity_gap/sdg61_proxy derived features
│   ├── 02_ml_training.ipynb           # GBT classifier + K-Means + Ridge → watsonx.ai deploy
│   └── 03_rag_pipeline.ipynb          # FAISS index build + Granite 3.2 end-to-end RAG test
├── cloud-functions/jaldrishti-api/
│   ├── index.js                       # 4 REST endpoints: getStateStats/getPrediction/listPriority/getNLQuery
│   ├── rag_handler.js                 # IAM token cache + FAISS cosine sim + Granite generation
│   └── package.json                   # v2.0, GRANITE_MODEL_ID env var
├── frontend/
│   ├── app.py                         # Streamlit NeerNiti UI — dark theme, 5 tabs
│   ├── requirements.txt               # streamlit, requests, plotly, pandas
│   └── .streamlit/secrets.toml.example
├── dashboard/
│   ├── index.html                     # Static Chart.js + Leaflet dashboard
│   ├── manifest.yml                   # CF deployment manifest
│   └── Staticfile
├── watson-assistant/
│   └── jalmitra_dialog_export.json    # 8 intents, 27 state entities, webhook to Cloud Functions
├── node-red/
│   └── nodered_flow.py                # 3 flows: data refresh, WA bridge, dashboard proxy
├── data/
│   └── mis_78_sample.csv              # 36 states × rural/urban/social groups
├── architecture/
│   └── jaldrishti_architecture.svg
├── report/
│   └── jaldrishti_project_report.md   # Full evaluation-criteria-mapped project report
├── slides/
│   └── jaldrishti_deck_outline.md     # 14-slide deck outline
├── .gitignore
└── README.md
```

---

## Quick Start — Run Locally

```bash
# Clone the repo
git clone https://github.com/YOUR_USERNAME/neerniti.git
cd neerniti

# Install Streamlit dependencies
pip install -r frontend/requirements.txt

# Launch the app
cd frontend
streamlit run app.py
```

Open [http://localhost:8501](http://localhost:8501) in your browser.

**To enable Granite AI:** go to the **Config tab** in the app and enter your IBM Cloud credentials (Project ID, API Key, Regional URL). No `secrets.toml` required.

---

## Step-by-Step IBM Cloud Deployment

### Step 1 — Provision Services

```bash
ibmcloud login --sso
ibmcloud plugin install cloud-object-storage
ibmcloud plugin install cloud-functions
ibmcloud plugin install cloud-foundry
```

From IBM Cloud Catalog (all Lite/free tier):
- **Cloud Object Storage** → bucket: `neerniti-data` (us-south)
- **Db2 on Cloud** → Lite → note hostname, port, credentials
- **Watson Studio** → Lite → project: "NeerNiti"
- **watsonx.ai** → associate with Studio project → note **Project ID**
- **Watson Assistant** → Lite → assistant: "JalMitra"
- **Cloud Foundry** → create org and space

### Step 2 — Upload Dataset to COS

```bash
ibmcloud cos object-put \
  --bucket neerniti-data \
  --key mis_78_sample.csv \
  --body ./data/mis_78_sample.csv
```

### Step 3 — Configure Credentials

In each notebook, replace the placeholder values:
```python
COS_API_KEY       = 'YOUR_COS_API_KEY'
COS_INSTANCE_CRN  = 'YOUR_COS_INSTANCE_CRN'
DB2_DSN           = 'DATABASE=BLUDB;HOSTNAME=...;PORT=30376;UID=...;PWD=...;SECURITY=SSL;'
WX_API_KEY        = 'YOUR_WATSONX_API_KEY'
WX_PROJECT_ID     = 'YOUR_WATSONX_PROJECT_ID'
WX_URL            = 'https://us-south.ml.cloud.ibm.com'  # or your region
```

### Step 4 — Run Notebooks in Order (Watson Studio)

1. Upload all 3 notebooks to Watson Studio
2. Run `01_etl_cleaning.ipynb` → populates `NEERNITI.STATE_WATER_METRICS` in Db2
3. Run `02_ml_training.ipynb` → trains 3 models, deploys to watsonx.ai
4. Run `03_rag_pipeline.ipynb` → builds FAISS index, saves to COS, tests Granite RAG

### Step 5 — Deploy Cloud Functions

```bash
cd cloud-functions/jaldrishti-api
npm install

ibmcloud fn namespace create neerniti-ns
ibmcloud fn action update neerniti/api index.js \
  --kind nodejs:16 --web true \
  --param DB2_HOST YOUR_DB2_HOST \
  --param DB2_UID YOUR_DB2_UID \
  --param DB2_PWD YOUR_DB2_PWD \
  --param WATSONX_API_KEY YOUR_WATSONX_API_KEY \
  --param WATSONX_URL YOUR_WATSONX_URL \
  --param WATSONX_PROJECT_ID YOUR_PROJECT_ID \
  --param GRANITE_MODEL_ID ibm/granite-3-2-8b-instruct

ibmcloud fn action get neerniti/api --url
```

### Step 6 — Import Watson Assistant Skill

1. Watson Assistant → Create assistant "JalMitra"
2. Add dialog skill → Upload `watson-assistant/jalmitra_dialog_export.json`
3. Integrations → Set webhook URL to your Cloud Functions web action URL

### Step 7 — Deploy Dashboard to Cloud Foundry

```bash
cd dashboard
ibmcloud cf push neerniti-dashboard \
  -f manifest.yml -m 64M -i 1 \
  --buildpack staticfile_buildpack
```

Dashboard URL: `https://neerniti-dashboard.mybluemix.net`

---

## Granite LLM Configuration

NeerNiti uses **IBM Granite 3.2 8B Instruct** via watsonx.ai RAG pipeline.

| Parameter | Value |
|---|---|
| Model ID | `ibm/granite-3-2-8b-instruct` |
| Regional URL (us-south) | `https://us-south.ml.cloud.ibm.com` |
| Regional URL (eu-de) | `https://eu-de.ml.cloud.ibm.com` |
| Regional URL (ap-north) | `https://au-syd.ml.cloud.ibm.com` |
| Temperature | 0.2 |
| Max tokens | 300 |

Alternative models (if Granite unavailable in your region):
- `meta-llama/llama-3-1-8b-instruct` (eu-de)
- `mistralai/mistral-large` (ap-north)

---

## Key Findings

- **94.5%** national average masks a **30-point urban–rural gap** in 8–12 states
- **Jharkhand (58%)** and **Bihar (62%)** are CRITICAL risk states for SDG 6.1
- States with **<60% clean cooking fuel** show systematically **>15% water equity gap**
- **ST households** across 12 states average **55–60%** — lowest of all social groups
- NeerNiti reduces analysis time from **2 weeks → 30 seconds**

---

## Presentation

The full 14-slide NeerNiti deck covers:
1. Title | 2. Problem | 3. Dataset | 4. Architecture | 5. IBM Services
6. RAG Pipeline | 7. ML Models | 8. JalMitra Demo | 9. Impact
10. Scalability | 11. Commercial Viability | 12. Roadmap | 13. Demo Links | 14. Conclusion

**Submission file:** `NeerNiti_updated.pptx` (export deck with "updated" in filename per professor requirement)

---

## License

MIT License — Open Government Data (MIS 78th Round) used under OGD Platform India terms.

---

*NeerNiti · Edunet Foundation Problem Statement #38 · IBM Cloud Lite · Streamlit · IBM Granite 3.2*
