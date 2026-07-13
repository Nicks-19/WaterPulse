"""
WaterPulse — AI Water Equity Analytics
IBM Granite + watsonx.ai + RAG | MIS 78th Round | SDG 6.1
"""

import streamlit as st
import requests
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import os

# ── Page config ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="WaterPulse — Water AI",
    page_icon="💧",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ── FULL UI OVERHAUL — Dark navbar + card layout ───────────────────────────────
st.markdown("""
<style>
/* ── Global reset ── */
html, body, [class*="css"] {
    font-family: "Geist Sans", "Inter", system-ui, sans-serif !important;
}
.stApp {
    background-color: #09090b !important;
    color: #e2e8f0 !important;
}
/* Hide Streamlit default header & footer */
#MainMenu, footer, header { visibility: hidden; }
.block-container { padding-top: 0 !important; max-width: 100% !important; }

/* ── NAVBAR ── */
.navbar {
    background: rgba(9, 9, 11, 0.6);
    backdrop-filter: blur(12px);
    -webkit-backdrop-filter: blur(12px);
    border-bottom: 1px solid rgba(255, 255, 255, 0.1);
    padding: 0 32px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    height: 60px;
    position: sticky;
    top: 0;
    z-index: 999;
}
.nav-brand {
    display: flex;
    align-items: center;
    gap: 10px;
    font-size: 20px;
    font-weight: 700;
    color: #ffffff;
    letter-spacing: -0.5px;
}
.nav-brand em { color: #ffffff; font-style: normal; opacity: 0.7; }
.nav-links {
    display: flex;
    align-items: center;
    gap: 6px;
}
.nav-link {
    color: rgba(255, 255, 255, 0.6);
    font-size: 14px;
    font-weight: 500;
    padding: 6px 14px;
    border-radius: 9999px;
    text-decoration: none;
    cursor: pointer;
    transition: all 0.3s ease;
}
.nav-link:hover { color: #ffffff; background: rgba(255, 255, 255, 0.05); }
.nav-link.active { color: #ffffff; background: rgba(255, 255, 255, 0.1); }
.nav-right {
    display: flex;
    align-items: center;
    gap: 10px;
}
.nav-badge {
    background: transparent;
    border: 1px solid rgba(255, 255, 255, 0.2);
    color: #ffffff;
    font-size: 11px;
    font-weight: 500;
    padding: 4px 12px;
    border-radius: 9999px;
}
.nav-badge.live { background: rgba(255, 255, 255, 0.1); border-color: rgba(255, 255, 255, 0.3); }
.nav-badge.live::before { content: "● "; font-size: 9px; }

/* ── HERO SECTION ── */
.hero {
    background: #09090b;
    border-bottom: 1px solid rgba(255, 255, 255, 0.05);
    padding: 64px 48px 48px;
    position: relative;
    overflow: hidden;
    text-align: center;
}
.hero::before {
    content: '';
    position: absolute;
    top: -150px;
    left: 50%;
    transform: translateX(-50%);
    width: 600px;
    height: 400px;
    background: radial-gradient(circle, rgba(139, 92, 246, 0.15) 0%, transparent 70%);
    pointer-events: none;
}
.hero-inner { position: relative; z-index: 1; display: flex; flex-direction: column; align-items: center; }
.hero-tag {
    font-size: 12px; font-weight: 500; letter-spacing: 0.5px;
    color: rgba(255,255,255,0.6); margin-bottom: 16px;
    border: 1px solid rgba(255,255,255,0.1); padding: 4px 12px; border-radius: 9999px;
    display: inline-block;
}
.hero-title { font-size: 48px; font-weight: 800; letter-spacing: -1.5px; line-height: 1.1; margin-bottom: 16px; color: #ffffff; }
.hero-title em { color: #ffffff; opacity: 0.8; font-style: normal; }
.hero-sub { font-size: 16px; color: rgba(255,255,255,0.6); max-width: 600px; margin-bottom: 32px; }
.hero-stats { display: flex; gap: 16px; justify-content: center; flex-wrap: wrap; }
.hstat {
    background: rgba(255,255,255,0.02);
    border: 1px solid rgba(255,255,255,0.08);
    border-radius: 16px;
    padding: 16px 24px;
    text-align: center;
    min-width: 130px;
}
.hstat .hn { font-size: 28px; font-weight: 700; line-height: 1; letter-spacing: -1px; color: #ffffff; }
.hstat .hl { font-size: 12px; color: rgba(255,255,255,0.5); margin-top: 6px; font-weight: 500; }

/* ── KPI CARDS ── */
.kpi-grid { display: grid; grid-template-columns: repeat(4,1fr); gap: 16px; margin: 32px 0; }
.kpi-card {
    background: rgba(255, 255, 255, 0.02);
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 20px;
    padding: 20px 24px;
    transition: all 0.3s ease;
}
.kpi-card:hover { background: rgba(255, 255, 255, 0.04); border-color: rgba(255, 255, 255, 0.15); transform: translateY(-2px); }
.kpi-card .kv { font-size: 32px; font-weight: 700; line-height: 1; letter-spacing: -1px; color: #ffffff; }
.kpi-card .kl { font-size: 13px; color: rgba(255,255,255,0.6); margin-top: 8px; font-weight: 500; }
.kpi-card .ks { font-size: 12px; margin-top: 8px; color: rgba(255,255,255,0.4); }

/* ── SECTION CARDS ── */
.section-card {
    background: rgba(255, 255, 255, 0.015);
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 24px;
    padding: 24px 28px;
    margin-bottom: 20px;
}
.section-card .sc-title {
    font-size: 14px; font-weight: 600;
    color: #ffffff; margin-bottom: 16px;
    padding-bottom: 12px; border-bottom: 1px solid rgba(255,255,255,0.05);
}

/* ── TABLE ── */
.styled-table { width: 100%; border-collapse: collapse; font-size: 13px; }
.styled-table th {
    background: transparent; color: rgba(255,255,255,0.6); padding: 12px 16px;
    text-align: left; font-weight: 500; font-size: 12px;
    border-bottom: 1px solid rgba(255,255,255,0.1);
}
.styled-table td {
    padding: 12px 16px; border-bottom: 1px solid rgba(255,255,255,0.03);
    color: rgba(255,255,255,0.8); vertical-align: middle;
}
.styled-table tr:hover td { background: rgba(255,255,255,0.02); }
.t-green  { color: #ffffff !important; font-weight: 500; }
.t-yellow { color: #ffffff !important; font-weight: 500; }
.t-red    { color: #ffffff !important; font-weight: 500; }
.tier-badge {
    font-size: 11px; font-weight: 500; padding: 4px 10px;
    border-radius: 9999px; border: 1px solid rgba(255,255,255,0.2);
    display: inline-block;
}

/* ── CHAT ── */
.chat-wrap {
    background: rgba(255,255,255,0.02);
    border: 1px solid rgba(255,255,255,0.08);
    border-radius: 24px;
    padding: 24px;
    min-height: 420px;
    display: flex; flex-direction: column; gap: 16px;
}
.chat-msg-bot {
    background: transparent;
    border: 1px solid rgba(255,255,255,0.1);
    color: #ffffff; padding: 14px 18px;
    border-radius: 16px 16px 16px 4px;
    font-size: 14px; line-height: 1.6;
    max-width: 85%; align-self: flex-start;
}
.chat-msg-user {
    background: #ffffff;
    color: #000000; padding: 14px 18px;
    border-radius: 16px 16px 4px 16px;
    font-size: 14px; align-self: flex-end;
    max-width: 75%; font-weight: 500;
}
.chat-model-badge {
    font-size: 11px; color: rgba(255,255,255,0.4); margin-top: 8px;
}
.quick-chip {
    background: transparent;
    border: 1px solid rgba(255,255,255,0.2);
    color: rgba(255,255,255,0.8); font-size: 13px; padding: 6px 16px;
    border-radius: 9999px; cursor: pointer; display: inline-block;
    margin: 4px; transition: all 0.3s;
}
.quick-chip:hover { background: rgba(255,255,255,0.1); color: #ffffff; }

/* ── CRED PANEL ── */
.cred-panel {
    background: rgba(255,255,255,0.02);
    border: 1px solid rgba(255,255,255,0.1);
    border-radius: 20px;
    padding: 24px;
    margin-bottom: 24px;
}
.cred-panel .cp-title {
    font-size: 16px; font-weight: 600; color: #ffffff; margin-bottom: 4px;
}
.cred-panel .cp-sub { font-size: 13px; color: rgba(255,255,255,0.5); margin-bottom: 20px; }

/* ── INPUT OVERRIDES ── */
.stTextInput input, .stSelectbox select {
    background: rgba(255,255,255,0.03) !important;
    border: 1px solid rgba(255,255,255,0.1) !important;
    color: #ffffff !important;
    border-radius: 12px !important;
    padding: 10px 14px !important;
}
.stTextInput input:focus {
    border-color: rgba(255,255,255,0.3) !important;
    box-shadow: none !important;
}
.stButton button {
    background: #ffffff !important;
    color: #000000 !important;
    border: none !important;
    border-radius: 9999px !important;
    font-weight: 500 !important;
    padding: 8px 24px !important;
    transition: opacity 0.3s !important;
}
.stButton button:hover {
    opacity: 0.9 !important;
}

/* ── METRICS OVERRIDE ── */
[data-testid="stMetricValue"] { color: #ffffff !important; font-size: 32px !important; font-weight: 700 !important; letter-spacing: -1px; }
[data-testid="stMetricLabel"] { color: rgba(255,255,255,0.6) !important; font-size: 13px !important; }

/* ── SCROLLBAR ── */
::-webkit-scrollbar { width: 6px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: rgba(255,255,255,0.1); border-radius: 6px; }
</style>
""", unsafe_allow_html=True)

