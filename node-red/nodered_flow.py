"""
WaterPulse — Node-RED Flow (exported as JSON)
Orchestrates: Data Refresh → Db2 Update → Dashboard Trigger
Platform: IBM Cloud Foundry (Lite: 256 MB RAM, 1 instance)

Flow 1: Scheduled Data Refresh (every 24h)
  [inject: daily 00:00] → [function: build COS request] → [http request: COS]
      → [function: parse CSV] → [http request: Db2 REST] → [debug]

Flow 2: Watson Assistant Webhook Bridge
  [http in: POST /jalmitra] → [function: format request] → [http request: Cloud Functions]
      → [function: format response] → [http response]

Flow 3: Dashboard Real-time Update
  [http in: GET /api/stats] → [http request: Cloud Functions /stats]
      → [http response: JSON]
"""

# Node-RED flow JSON (to be pasted into Node-RED editor via Import)
NODERED_FLOW = [
  {
    "id": "flow1",
    "type": "tab",
    "label": "WaterPulse Data Refresh",
    "disabled": False,
    "info": "Scheduled daily refresh of water metrics data"
  },
  {
    "id": "inject1",
    "type": "inject",
    "z": "flow1",
    "name": "Daily 00:00 Trigger",
    "props": [{"p": "payload"}],
    "repeat": "86400",
    "crontab": "0 0 * * *",
    "once": True,
    "onceDelay": 5,
    "wires": [["func_build_request"]]
  },
  {
    "id": "func_build_request",
    "type": "function",
    "z": "flow1",
    "name": "Build COS Request",
    "func": """
msg.url = 'https://s3.us-south.cloud-object-storage.appdomain.cloud/waterpulse-raw-data/cleaned/waterpulse_master_cleaned.csv';
msg.headers = { Authorization: 'Bearer ' + global.get('iam_token') };
return msg;
""",
    "outputs": 1,
    "wires": [["http_cos_fetch"]]
  },
  {
    "id": "http_cos_fetch",
    "type": "http request",
    "z": "flow1",
    "name": "Fetch from COS",
    "method": "GET",
    "ret": "txt",
    "url": "",
    "wires": [["func_parse_csv"]]
  },
  {
    "id": "func_parse_csv",
    "type": "function",
    "z": "flow1",
    "name": "Parse & Validate CSV",
    "func": """
const lines = msg.payload.split('\\n');
const headers = lines[0].split(',');
const rows = lines.slice(1).filter(l => l.trim()).map(l => {
    const vals = l.split(',');
    return Object.fromEntries(headers.map((h,i) => [h.trim(), vals[i]?.trim()]));
});
msg.payload = { rows, count: rows.length };
node.status({ fill: 'green', shape: 'dot', text: rows.length + ' rows parsed' });
return msg;
""",
    "outputs": 1,
    "wires": [["http_cf_refresh"]]
  },
  {
    "id": "http_cf_refresh",
    "type": "http request",
    "z": "flow1",
    "name": "Trigger CF Refresh",
    "method": "POST",
    "ret": "obj",
    "url": "https://us-south.functions.cloud.ibm.com/api/v1/web/YOUR_NAMESPACE/waterpulse/refreshData.json",
    "wires": [["debug_refresh"]]
  },
  {
    "id": "debug_refresh",
    "type": "debug",
    "z": "flow1",
    "name": "Refresh Status",
    "active": True,
    "wires": []
  },

  {
    "id": "flow2",
    "type": "tab",
    "label": "JalMitra Chatbot Bridge",
    "disabled": False,
    "info": "Bridges Watson Assistant webhook to Cloud Functions"
  },
  {
    "id": "http_in_chat",
    "type": "http in",
    "z": "flow2",
    "name": "POST /jalmitra",
    "url": "/jalmitra",
    "method": "post",
    "wires": [["func_format_wa"]]
  },
  {
    "id": "func_format_wa",
    "type": "function",
    "z": "flow2",
    "name": "Format WA Request",
    "func": """
const body = msg.payload;
msg.payload = {
    intent: body.intents?.[0]?.intent || 'unknown',
    entities: body.entities || [],
    input_text: body.input?.text || ''
};
msg.headers = { 'Content-Type': 'application/json' };
return msg;
""",
    "outputs": 1,
    "wires": [["http_cf_nlquery"]]
  },
  {
    "id": "http_cf_nlquery",
    "type": "http request",
    "z": "flow2",
    "name": "Call CF nlquery",
    "method": "POST",
    "ret": "obj",
    "url": "https://us-south.functions.cloud.ibm.com/api/v1/web/YOUR_NAMESPACE/waterpulse/getNLQuery.json",
    "wires": [["func_format_wa_resp"]]
  },
  {
    "id": "func_format_wa_resp",
    "type": "function",
    "z": "flow2",
    "name": "Format WA Response",
    "func": """
const cfResp = msg.payload;
msg.payload = {
    output: {
        generic: [{
            response_type: 'text',
            text: cfResp.response_text || 'Data not available'
        }]
    }
};
msg.statusCode = 200;
return msg;
""",
    "outputs": 1,
    "wires": [["http_out_chat"]]
  },
  {
    "id": "http_out_chat",
    "type": "http response",
    "z": "flow2",
    "name": "Response",
    "wires": []
  },

  {
    "id": "flow3",
    "type": "tab",
    "label": "Dashboard API Proxy",
    "disabled": False,
    "info": "Proxies dashboard requests to Cloud Functions"
  },
  {
    "id": "http_in_stats",
    "type": "http in",
    "z": "flow3",
    "name": "GET /api/state-stats",
    "url": "/api/state-stats",
    "method": "get",
    "wires": [["func_build_stats_req"]]
  },
  {
    "id": "func_build_stats_req",
    "type": "function",
    "z": "flow3",
    "name": "Build Stats URL",
    "func": """
const stateCode = msg.req.query.stateCode || '10';
const year      = msg.req.query.year || '2023';
msg.url = 'https://us-south.functions.cloud.ibm.com/api/v1/web/YOUR_NAMESPACE/waterpulse/getStateStats.json' +
          '?stateCode=' + stateCode + '&year=' + year;
return msg;
""",
    "outputs": 1,
    "wires": [["http_cf_stats"]]
  },
  {
    "id": "http_cf_stats",
    "type": "http request",
    "z": "flow3",
    "name": "Call CF Stats",
    "method": "GET",
    "ret": "obj",
    "url": "",
    "wires": [["http_out_stats"]]
  },
  {
    "id": "http_out_stats",
    "type": "http response",
    "z": "flow3",
    "name": "Stats Response",
    "wires": []
  }
]

import json
print(json.dumps(NODERED_FLOW, indent=2))
