import re
import time
import html

import streamlit as st
from agents import build_reader_agent, build_search_agent, writer_chain, critic_chain

# ──────────────────────────────────────────────────────────────
# Page setup
# ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Multi-Agent Research System",
    page_icon="🔎",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ──────────────────────────────────────────────────────────────
# Styles
# ──────────────────────────────────────────────────────────────
st.markdown(
    """
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@500;600;700&family=Inter:wght@400;500;600&family=JetBrains+Mono:wght@400;500&display=swap');

:root {
    --bg: #0B0F17;
    --panel: #121826;
    --panel-2: #171F30;
    --line: #232D42;
    --text: #E6EAF2;
    --muted: #8A94A8;
    --accent: #7C5CFF;
    --accent-2: #22D3EE;
    --ok: #34D399;
    --warn: #FBBF24;
    --bad: #F87171;
}

html, body, [class*="css"], .stMarkdown, p, li, label, input, textarea, button {
    font-family: 'Inter', sans-serif;
}
.stApp {
    background:
        radial-gradient(900px 500px at 10% -10%, rgba(124,92,255,0.18), transparent 60%),
        radial-gradient(800px 500px at 100% 0%, rgba(34,211,238,0.10), transparent 60%),
        var(--bg);
}
header[data-testid="stHeader"] { background: transparent; }
.block-container { padding-top: 2.2rem; max-width: 1200px; }
#MainMenu, footer { visibility: hidden; }

/* ── Hero ─────────────────────────────── */
.hero { text-align: center; margin: 0.5rem 0 1.8rem; }
.hero-badge {
    display: inline-flex; align-items: center; gap: .45rem;
    padding: .35rem .85rem; border-radius: 999px;
    border: 1px solid var(--line); background: rgba(18,24,38,.7);
    color: var(--muted); font-size: .8rem; letter-spacing: .02em;
}
.hero-badge .dot { width: 7px; height: 7px; border-radius: 50%; background: var(--ok); box-shadow: 0 0 10px var(--ok); }
.hero h1 {
    font-family: 'Space Grotesk', sans-serif !important; font-weight: 700;
    font-size: clamp(2.1rem, 4.5vw, 3.4rem); line-height: 1.08;
    margin: 1rem 0 .6rem; color: var(--text); letter-spacing: -0.02em;
}
.hero h1 span {
    background: linear-gradient(90deg, var(--accent), var(--accent-2));
    -webkit-background-clip: text; background-clip: text; color: transparent;
}
.hero p { color: var(--muted); font-size: 1.05rem; max-width: 640px; margin: 0 auto; }

/* ── Input ────────────────────────────── */
div[data-testid="stForm"] {
    background: var(--panel); border: 1px solid var(--line);
    border-radius: 18px; padding: 1.1rem 1.2rem .9rem;
    box-shadow: 0 20px 60px rgba(0,0,0,.35);
}
div[data-testid="stTextInput"] input {
    background: var(--bg) !important; color: var(--text) !important;
    border: 1px solid var(--line) !important; border-radius: 12px !important;
    padding: .85rem 1rem !important; font-size: 1.02rem !important;
}
div[data-testid="stTextInput"] input:focus {
    border-color: var(--accent) !important;
    box-shadow: 0 0 0 3px rgba(124,92,255,.25) !important;
}
div[data-testid="stFormSubmitButton"] button, .stDownloadButton button {
    background: linear-gradient(90deg, var(--accent), #5B8CFF) !important;
    color: white !important; border: none !important; border-radius: 12px !important;
    font-weight: 600 !important; padding: .72rem 1.2rem !important;
    transition: transform .15s ease, box-shadow .15s ease;
}
div[data-testid="stFormSubmitButton"] button:hover, .stDownloadButton button:hover {
    transform: translateY(-1px); box-shadow: 0 10px 25px rgba(124,92,255,.35);
}

/* Example chips */
.chips-label { color: var(--muted); font-size: .82rem; margin: .9rem 0 .35rem; }
div[data-testid="stHorizontalBlock"] .chip-row button,
.stButton button {
    background: var(--panel) !important; color: var(--text) !important;
    border: 1px solid var(--line) !important; border-radius: 999px !important;
    font-size: .85rem !important; padding: .35rem .9rem !important;
    transition: border-color .15s ease, background .15s ease;
}
.stButton button:hover { border-color: var(--accent) !important; background: var(--panel-2) !important; }

/* ── Pipeline tracker ─────────────────── */
.pipeline { display: grid; grid-template-columns: repeat(4, 1fr); gap: .8rem; margin: 1.6rem 0 1.2rem; }
@media (max-width: 800px) { .pipeline { grid-template-columns: repeat(2, 1fr); } }
.step {
    position: relative; background: var(--panel); border: 1px solid var(--line);
    border-radius: 16px; padding: 1rem 1rem .9rem; overflow: hidden;
    transition: border-color .3s ease, transform .3s ease;
}
.step .num { font-family: 'JetBrains Mono', monospace; font-size: .72rem; color: var(--muted); }
.step .icon { font-size: 1.5rem; margin: .35rem 0 .2rem; }
.step .name { font-family: 'Space Grotesk', sans-serif; font-weight: 600; color: var(--text); font-size: 1.02rem; }
.step .desc { color: var(--muted); font-size: .8rem; margin-top: .15rem; }
.step .status { margin-top: .7rem; font-size: .75rem; font-weight: 600; display: flex; align-items: center; gap: .4rem; }
.step.idle .status { color: var(--muted); }
.step.running { border-color: var(--accent); transform: translateY(-3px); box-shadow: 0 12px 30px rgba(124,92,255,.25); }
.step.running .status { color: var(--accent-2); }
.step.running::after {
    content: ""; position: absolute; left: 0; bottom: 0; height: 3px; width: 40%;
    background: linear-gradient(90deg, transparent, var(--accent-2), transparent);
    animation: scan 1.2s linear infinite;
}
.step.done { border-color: rgba(52,211,153,.45); }
.step.done .status { color: var(--ok); }
.step.error { border-color: var(--bad); }
.step.error .status { color: var(--bad); }
@keyframes scan { from { left: -40%; } to { left: 100%; } }
.spinner {
    width: 11px; height: 11px; border-radius: 50%;
    border: 2px solid rgba(34,211,238,.25); border-top-color: var(--accent-2);
    animation: spin .8s linear infinite;
}
@keyframes spin { to { transform: rotate(360deg); } }

/* ── Stat cards ───────────────────────── */
.stats { display: grid; grid-template-columns: repeat(4, 1fr); gap: .8rem; margin: .4rem 0 1.4rem; }
@media (max-width: 800px) { .stats { grid-template-columns: repeat(2, 1fr); } }
.stat { background: var(--panel); border: 1px solid var(--line); border-radius: 16px; padding: 1rem 1.1rem; }
.stat .label { color: var(--muted); font-size: .78rem; text-transform: uppercase; letter-spacing: .06em; }
.stat .value { font-family: 'Space Grotesk', sans-serif; font-size: 1.9rem; font-weight: 700; color: var(--text); margin-top: .2rem; }
.stat .value small { font-size: 1rem; color: var(--muted); font-weight: 500; }

/* ── Tabs ─────────────────────────────── */
.stTabs [data-baseweb="tab-list"] { gap: .4rem; border-bottom: 1px solid var(--line); }
.stTabs [data-baseweb="tab"] {
    background: transparent; border-radius: 10px 10px 0 0; padding: .6rem 1rem;
    color: var(--muted); font-weight: 500;
}
.stTabs [aria-selected="true"] { color: var(--text) !important; background: var(--panel) !important; }
.stTabs [data-baseweb="tab-highlight"] { background: linear-gradient(90deg, var(--accent), var(--accent-2)); }

/* ── Report / panels ──────────────────── */
.panel-title { font-family: 'Space Grotesk', sans-serif; font-size: 1.35rem; font-weight: 600; color: var(--text); margin: .2rem 0 .8rem; }
.report-meta { color: var(--muted); font-size: .85rem; margin-bottom: 1rem; }
div[data-testid="stVerticalBlockBorderWrapper"] {
    background: var(--panel); border-color: var(--line) !important; border-radius: 16px !important;
}

/* Critic */
.score-wrap { display: flex; align-items: center; gap: 1.4rem; flex-wrap: wrap; margin-bottom: 1.2rem; }
.ring {
    --p: 0; --c: var(--ok);
    width: 128px; height: 128px; border-radius: 50%; display: grid; place-items: center;
    background: conic-gradient(var(--c) calc(var(--p) * 1%), var(--line) 0);
}
.ring .inner {
    width: 104px; height: 104px; border-radius: 50%; background: var(--panel);
    display: grid; place-items: center; text-align: center;
}
.ring .n { font-family: 'Space Grotesk', sans-serif; font-size: 2.1rem; font-weight: 700; color: var(--text); line-height: 1; }
.ring .d { color: var(--muted); font-size: .8rem; }
.verdict {
    flex: 1; min-width: 240px; background: var(--panel-2); border-left: 3px solid var(--accent);
    border-radius: 10px; padding: .9rem 1.1rem; color: var(--text); font-size: 1.02rem; font-style: italic;
}
.verdict .lbl { display: block; font-style: normal; color: var(--muted); font-size: .75rem; text-transform: uppercase; letter-spacing: .06em; margin-bottom: .3rem; }
.fb-card { background: var(--panel); border: 1px solid var(--line); border-radius: 16px; padding: 1rem 1.2rem; height: 100%; }
.fb-card h4 { font-family: 'Space Grotesk', sans-serif; margin: 0 0 .6rem; font-size: 1.05rem; }
.fb-card.good h4 { color: var(--ok); }
.fb-card.improve h4 { color: var(--warn); }
.fb-card ul { margin: 0; padding-left: 1.1rem; color: var(--text); }
.fb-card li { margin-bottom: .45rem; line-height: 1.5; }

/* Sources */
.src {
    display: block; background: var(--panel);
    border: 1px solid var(--line); border-radius: 14px; padding: .9rem 1.1rem; margin-bottom: .7rem;
    transition: border-color .15s ease, transform .15s ease;
}
.src:hover { border-color: var(--accent); transform: translateX(3px); }
.src a.t { color: var(--text) !important; font-weight: 600; font-size: .98rem; text-decoration: none !important; }
.src a.t:hover { color: var(--accent-2) !important; }
.src .u { color: var(--accent-2); font-family: 'JetBrains Mono', monospace; font-size: .75rem; margin: .2rem 0 .35rem; word-break: break-all; }
.src .s { color: var(--muted); font-size: .87rem; line-height: 1.5; }

.scraped {
    background: var(--bg); border: 1px solid var(--line); border-radius: 14px; padding: 1rem 1.2rem;
    color: #C3CAD8; font-size: .9rem; line-height: 1.65; max-height: 520px; overflow-y: auto; white-space: pre-wrap;
}

.empty {
    text-align: center; border: 1px dashed var(--line); border-radius: 18px; padding: 2.4rem 1rem;
    color: var(--muted); margin-top: 1.2rem;
}
.empty .big { font-size: 2rem; margin-bottom: .4rem; }
.footer { text-align: center; color: var(--muted); font-size: .8rem; margin: 3rem 0 1rem; }
</style>
""",
    unsafe_allow_html=True,
)