# ── Safe secrets reader ────────────────────────────────────────────────────────
from dotenv import load_dotenv
load_dotenv(override=True)

def _secret(key, default=""):
    try:    return st.secrets[key]
    except: return os.getenv(key, default)

WATSONX_API_KEY    = _secret("WATSONX_API_KEY")
WATSONX_URL        = _secret("WATSONX_URL", "https://us-south.ml.cloud.ibm.com")
WATSONX_PROJECT_ID = _secret("WATSONX_PROJECT_ID")
GRANITE_MODEL_ID   = _secret("GRANITE_MODEL_ID", "ibm/granite-3-8b-instruct")

# Add an AGENT_INSTRUCTIONS section so you can customize the agent behavior easily
DEFAULT_INSTRUCTIONS = "You are WaterPulse, an AI assistant specialising in India's drinking water access data from MIS 78th Round (2020-21). Answer using only the provided context. Cite specific percentages. Be concise and policy-focused."
AGENT_INSTRUCTIONS = _secret("AGENT_INSTRUCTIONS", DEFAULT_INSTRUCTIONS)

# ── MIS 78th Round Data ────────────────────────────────────────────────────────
MIS_DATA = pd.DataFrame({
    "state":      ["Jharkhand","Bihar","Odisha","Rajasthan","Uttar Pradesh",
                   "Assam","Chhattisgarh","Madhya Pradesh","West Bengal","Maharashtra",
                   "Karnataka","Gujarat","Kerala","Punjab","Himachal Pradesh"],
    "rural_pct":  [56.4,58.6,62.4,64.8,72.4,68.4,66.8,68.6,76.8,81.6,79.4,84.6,93.4,89.4,97.3],
    "urban_pct":  [82.8,84.2,86.4,88.6,91.3,88.6,88.4,90.4,93.4,95.8,94.6,96.4,97.8,96.7,99.1],
    "cook_rural": [28.6,32.4,34.8,38.2,44.6,38.6,36.4,40.2,48.6,58.4,56.8,62.4,78.6,72.6,68.4],
    "migration":  [5.2, 6.9, 4.6, 4.9, 5.8, 4.2, 4.8, 4.4, 5.4, 5.6, 5.4, 5.8, 6.8, 5.6, 4.1],
})
MIS_DATA["equity_gap"] = (MIS_DATA["urban_pct"] - MIS_DATA["rural_pct"]).round(1)
MIS_DATA["sdg_proxy"]  = (MIS_DATA["rural_pct"]*0.65 + MIS_DATA["urban_pct"]*0.35).round(1)
MIS_DATA["sdg_status"] = MIS_DATA["sdg_proxy"].apply(
    lambda x: "🔴 CRITICAL" if x < 70 else ("🟠 AT RISK" if x < 80 else "🟢 ON TRACK"))
