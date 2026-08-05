import re
import traceback
from datetime import datetime

import streamlit as st

from pipeline import run_research_pipeline

st.set_page_config(page_title="Research Engine", page_icon="🛰️", layout="wide")

# ---------------------------------------------------------------------------
# Pipeline stage tokens — one accent per agent, carried through the whole UI
# ---------------------------------------------------------------------------
STAGES = [
    {"id": "search",   "num": "01", "label": "Search",    "color": "#FFD166"},
    {"id": "scraped",  "num": "02", "label": "Read",       "color": "#FFA733"},
    {"id": "report",   "num": "03", "label": "Write",      "color": "#FF6A00"},
    {"id": "feedback", "num": "04", "label": "Critique",   "color": "#FF3D00"},
]
STAGE_IDS = [s["id"] for s in STAGES]

# ---------------------------------------------------------------------------
# Style
# ---------------------------------------------------------------------------
st.markdown(
    """
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@500;600;700&family=Inter:wght@400;500;600&family=IBM+Plex+Mono:wght@400;500&family=Source+Serif+4:opsz,wght@8..60,400;8..60,600&display=swap');

:root{
  --bg:#0A0806; --surface:#161210; --surface-2:#1F1912; --border:#332822;
  --text:#F5EFE8; --text-dim:#A89C8C; --text-faint:#6B6255;
}

html, body, [class*="css"]{ font-family:'Inter', sans-serif; }

.stApp{
  background:
    repeating-linear-gradient(0deg, rgba(255,255,255,0.015) 0px, rgba(255,255,255,0.015) 1px, transparent 1px, transparent 42px),
    repeating-linear-gradient(90deg, rgba(255,255,255,0.015) 0px, rgba(255,255,255,0.015) 1px, transparent 1px, transparent 42px),
    radial-gradient(1200px 600px at 15% -10%, #241405 0%, transparent 60%),
    var(--bg);
  color: var(--text);
}
.stApp::before{
  content:""; position:fixed; inset:0; pointer-events:none; z-index:0; opacity:0.5;
  background-image:url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='120' height='120'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.9' numOctaves='2' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23n)' opacity='0.035'/%3E%3C/svg%3E");
}
#MainMenu, footer, header{ visibility:hidden; }
.block-container{ max-width:920px; padding-top:2.4rem; padding-bottom:3rem; position:relative; z-index:1; }

/* Hero */
.hero-wrap{ position:relative; padding-top:0.4rem; margin-bottom:0.4rem; }
.radar{
  position:absolute; top:-90px; left:-120px; width:340px; height:340px; z-index:0;
  background: conic-gradient(from 0deg, rgba(255,122,24,0.2), transparent 30%);
  border-radius:50%; filter: blur(6px);
  animation: spin 7s linear infinite;
}
@keyframes spin{ to{ transform: rotate(360deg); } }
.eyebrow{
  position:relative; z-index:1; font-family:'IBM Plex Mono', monospace; font-size:0.72rem;
  letter-spacing:0.24em; color: var(--text-faint); text-transform:uppercase; margin-bottom:0.6rem;
}
.eyebrow::before{ content:"● "; color:#FF7A18; }
.hero-title{
  position:relative; z-index:1; font-family:'Space Grotesk', sans-serif; font-weight:700; font-size:2.7rem;
  line-height:1.06; letter-spacing:-0.015em; margin:0 0 0.4rem 0;
  background: linear-gradient(90deg, #FFF6EC 45%, #C98B4A 100%);
  -webkit-background-clip:text; background-clip:text; -webkit-text-fill-color:transparent;
}
.hero-sub{ position:relative; z-index:1; color: var(--text-dim); font-size:0.98rem; margin-bottom:1.8rem; }
.hero-sub span{ color:#FF9F1C; font-family:'IBM Plex Mono', monospace; }

/* Command bar */
div[data-testid="stTextInput"] input{
  background: var(--surface) !important; border:1px solid var(--border) !important;
  border-left:3px solid #FF7A18 !important;
  color: var(--text) !important; border-radius:8px !important;
  font-family:'IBM Plex Mono', monospace !important; font-size:0.92rem !important;
  padding:0.85rem 1rem !important;
}
div[data-testid="stTextInput"] input:focus{
  border-color:#FF7A18 !important; border-left:3px solid #FF7A18 !important;
  box-shadow:0 0 0 3px rgba(255,122,24,0.18) !important;
}
div[data-testid="stTextInput"] input::placeholder{ color: var(--text-faint) !important; }
div[data-testid="stTextInput"] label{ display:none; }

div[data-testid="stButton"] button{
  background: linear-gradient(135deg, #FF9F1C, #FF3D00) !important;
  color:#0A0806 !important; border:none !important; border-radius:8px !important;
  font-family:'Space Grotesk', sans-serif !important; font-weight:600 !important;
  padding:0.7rem 1.4rem !important; letter-spacing:0.01em;
  transition: transform 0.15s ease, box-shadow 0.15s ease !important;
  cursor:pointer !important;
}
div[data-testid="stButton"] button:not(:disabled):hover{
  transform: translateY(-1px); box-shadow:0 6px 18px rgba(255,122,24,0.3) !important;
  cursor:pointer !important;
}
div[data-testid="stButton"] button:disabled{
  background: var(--surface-2) !important; color: var(--text-faint) !important;
  box-shadow:none !important; transform:none !important; opacity:0.65 !important;
  cursor:not-allowed !important;
}

.status-line{
  font-family:'IBM Plex Mono', monospace; font-size:0.74rem; letter-spacing:0.06em;
  color: var(--text-faint); margin:1.1rem 0 0.4rem 2px;
}
.status-line .cursor{ display:inline-block; width:7px; height:11px; background:#FF7A18; margin-left:3px;
  animation: blink 1s steps(1) infinite; vertical-align:-1px; }
@keyframes blink{ 50%{ opacity:0; } }

/* Tracker */
.tracker{ position:relative; display:flex; justify-content:space-between; margin:1rem 0 2.6rem 0; }
.tracker::before{
  content:""; position:absolute; top:9px; left:14px; right:14px; height:2px; background:var(--border); z-index:0;
}
.tracker-fill{
  position:absolute; top:9px; left:14px; height:2px; z-index:0; overflow:visible;
  background:linear-gradient(90deg, #FFD166, #FFA733, #FF6A00, #FF3D00);
  transition: width 0.5s ease;
}
.tracker-fill.live::after{
  content:""; position:absolute; top:-3px; right:-4px; width:8px; height:8px; border-radius:50%;
  background:#fff; box-shadow:0 0 8px 2px rgba(255,255,255,0.9);
  animation: travel 1.1s ease-in-out infinite;
}
@keyframes travel{ 0%,100%{ opacity:0.3; transform:scale(0.8);} 50%{ opacity:1; transform:scale(1.3);} }
.stage-node{ position:relative; z-index:1; display:flex; flex-direction:column; align-items:center; gap:0.5rem; flex:1; }
.stage-dot{
  width:18px; height:18px; border-radius:50%; background:var(--bg); border:2px solid var(--border);
  transition: all 0.3s ease;
}
.stage-node.done .stage-dot{ background: var(--accent); border-color: var(--accent); }
.stage-node.active .stage-dot{
  border-color: var(--accent); box-shadow:0 0 0 4px color-mix(in srgb, var(--accent) 25%, transparent);
  animation: pulse 1.4s ease-in-out infinite;
}
@keyframes pulse{ 0%,100%{ transform:scale(1); } 50%{ transform:scale(1.18); } }
.stage-num{ font-family:'IBM Plex Mono', monospace; font-size:0.68rem; color: var(--text-faint); }
.stage-node.active .stage-num{ color: var(--accent); }
.stage-label{ font-family:'Space Grotesk', sans-serif; font-size:0.82rem; font-weight:600; color: var(--text-faint); }
.stage-node.done .stage-label, .stage-node.active .stage-label{ color: var(--text); }

/* Tabs */
button[data-baseweb="tab"]{
  font-family:'Space Grotesk', sans-serif !important; font-weight:600 !important;
  color: var(--text-faint) !important; font-size:0.88rem !important;
}
button[data-baseweb="tab"][aria-selected="true"]{ color: var(--text) !important; }
div[data-baseweb="tab-highlight"]{ background:#FF7A18 !important; }
div[data-baseweb="tab-border"]{ background: var(--border) !important; }

/* Cards */
div[data-testid="stVerticalBlockBorderWrapper"]{
  background: var(--surface) !important; border:1px solid var(--border) !important;
  border-radius:12px !important;
}
div[data-testid="stMarkdownContainer"] p, div[data-testid="stMarkdownContainer"] li{
  font-family:'Source Serif 4', serif; font-size:1.02rem; line-height:1.68; color:#EAE1D4;
}
div[data-testid="stMarkdownContainer"] h1, div[data-testid="stMarkdownContainer"] h2, div[data-testid="stMarkdownContainer"] h3{
  font-family:'Space Grotesk', sans-serif !important; color: var(--text) !important;
}

.letterhead{ margin-bottom:1.1rem; padding-bottom:1rem; border-bottom:1px dashed var(--border); }
.letterhead .doc-title{
  font-family:'Space Grotesk', sans-serif; font-weight:700; font-size:1.3rem; color: var(--text); margin-bottom:0.35rem;
}
.letterhead .doc-meta{
  font-family:'IBM Plex Mono', monospace; font-size:0.72rem; color: var(--text-faint); letter-spacing:0.03em;
}

textarea{
  font-family:'IBM Plex Mono', monospace !important; font-size:0.85rem !important;
  background: var(--surface) !important; color:#D9CFC0 !important; border-color: var(--border) !important;
}

.card-tag{
  display:inline-block; font-family:'IBM Plex Mono', monospace; font-size:0.7rem;
  letter-spacing:0.14em; text-transform:uppercase; padding:0.25rem 0.6rem; border-radius:5px;
  margin-bottom:0.9rem;
}

div[data-testid="stStatusWidget"], div[data-testid="stAlert"]{
  background: var(--surface) !important; border:1px solid var(--border) !important; border-radius:10px !important;
}

.stamp-row{ display:flex; align-items:center; gap:1.3rem; margin-bottom:1.1rem; }
.stamp-svg{ transform: rotate(-9deg); flex-shrink:0; opacity:0.92; }
.stamp-caption{ font-family:'IBM Plex Mono', monospace; font-size:0.76rem; color: var(--text-faint); line-height:1.5; }

.log-footer{
  margin-top:3rem; padding-top:1rem; border-top:1px dashed var(--border);
  font-family:'IBM Plex Mono', monospace; font-size:0.7rem; color: var(--text-faint); letter-spacing:0.03em;
}

section[data-testid="stSidebar"]{ background: #060402; border-right:1px solid var(--border); }
</style>
""",
    unsafe_allow_html=True,
)