# ──────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────
STEPS = [
    ("🔍", "Search Agent", "Finds sources with Tavily"),
    ("📖", "Reader Agent", "Scrapes the best source"),
    ("✍️", "Writer", "Drafts the report"),
    ("🧐", "Critic", "Scores and reviews"),
]
STATUS_TEXT = {
    "idle": "Waiting",
    "running": '<span class="spinner"></span> Working…',
    "done": "✓ Done",
    "error": "✕ Failed",
}


def render_pipeline(placeholder, statuses):
    cards = []
    for i, ((icon, name, desc), status) in enumerate(zip(STEPS, statuses), start=1):
        cards.append(
            f'<div class="step {status}">'
            f'<div class="num">STEP 0{i}</div>'
            f'<div class="icon">{icon}</div>'
            f'<div class="name">{name}</div>'
            f'<div class="desc">{desc}</div>'
            f'<div class="status">{STATUS_TEXT[status]}</div>'
            f"</div>"
        )
    placeholder.markdown(f'<div class="pipeline">{"".join(cards)}</div>', unsafe_allow_html=True)


def parse_sources(text):
    """Pull Title / URL / Snippet blocks out of the search agent output."""
    sources = []
    for block in re.split(r"\n-{3,}\n", text):
        url = re.search(r"URL:\s*(\S+)", block)
        if not url:
            continue
        title = re.search(r"Title:\s*(.+)", block)
        snippet = re.search(r"Snippet:\s*(.+)", block, re.S)
        sources.append({
            "title": title.group(1).strip() if title else url.group(1),
            "url": url.group(1).strip(),
            "snippet": snippet.group(1).strip() if snippet else "",
        })
    if not sources:  # agent may have rewritten results in its own words
        for u in dict.fromkeys(re.findall(r"https?://[^\s\)\]>\"']+", text)):
            sources.append({"title": u.split("/")[2], "url": u, "snippet": ""})
    return sources