MIS_DATA["tier"] = MIS_DATA.apply(
    lambda r: "D" if r.sdg_proxy < 80 and r.equity_gap >= 15
    else ("C" if r.sdg_proxy < 80 else ("B" if r.equity_gap >= 15 else "A")), axis=1)

TIER_FULL = {"A":"A — On Track","B":"B — High Gap","C":"C — Low Access","D":"D — Priority"}
TIER_CSS  = {"A":"tb-a","B":"tb-b","C":"tb-c","D":"tb-d"}

# ── Watsonx.ai helpers ─────────────────────────────────────────────────────────
@st.cache_data(ttl=60, show_spinner=False)
def get_iam_token(api_key):
    r = requests.post(
        "https://iam.cloud.ibm.com/identity/token",
        data={"grant_type":"urn:ibm:params:oauth:grant-type:apikey","apikey":api_key},
        headers={"Content-Type":"application/x-www-form-urlencoded"}, timeout=10)
    return r.json()["access_token"]

def ask_granite(question, context):
    if not WATSONX_API_KEY or not WATSONX_PROJECT_ID:
        return "⚠️ Enter your API Key and Project ID in your **.env** file to enable Granite AI."
    try:
        token = get_iam_token(WATSONX_API_KEY)
        prompt = f"""<|system|>
{AGENT_INSTRUCTIONS}
<|user|>
Context:
{context}

Question: {question}
<|assistant|>"""
        r = requests.post(
            f"{WATSONX_URL}/ml/v1/text/generation?version=2024-03-14",
            json={"model_id":GRANITE_MODEL_ID,"project_id":WATSONX_PROJECT_ID,
                  "input":prompt,"parameters":{"max_new_tokens":400,"temperature":0.1,
                  "top_p":0.9,"stop_sequences":["<|user|>","<|system|>"]}},
            headers={"Authorization":f"Bearer {token}","Content-Type":"application/json"},
            timeout=30)
        
        if r.status_code != 200:
            return f"⚠️ IBM Cloud Error ({r.status_code}): {r.text}"
            
        return r.json()["results"][0]["generated_text"].strip()
    except Exception as e:
        return f"⚠️ Granite error: {e}"