def get_text(value) -> str:
    if value is None:
        return ""
    return value.content if hasattr(value, "content") else str(value)


def render_tracker(states: dict, live: bool = False) -> str:
    """states: {stage_id: 'pending' | 'active' | 'done'}
    NOTE: every returned line starts at column 0 — Markdown treats a
    4-space indent as a code block, which would make Streamlit print
    this HTML as literal text instead of rendering it.
    """
    done_count = sum(1 for s in states.values() if s == "done")
    fill_pct = (done_count / len(STAGES)) * 100
    live_class = " live" if live and done_count < len(STAGES) else ""
    nodes = ""
    for stage in STAGES:
        state = states.get(stage["id"], "pending")
        nodes += (
            f'<div class="stage-node {state}" style="--accent:{stage["color"]}">'
            f'<div class="stage-num">{stage["num"]}</div>'
            f'<div class="stage-dot"></div>'
            f'<div class="stage-label">{stage["label"]}</div>'
            f'</div>'
        )
    return (
        f'<div class="tracker">'
        f'<div class="tracker-fill{live_class}" style="width:calc({fill_pct}% - 28px)"></div>'
        f'{nodes}'
        f'</div>'
    )


def extract_score(text: str):
    """Pull a rating out of the critic's free-text feedback, if it stated one."""
    patterns = [
        r'(\d{1,2}(?:\.\d)?\s*/\s*10)\b',
        r'(\d{1,3}\s*/\s*100)\b',
        r'(?:score|rating)\s*[:\-]\s*(\d{1,3}(?:\.\d)?(?:\s*/\s*\d{1,3})?)',
    ]
    for pat in patterns:
        m = re.search(pat, text, re.IGNORECASE)
        if m:
            return m.group(1).replace(" ", "")
    return None


