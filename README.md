# 💧 WaterPulse — नीरनीति
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

---

## Repository Structure

```
WaterPulse/
├── frontend/
│   ├── app.py                         # Streamlit WaterPulse UI — premium dark theme
│   ├── requirements.txt               # streamlit, requests, plotly, pandas
│   └── .streamlit/secrets.toml.example
├── cloud-functions/waterpulse-api/
│   ├── index.js                       # 4 REST endpoints: getStateStats/getPrediction/listPriority/getNLQuery
│   ├── rag_handler.js                 # IAM token cache + FAISS cosine sim + Granite generation
│   └── package.json                   # v2.0, GRANITE_MODEL_ID env var
├── watson-assistant/
│   └── jalmitra_dialog_export.json    # 8 intents, 27 state entities, webhook to Cloud Functions
├── node-red/
│   └── nodered_flow.py                # 3 flows: data refresh, WA bridge, API proxy
├── data/
│   └── mis_78_sample.csv              # 36 states × rural/urban/social groups
├── .gitignore
└── README.md
```

---

## Quick Start — Run Locally

```bash
# Clone the repo
git clone https://github.com/Nicks-19/WaterPulse.git
cd WaterPulse

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
```

From IBM Cloud Catalog (all Lite/free tier):
- **Cloud Object Storage** → bucket: `waterpulse-data` (us-south)
- **Db2 on Cloud** → Lite → note hostname, port, credentials
- **Watson Studio** → Lite → project: "WaterPulse"
- **watsonx.ai** → associate with Studio project → note **Project ID**
- **Watson Assistant** → Lite → assistant: "JalMitra"

### Step 2 — Upload Dataset to COS

```bash
ibmcloud cos object-put \
  --bucket waterpulse-data \
  --key mis_78_sample.csv \
  --body ./data/mis_78_sample.csv
```

### Step 3 — Deploy Cloud Functions

```bash
cd cloud-functions/waterpulse-api
npm install

ibmcloud fn namespace create waterpulse-ns
ibmcloud fn action update waterpulse/api index.js \
  --kind nodejs:16 --web true \
  --param DB2_HOST YOUR_DB2_HOST \
  --param DB2_UID YOUR_DB2_UID \
  --param DB2_PWD YOUR_DB2_PWD \
  --param WATSONX_API_KEY YOUR_WATSONX_API_KEY \
  --param WATSONX_URL YOUR_WATSONX_URL \
  --param WATSONX_PROJECT_ID YOUR_PROJECT_ID \
  --param GRANITE_MODEL_ID ibm/granite-3-2-8b-instruct

ibmcloud fn action get waterpulse/api --url
```

### Step 4 — Import Watson Assistant Skill

1. Watson Assistant → Create assistant "JalMitra"
2. Add dialog skill → Upload `watson-assistant/jalmitra_dialog_export.json`
3. Integrations → Set webhook URL to your Cloud Functions web action URL

---

## Granite LLM Configuration

WaterPulse uses **IBM Granite 3.2 8B Instruct** via watsonx.ai RAG pipeline.

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

---

## License

MIT License — Open Government Data (MIS 78th Round) used under OGD Platform India terms.

---

*WaterPulse · Edunet Foundation Problem Statement #38 · IBM Cloud Lite · Streamlit · IBM Granite 3.2*