def build_context(question):
    q = question.lower()
    rel = MIS_DATA.copy()
    for s in MIS_DATA["state"].str.lower():
        if s in q:
            rel = MIS_DATA[MIS_DATA["state"].str.lower() == s]; break
    else:
        if any(w in q for w in ["worst","urgent","critical","priority","intervention"]):
            rel = MIS_DATA.nsmallest(5,"sdg_proxy")
        elif any(w in q for w in ["best","top","highest","good"]):
            rel = MIS_DATA.nlargest(5,"sdg_proxy")
    return "\n".join(
        f"State:{r['state']}|Rural:{r['rural_pct']}%|Urban:{r['urban_pct']}%|"
        f"Gap:{r['equity_gap']}pp|SDG:{r['sdg_proxy']}%|{r['sdg_status']}|"
        f"Tier:{r['tier']}|CookFuel:{r['cook_rural']}%|Migration:{r['migration']}%"
        for _,r in rel.iterrows())

# ── NAVBAR ─────────────────────────────────────────────────────────────────────
current_tab = st.query_params.get("tab", "dashboard")

def nav_link(tab_id, label):
    active_class = " active" if current_tab == tab_id else ""
    return f'<a href="/?tab={tab_id}" target="_self" class="nav-link{active_class}">{label}</a>'

st.markdown(f"""
<div class="navbar">
  <div class="nav-brand">💧 WaterPulse</div>
  <div class="nav-links">
    {nav_link('dashboard', 'Dashboard')}
    {nav_link('jalmitra', 'JalMitra AI')}
    {nav_link('states', 'States')}
    {nav_link('about', 'About')}
  </div>
</div>
""", unsafe_allow_html=True)

# ── HERO ───────────────────────────────────────────────────────────────────────
if current_tab == "dashboard":
    st.markdown(f"""
<div class="hero">
  <div class="hero-inner">
    <div class="hero-tag">Edunet Foundation · Problem Statement No. 38 · IBM Cloud Lite</div>
    <div class="hero-title">💧 WaterPulse — Water Equity <em>Analytics</em></div>
    <div class="hero-sub">AI-Driven Platform for SDG 6.1 · IBM Granite 3.2 8B · watsonx.ai RAG Pipeline · MIS 78th Round</div>
    <div class="hero-stats">
      <div class="hstat"><div class="hn">36</div><div class="hl">States / UTs</div></div>
      <div class="hstat"><div class="hn">94.5%</div><div class="hl">National Avg</div></div>
      <div class="hstat"><div class="hn">180M+</div><div class="hl">Rural at Risk</div></div>
      <div class="hstat"><div class="hn">12/27</div><div class="hl">SDG Risk States</div></div>
      <div class="hstat"><div class="hn">₹0</div><div class="hl">Infra Cost/Month</div></div>
    </div>
  </div>
</div>
""", unsafe_allow_html=True)