def render_stamp(score) -> str:
    label_text = "PEER REVIEWED • AI CRITIC • " * 3
    center = score if score else "✓"
    font_size = 22 if score and len(score) <= 5 else 15
    return f"""<svg class="stamp-svg" width="108" height="108" viewBox="0 0 120 120" xmlns="http://www.w3.org/2000/svg">
<defs><path id="circlePath" d="M 60,60 m -48,0 a 48,48 0 1,1 96,0 a 48,48 0 1,1 -96,0"/></defs>
<circle cx="60" cy="60" r="52" fill="none" stroke="#FF3D00" stroke-width="1.4" stroke-dasharray="1.5 3.5" opacity="0.8"/>
<circle cx="60" cy="60" r="40" fill="none" stroke="#FF3D00" stroke-width="1.2" opacity="0.6"/>
<text font-size="7.3" letter-spacing="1.5" fill="#FF3D00"><textPath href="#circlePath" startOffset="0%">{label_text}</textPath></text>
<text x="60" y="65" font-size="{font_size}" fill="#FF3D00" text-anchor="middle" font-family="IBM Plex Mono, monospace" font-weight="600">{center}</text>
</svg>"""


# ---------------------------------------------------------------------------
# State
# ---------------------------------------------------------------------------
if "state" not in st.session_state:
    st.session_state.state = None