def parse_feedback(text):
    """Split the critic output into score, strengths, improvements, verdict."""
    score = re.search(r"Score:\s*\**\s*(\d+(?:\.\d+)?)\s*/\s*10", text, re.I)

    def section(name, stop):
        m = re.search(rf"{name}:?\**\s*\n(.*?)(?=\n\s*\**(?:{stop})|\Z)", text, re.S | re.I)
        if not m:
            return []
        items = [re.sub(r"^\s*[-*•\d.]+\s*", "", line).strip() for line in m.group(1).splitlines()]
        return [i for i in items if i]

    strengths = section("Strengths", "Areas to Improve|One line verdict")
    improve = section("Areas to Improve", "One line verdict")
    verdict = re.search(r"One line verdict:?\**\s*\n?\s*(.+)", text, re.I)
    return {
        "score": float(score.group(1)) if score else None,
        "strengths": strengths,
        "improve": improve,
        "verdict": verdict.group(1).strip() if verdict else "",
    }


def set_topic(example):
    st.session_state["topic_input"] = example


# ──────────────────────────────────────────────────────────────
# Hero + input
# ──────────────────────────────────────────────────────────────
st.markdown(
    """
<div class="hero">
  <div class="hero-badge"><span class="dot"></span> 4 agents · LangChain · GPT 4o mini · Tavily</div>
  <h1>Research anything with a <span>team of AI agents</span></h1>
  <p>Type a topic. One agent searches the web, one reads the best source, one writes the report, and one critiques it.</p>
</div>
""",
    unsafe_allow_html=True,
)