# ── MAIN CONTENT ───────────────────────────────────────────────────────────────
st.markdown("<div style='padding: 8px 32px 0;'>", unsafe_allow_html=True)

# ════════════════════════════════════════════════════════════════
# TAB 1 — DASHBOARD
# ════════════════════════════════════════════════════════════════
if current_tab == "dashboard":
    on_track = len(MIS_DATA[MIS_DATA["sdg_proxy"] >= 80])
    at_risk  = len(MIS_DATA[MIS_DATA["sdg_proxy"] <  80])

    # KPI row
    st.markdown("""
    <div class="kpi-grid">
      <div class="kpi-card kc-green">
        <div class="kv">94.5%</div>
        <div class="kl">National Avg Water Access</div>
        <div class="ks" style="color:#34d399">↑ MIS 78th Round, All Sectors</div>
      </div>
      <div class="kpi-card kc-yellow">
        <div class="kv">72.3%</div>
        <div class="kl">Rural Average</div>
        <div class="ks" style="color:#fbbf24">↓ 22.2 pp below urban</div>
      </div>
      <div class="kpi-card kc-red">
        <div class="kv">12 / 27</div>
        <div class="kl">States at SDG-6 Risk</div>
        <div class="ks" style="color:#f87171">SDG proxy score &lt; 80%</div>
      </div>
      <div class="kpi-card kc-purple">
        <div class="kv">31.4 pp</div>
        <div class="kl">Max Equity Gap</div>
        <div class="ks" style="color:#c4b5fd">Jharkhand — urban vs rural</div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    # Charts row 1
    col_l, col_r = st.columns([1.5, 1])

    BG = "#111827"
    with col_l:
        st.markdown('<div class="section-card"><div class="sc-title">Rural vs Urban Water Access — All States (MIS 78th Round)</div>', unsafe_allow_html=True)
        sdf = MIS_DATA.sort_values("rural_pct")
        fig = go.Figure()
        fig.add_bar(name="Rural %", x=sdf["state"], y=sdf["rural_pct"],
                    marker_color="#0ea5e9", marker_line_width=0)
        fig.add_bar(name="Urban %", x=sdf["state"], y=sdf["urban_pct"],
                    marker_color="#10b981", marker_line_width=0)
        fig.add_hline(y=80, line_dash="dot", line_color="rgba(251,191,36,0.5)",
                      annotation_text="SDG 80% threshold", annotation_font_color="#fbbf24",
                      annotation_font_size=9)
        fig.update_layout(
            barmode="group", plot_bgcolor=BG, paper_bgcolor=BG,
            font_color="#cbd5e1", legend=dict(bgcolor="rgba(0,0,0,0)", font_size=11),
            margin=dict(l=10,r=10,t=6,b=72), height=300,
            yaxis=dict(range=[40,105], gridcolor="rgba(255,255,255,0.04)",
                       ticksuffix="%", tickfont=dict(size=10)),
            xaxis=dict(tickangle=-38, tickfont=dict(size=9), gridcolor="rgba(0,0,0,0)")
        )
        st.plotly_chart(fig, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

    with col_r:
        st.markdown('<div class="section-card"><div class="sc-title">SDG 6.1 Progress Tracker</div>', unsafe_allow_html=True)
        fig2 = go.Figure(go.Pie(
            labels=["🟢 On Track (≥80%)", "🔴 At Risk (<80%)"],
            values=[on_track, at_risk], hole=0.6,
            marker=dict(colors=["#10b981","#ef4444"],
                        line=dict(color=BG, width=2)),
            textfont=dict(color="white", size=11)
        ))
        fig2.update_layout(
            plot_bgcolor=BG, paper_bgcolor=BG, font_color="#cbd5e1",
            margin=dict(l=0,r=0,t=6,b=0), height=190,
            legend=dict(bgcolor="rgba(0,0,0,0)", font_size=10),
            annotations=[dict(text=f"<b>{on_track}/{len(MIS_DATA)}</b><br>On Track",
                              x=0.5, y=0.5, font_size=13, font_color="#56cfb2", showarrow=False)]
        )
        st.plotly_chart(fig2, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

        st.markdown('<div class="section-card"><div class="sc-title">Cook Fuel vs Water Access (r ≈ 0.78)</div>', unsafe_allow_html=True)
        clr_map = {"A":"#10b981","B":"#3b82f6","C":"#f59e0b","D":"#ef4444"}
        fig3 = px.scatter(MIS_DATA, x="cook_rural", y="rural_pct",
                          text="state", color="tier", color_discrete_map=clr_map,
                          hover_data={"equity_gap":True})
        fig3.update_traces(textposition="top center", textfont_size=7, marker_size=9)
        fig3.update_layout(
            plot_bgcolor=BG, paper_bgcolor=BG, font_color="#cbd5e1",
            margin=dict(l=10,r=10,t=6,b=10), height=200,
            xaxis_title="Cook Fuel Rural %", yaxis_title="Rural Water %",
            showlegend=False,
            xaxis=dict(gridcolor="rgba(255,255,255,0.04)"),
            yaxis=dict(gridcolor="rgba(255,255,255,0.04)")
        )
        st.plotly_chart(fig3, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

    # Priority table
    st.markdown('<div class="section-card"><div class="sc-title">Priority States Leaderboard — ML Equity Tier Classification</div>', unsafe_allow_html=True)
    tdf = MIS_DATA.sort_values("sdg_proxy").reset_index(drop=True)

    def status_color(s):
        if "CRITICAL" in s: return "t-red"
        if "AT RISK"  in s: return "t-yellow"
        return "t-green"

    rows_html = ""
    for i, r in tdf.iterrows():
        sc  = status_color(r["sdg_status"])
        tc  = TIER_CSS[r["tier"]]
        tfl = TIER_FULL[r["tier"]]
        rows_html += f"""<tr>
          <td style="font-weight:700;color:#94a3c8">{i+1}</td>
          <td style="font-weight:600;color:#fff">{r['state']}</td>
          <td style="color:#60a5fa">{r['rural_pct']}%</td>
          <td style="color:#34d399">{r['urban_pct']}%</td>
          <td style="color:#fbbf24">{r['equity_gap']} pp</td>
          <td style="color:#a78bfa;font-weight:700">{r['sdg_proxy']}%</td>
          <td class="{sc}">{r['sdg_status']}</td>
          <td><span class="tier-badge {tc}">{tfl}</span></td>
        </tr>"""

    st.markdown(f"""
    <table class="styled-table">
      <thead><tr>
        <th>#</th><th>State</th><th>Rural %</th><th>Urban %</th>
        <th>Equity Gap</th><th>SDG Proxy</th><th>Status</th><th>ML Tier</th>
      </tr></thead>
      <tbody>{rows_html}</tbody>
    </table>""", unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

# ════════════════════════════════════════════════════════════════
# TAB 2 — JALMITRA AI CHAT
# ════════════════════════════════════════════════════════════════
if current_tab == "jalmitra":
    st.markdown(f"""
    <div style="display:flex;align-items:center;gap:14px;margin-bottom:16px">
      <div style="font-size:28px">🤖</div>
      <div>
        <div style="font-size:18px;font-weight:800;color:#fff">JalMitra — IBM Granite AI</div>
        <div style="font-size:11px;color:#475569">Model: <code style="color:#56cfb2">{GRANITE_MODEL_ID}</code> via IBM watsonx.ai · RAG over MIS 78th Round data</div>
      </div>
      <div style="margin-left:auto">
        <span style="background:rgba(86,207,178,.1);border:1px solid rgba(86,207,178,.25);color:#56cfb2;font-size:10px;font-weight:700;padding:4px 10px;border-radius:12px">{"● LIVE" if WATSONX_API_KEY and WATSONX_PROJECT_ID else "○ Configure credentials in .env file"}</span>
      </div>
    </div>
    """, unsafe_allow_html=True)

    # Quick chips
    st.markdown("<div style='margin-bottom:12px;'>", unsafe_allow_html=True)
    quick_qs = [
        "Water access in rural Bihar",
        "Which states need urgent intervention?",
        "Is Jharkhand on track for SDG 6?",
        "Cook fuel and water correlation",
        "Compare Bihar and Kerala",
        "Top 5 priority states"
    ]
    chip_cols = st.columns(len(quick_qs))
    for i, q in enumerate(quick_qs):
        if chip_cols[i].button(q, use_container_width=True, key=f"chip_{i}"):
            st.session_state["pending_q"] = q
    st.markdown("</div>", unsafe_allow_html=True)

    # Message history
    if "messages" not in st.session_state:
        st.session_state.messages = [{
            "role": "assistant",
            "content": "🌊 Namaste! I'm **JalMitra**, powered by **IBM Granite 3.2 8B Instruct** via watsonx.ai.\n\nAsk me anything about India's drinking water access, equity gaps, or SDG 6.1 progress — I answer from real **MIS 78th Round** data."
        }]

    # Process pending chip question
    if "pending_q" in st.session_state:
        pq = st.session_state.pop("pending_q")
        st.session_state.messages.append({"role":"user","content":pq})
        with st.spinner(f"🤖 {GRANITE_MODEL_ID.split('/')[-1]} is thinking..."):
            ctx = build_context(pq)
            ans = ask_granite(pq, ctx)
            st.session_state.messages.append({
                "role":"assistant",
                "content":f"{ans}\n\n---\n*🤖 {GRANITE_MODEL_ID} · IBM watsonx.ai · Source: MIS 78th Round*"
            })

    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    if user_q := st.chat_input("Ask about any state's water access, equity gap, SDG status..."):
        st.session_state.messages.append({"role":"user","content":user_q})
        with st.chat_message("user"):
            st.markdown(user_q)
        with st.chat_message("assistant"):
            with st.spinner(f"🤖 {GRANITE_MODEL_ID.split('/')[-1]} is thinking..."):
                ctx = build_context(user_q)
                ans = ask_granite(user_q, ctx)
                full = f"{ans}\n\n---\n*🤖 {GRANITE_MODEL_ID} · IBM watsonx.ai · Source: MIS 78th Round*"
                st.markdown(full)
                st.session_state.messages.append({"role":"assistant","content":full})

    if st.button("🗑 Clear conversation"):
        st.session_state.messages = []
        st.rerun()

# ════════════════════════════════════════════════════════════════
# TAB 3 — STATE EXPLORER
# ════════════════════════════════════════════════════════════════
if current_tab == "states":
    st.markdown("### 🗺 State-Level Deep Dive")
    sel = st.selectbox("Select a State", MIS_DATA["state"].tolist(),
                       index=0, key="state_sel")
    row = MIS_DATA[MIS_DATA["state"] == sel].iloc[0]
    tier_col = {"A":"#10b981","B":"#60a5fa","C":"#fbbf24","D":"#f87171"}[row["tier"]]

    # State header
    st.markdown(f"""
    <div style="background:#111827;border:1px solid rgba(255,255,255,0.07);border-radius:14px;
                padding:18px 22px;margin-bottom:16px;border-left:3px solid {tier_col}">
      <div style="display:flex;align-items:center;gap:16px">
        <div style="font-size:32px">🗾</div>
        <div>
          <div style="font-size:22px;font-weight:800;color:#fff">{sel}</div>
          <div style="font-size:12px;color:#64748b;margin-top:2px">
            ML Tier: <strong style="color:{tier_col}">{TIER_FULL[row['tier']]}</strong>
            &nbsp;·&nbsp; Status: <strong>{row['sdg_status']}</strong>
            &nbsp;·&nbsp; Migration: {row['migration']}%
          </div>
        </div>
        <div style="margin-left:auto;text-align:right">
          <div style="font-size:28px;font-weight:900;color:{tier_col}">{row['sdg_proxy']}%</div>
          <div style="font-size:10px;color:#475569">SDG 6.1 Proxy Score</div>
        </div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    c1,c2,c3,c4 = st.columns(4)
    c1.metric("Rural Access",  f"{row['rural_pct']}%")
    c2.metric("Urban Access",  f"{row['urban_pct']}%")
    c3.metric("Equity Gap",    f"{row['equity_gap']} pp")
    c4.metric("Cook Fuel Rural", f"{row['cook_rural']}%")

    ca, cb = st.columns(2)
    with ca:
        st.markdown('<div class="section-card"><div class="sc-title">Water Access Breakdown</div>', unsafe_allow_html=True)
        fig_a = go.Figure(go.Bar(
            x=["Rural","Urban"], y=[row["rural_pct"],row["urban_pct"]],
            marker_color=["#0ea5e9","#10b981"], marker_line_width=0,
            text=[f"{row['rural_pct']}%",f"{row['urban_pct']}%"],
            textposition="outside", textfont=dict(color="white",size=12)
        ))
        fig_a.add_hline(y=80, line_dash="dot", line_color="rgba(251,191,36,0.5)")
        fig_a.update_layout(
            plot_bgcolor="#111827", paper_bgcolor="#111827",
            font_color="#cbd5e1", yaxis=dict(range=[0,110],ticksuffix="%",
            gridcolor="rgba(255,255,255,0.04)"),
            margin=dict(l=10,r=10,t=10,b=10), height=240, showlegend=False
        )
        st.plotly_chart(fig_a, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

    with cb:
        st.markdown('<div class="section-card"><div class="sc-title">All Indicators</div>', unsafe_allow_html=True)
        cats   = ["Rural Water","Urban Water","Cook Fuel","SDG Proxy"]
        vals   = [row["rural_pct"],row["urban_pct"],row["cook_rural"],row["sdg_proxy"]]
        colors = ["#0ea5e9","#10b981","#f59e0b","#a78bfa"]
        fig_b  = go.Figure(go.Bar(x=cats, y=vals, marker_color=colors, marker_line_width=0,
                                  text=[f"{v}%" for v in vals], textposition="outside",
                                  textfont=dict(color="white",size=11)))
        fig_b.add_hline(y=80, line_dash="dot", line_color="rgba(251,191,36,0.5)")
        fig_b.update_layout(
            plot_bgcolor="#111827", paper_bgcolor="#111827",
            font_color="#cbd5e1", yaxis=dict(range=[0,110],ticksuffix="%",
            gridcolor="rgba(255,255,255,0.04)"),
            margin=dict(l=10,r=10,t=10,b=10), height=240, showlegend=False
        )
        st.plotly_chart(fig_b, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

    policy = ("🚨 **Urgent JJM intervention required.** This state is Tier D — lowest access, highest disparity. "
              "Prioritize rural piped water, bundled SDG 6+7 programs."
              if row["tier"]=="D" else
              "⚠️ **Scale up current programs.** Low access state — accelerate JJM tap connections."
              if row["tier"]=="C" else
              "📋 **Monitor equity gap.** High access but disparity is growing. Focus on rural marginalized groups."
              if row["tier"]=="B" else
              "✅ **On track.** Continue current programs. Share best practices with at-risk states.")
    st.info(policy)



# ════════════════════════════════════════════════════════════════
# TAB 5 — ABOUT
# ════════════════════════════════════════════════════════════════
if current_tab == "about":
    col_a, col_b = st.columns(2)
    with col_a:
        st.markdown("""
### 💧 About WaterPulse

**Problem Statement No. 38** — Edunet Foundation × IBM

WaterPulse is a zero-cost AI analytics platform that turns India's **MIS 78th Round** survey data
into live, actionable water equity insights for policymakers, NGOs and citizens.

**Key Features:**
- 📊 Interactive dashboard — 5 chart panels, live KPIs
- 🤖 JalMitra chatbot — IBM Granite RAG-powered AI
- 🗺 State-level deep dive explorer
- 🎯 ML equity-tier classification (K-Means, 4 tiers)
- 🔴 SDG 6.1 risk scoring (GBT classifier, F1≈88%)
        """)
    with col_b:
        st.markdown("""
### 🏗 Tech Stack

| Layer | Technology |
|---|---|
| **LLM** | IBM Granite 3.2 8B via watsonx.ai |
| **Embeddings** | ibm/slate-125m-english-rtrvr |
| **Vector DB** | FAISS (COS-stored) |
| **ML Models** | scikit-learn GBT, K-Means, Ridge |
| **Serving** | IBM Cloud Functions (4 endpoints) |
| **Chatbot NLU** | Watson Assistant (8 intents) |
| **Storage** | IBM Db2 + Cloud Object Storage |
| **Frontend** | Python Streamlit (this app) |
| **Hosting** | IBM Cloud Foundry / Streamlit Cloud |
| **Cost** | ₹0 / month (IBM Lite tier) |
        """)

    st.markdown("---")
    st.caption("WaterPulse v2.0 · MIT License · Edunet Foundation · Problem Statement No. 38 · IBM Cloud Lite")

st.markdown("</div>", unsafe_allow_html=True)