if "error" not in st.session_state:
    st.session_state.error = None
if "running" not in st.session_state:
    st.session_state.running = False
if "topic_run" not in st.session_state:
    st.session_state.topic_run = ""

with st.sidebar:
    st.markdown(
        "<div style='font-family:Space Grotesk,sans-serif;font-weight:700;"
        "font-size:1.1rem;color:#F5EFE8;'>🛰️ Research Engine</div>",
        unsafe_allow_html=True,
    )
    with st.expander("About"):
        st.caption("Four agents run in sequence: search, read, write, critique.")
    if st.session_state.state or st.session_state.error:
        st.divider()
        if st.button("Clear results", use_container_width=True):
            st.session_state.state = None
            st.session_state.error = None
            st.rerun()

# ---------------------------------------------------------------------------
# Hero + command bar
# ---------------------------------------------------------------------------
st.markdown(
    '<div class="hero-wrap"><div class="radar"></div>'
    '<div class="eyebrow">MULTI-AGENT PIPELINE</div>'
    '<div class="hero-title">Research Engine</div>'
    '<div class="hero-sub">Give it a topic — <span>agents</span> handle the rest.</div>'
    '</div>',
    unsafe_allow_html=True,
)

col_input, col_btn = st.columns([5, 1], vertical_alignment="bottom")
with col_input:
    topic = st.text_input(
        "topic", placeholder="→ quantum computing and modern cryptography",
        disabled=st.session_state.running, label_visibility="collapsed",
    )
with col_btn:
    run_btn = st.button(
        "Launch ↗", type="primary", use_container_width=True,
        disabled=st.session_state.running,   # <-- only gated by running, not by topic text
    )