with st.form("research_form", border=False):
    c1, c2 = st.columns([5, 1], vertical_alignment="bottom")
    with c1:
        topic = st.text_input(
            "Research topic",
            key="topic_input",
            placeholder="e.g. Impact of war on the stock market",
            label_visibility="collapsed",
        )
    with c2:
        run = st.form_submit_button("Run research  →", use_container_width=True)

st.markdown('<div class="chips-label">Try an example</div>', unsafe_allow_html=True)
examples = [
    "War and the stock market",
    "Solid state batteries",
    "AI in supply chains",
    "Digital twins in industry",
]
chip_cols = st.columns(len(examples))
for col, ex in zip(chip_cols, examples):
    col.button(ex, key=f"ex_{ex}", on_click=set_topic, args=(ex,), use_container_width=True)

pipeline_slot = st.empty()

# ──────────────────────────────────────────────────────────────
# Run the pipeline
# ──────────────────────────────────────────────────────────────
if run and not topic.strip():
    st.toast("Enter a topic first", icon="✏️")

if run and topic.strip():
    topic = topic.strip()
    statuses = ["idle"] * 4
    state = {}
    start = time.time()
    current = 0

    try:
        # Step 1: search
        current = 0
        statuses[0] = "running"; render_pipeline(pipeline_slot, statuses)
        result = build_search_agent().invoke({
            "messages": [("user", f"Find recent, reliable and detailed information about: {topic}")]
        })
        state["search_results"] = result["messages"][-1].content
        statuses[0] = "done"

        # Step 2: read
        current = 1
        statuses[1] = "running"; render_pipeline(pipeline_slot, statuses)
        result = build_reader_agent().invoke({
            "messages": [("user",
                f"Based on the following search results about '{topic}', "
                f"pick the most relevant URL and scrape it for deeper content.\n\n"
                f"Search Results:\n{state['search_results'][:800]}"
            )]
        })
        state["scraped_content"] = result["messages"][-1].content
        statuses[1] = "done"

        # Step 3: write
        current = 2
        statuses[2] = "running"; render_pipeline(pipeline_slot, statuses)
        research_combined = (
            f"SEARCH RESULTS:\n{state['search_results']}\n\n"
            f"DETAILED SCRAPED CONTENT:\n{state['scraped_content']}"
        )
        state["report"] = writer_chain.invoke({"topic": topic, "research": research_combined})
        statuses[2] = "done"

        # Step 4: critique
        current = 3
        statuses[3] = "running"; render_pipeline(pipeline_slot, statuses)
        state["feedback"] = critic_chain.invoke({"report": state["report"]})
        statuses[3] = "done"; render_pipeline(pipeline_slot, statuses)

        state["elapsed"] = time.time() - start
        st.session_state["state"] = state
        st.session_state["topic"] = topic
        st.toast("Research complete", icon="✅")

    except Exception as e:
        statuses[current] = "error"
        render_pipeline(pipeline_slot, statuses)
        st.error(f"**{STEPS[current][1]} failed:** {e}")
        st.stop()