status_line_slot = st.empty()
tracker_slot = st.empty()

initial_states = {sid: "pending" for sid in STAGE_IDS}
if not st.session_state.running and not st.session_state.state:
    status_line_slot.markdown(
        '<div class="status-line">STATUS: STANDBY<span class="cursor"></span></div>',
        unsafe_allow_html=True,
    )
    tracker_slot.markdown(render_tracker(initial_states), unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Run
# ---------------------------------------------------------------------------
if run_btn:
    if not topic.strip():
        st.toast("Enter a topic first.", icon="⚠️")
    else:
        st.session_state.running = True
        st.session_state.topic_run = topic
        st.session_state.state = None
        st.session_state.error = None
        st.rerun()

# Separate block: this runs on the rerun triggered above
if st.session_state.running and st.session_state.state is None and st.session_state.error is None:
    states = {sid: "pending" for sid in STAGE_IDS}
    states[STAGE_IDS[0]] = "active"
    status_line_slot.markdown(
        '<div class="status-line">STATUS: TRANSMITTING<span class="cursor"></span></div>',
        unsafe_allow_html=True,
    )
    tracker_slot.markdown(render_tracker(states, live=True), unsafe_allow_html=True)

    def on_update(stage: str, content):
        states[stage] = "done"
        idx = STAGE_IDS.index(stage)
        if idx + 1 < len(STAGE_IDS):
            states[STAGE_IDS[idx + 1]] = "active"
        tracker_slot.markdown(render_tracker(states, live=True), unsafe_allow_html=True)

    try:
        result = run_research_pipeline(st.session_state.topic_run, on_update=on_update)
        st.session_state.state = result
    except Exception as e:
        for sid, s in states.items():
            if s == "active":
                states[sid] = "pending"
        tracker_slot.markdown(render_tracker(states), unsafe_allow_html=True)
        st.session_state.error = f"{e}\n\n{traceback.format_exc()}"

    st.session_state.running = False
    st.rerun()

# ---------------------------------------------------------------------------
# Results
# ---------------------------------------------------------------------------
if st.session_state.error:
    st.error("Pipeline failed.")
    st.code(st.session_state.error)

if st.session_state.state:
    state = st.session_state.state
    report_text = get_text(state.get("report"))
    feedback_text = get_text(state.get("feedback"))
    scraped_text = get_text(state.get("scraped_content"))
    score = extract_score(feedback_text)
    run_time = datetime.now().strftime("%Y-%m-%d %H:%M")

    tab_report, tab_feedback, tab_scraped = st.tabs(
        ["Report", "Critique", "Source"]
    )

    with tab_report:
        with st.container(border=True):
            st.markdown(
                f'<div class="letterhead">'
                f'<div class="doc-title">{st.session_state.topic_run.strip().capitalize()}</div>'
                f'<div class="doc-meta">DRAFTED BY WRITER AGENT · {run_time} · STAGE 03</div>'
                f'</div>',
                unsafe_allow_html=True,
            )
            st.markdown(report_text)
        st.download_button("Download report (.md)", report_text, file_name="research_report.md", mime="text/markdown")

    with tab_feedback:
        with st.container(border=True):
            st.markdown(
                f'<div class="stamp-row">{render_stamp(score)}'
                f'<div class="stamp-caption">STAGE 04 · CRITIC AGENT<br>Independent review of the draft above'
                f'{" · rated " + score if score else ""}.</div></div>',
                unsafe_allow_html=True,
            )
            st.markdown(feedback_text)
        st.download_button("Download critique (.md)", feedback_text, file_name="critic_feedback.md", mime="text/markdown")

    with tab_scraped:
        st.text_area("scraped content", scraped_text, height=380, label_visibility="collapsed")

    st.markdown(
        f'<div class="log-footer">// research-engine · run logged locally · {run_time}</div>',
        unsafe_allow_html=True,
    )