# ──────────────────────────────────────────────────────────────
# Results
# ──────────────────────────────────────────────────────────────
if "state" in st.session_state:
    state = st.session_state["state"]
    if not run:
        render_pipeline(pipeline_slot, ["done"] * 4)

    sources = parse_sources(state["search_results"])
    fb = parse_feedback(state["feedback"])
    words = len(state["report"].split())
    score_txt = f'{fb["score"]:g}<small>/10</small>' if fb["score"] is not None else "–"

    st.markdown(
        f"""
<div class="stats">
  <div class="stat"><div class="label">Critic score</div><div class="value">{score_txt}</div></div>
  <div class="stat"><div class="label">Sources found</div><div class="value">{len(sources)}</div></div>
  <div class="stat"><div class="label">Report length</div><div class="value">{words:,}<small> words</small></div></div>
  <div class="stat"><div class="label">Time taken</div><div class="value">{state.get("elapsed", 0):.0f}<small> s</small></div></div>
</div>
""",
        unsafe_allow_html=True,
    )

    tab1, tab2, tab3, tab4 = st.tabs(["📄 Report", "🧐 Critic feedback", "🔗 Sources", "📰 Scraped content"])

    # Report
    with tab1:
        top_l, top_r = st.columns([4, 1], vertical_alignment="center")
        top_l.markdown(
            f'<div class="panel-title">{html.escape(st.session_state["topic"])}</div>'
            f'<div class="report-meta">Generated report · {words:,} words · about {max(1, words // 200)} min read</div>',
            unsafe_allow_html=True,
        )
        slug = re.sub(r"[^a-z0-9]+", "_", st.session_state["topic"].lower()).strip("_")[:50] or "report"
        top_r.download_button(
            "⬇ Download .md",
            data=state["report"],
            file_name=f"{slug}.md",
            mime="text/markdown",
            use_container_width=True,
        )
        with st.container(border=True):
            st.markdown(state["report"])

    # Critic
    with tab2:
        if fb["score"] is not None:
            pct = fb["score"] * 10
            color = "var(--ok)" if fb["score"] >= 8 else "var(--warn)" if fb["score"] >= 6 else "var(--bad)"
            st.markdown(
                f"""
<div class="score-wrap">
  <div class="ring" style="--p:{pct}; --c:{color};">
    <div class="inner"><div><div class="n">{fb["score"]:g}</div><div class="d">out of 10</div></div></div>
  </div>
  <div class="verdict"><span class="lbl">Verdict</span>{html.escape(fb["verdict"]) or "No verdict given."}</div>
</div>
""",
                unsafe_allow_html=True,
            )
        if fb["strengths"] or fb["improve"]:
            g, i = st.columns(2)

            def bullets(items):
                return "".join(f"<li>{html.escape(x)}</li>" for x in items) or "<li>None listed</li>"

            g.markdown(f'<div class="fb-card good"><h4>✓ Strengths</h4><ul>{bullets(fb["strengths"])}</ul></div>',
                       unsafe_allow_html=True)
            i.markdown(f'<div class="fb-card improve"><h4>↗ Areas to improve</h4><ul>{bullets(fb["improve"])}</ul></div>',
                       unsafe_allow_html=True)
        else:  # critic didn't follow the format, show it raw
            with st.container(border=True):
                st.markdown(state["feedback"])

    # Sources
    with tab3:
        if sources:
            st.markdown(
                "".join(
                    f'<div class="src">'
                    f'<a class="t" href="{html.escape(s["url"])}" target="_blank" rel="noopener">{html.escape(s["title"])} ↗</a>'
                    f'<div class="u">{html.escape(s["url"])}</div>'
                    f'<div class="s">{html.escape(s["snippet"][:300])}</div></div>'
                    for s in sources
                ),
                unsafe_allow_html=True,
            )
        else:
            with st.container(border=True):
                st.markdown(state["search_results"])

    # Scraped content
    with tab4:
        st.markdown(f'<div class="scraped">{html.escape(state["scraped_content"])}</div>', unsafe_allow_html=True)

else:
    render_pipeline(pipeline_slot, ["idle"] * 4)
    st.markdown(
        '<div class="empty"><div class="big">🧭</div>'
        "Pick an example or type your own topic to start the agents.</div>",
        unsafe_allow_html=True,
    )

st.markdown(
    '<div class="footer">Built by Vikram Hawladar · '
    '<a href="https://github.com/VIPRAX17/multi-agent-research-system" target="_blank" style="color:#8A94A8">GitHub</a></div>',
    unsafe_allow_html=True,
)
