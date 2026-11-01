import streamlit as st
from agents import build_reader_agent, build_search_agent, writer_chain, critic_chain

st.set_page_config(page_title="Multi-Agent Research System", page_icon="🔎", layout="wide")

st.title("🔎 Multi-Agent Research System")
st.caption("Search agent → Reader agent → Writer chain → Critic chain")

topic = st.text_input("Enter a research topic", placeholder="e.g. Impact of war on the stock market")
run = st.button("Run Research", type="primary", disabled=not topic)

if run:
    state = {}

    # Step 1 - Search agent
    with st.status("Step 1: Search agent is searching the web...", expanded=False) as s:
        search_agent = build_search_agent()
        result = search_agent.invoke({
            "messages": [("user", f"Find recent, reliable and detailed information about: {topic}")]
        })
        state["search_results"] = result["messages"][-1].content
        s.update(label="Step 1: Search complete ✅", state="complete")

    # Step 2 - Reader agent
    with st.status("Step 2: Reader agent is scraping the top source...", expanded=False) as s:
        reader_agent = build_reader_agent()
        result = reader_agent.invoke({
            "messages": [("user",
                f"Based on the following search results about '{topic}', "
                f"pick the most relevant URL and scrape it for deeper content.\n\n"
                f"Search Results:\n{state['search_results'][:800]}"
            )]
        })
        state["scraped_content"] = result["messages"][-1].content
        s.update(label="Step 2: Scraping complete ✅", state="complete")

    # Step 3 - Writer chain
    with st.status("Step 3: Writer is drafting the report...", expanded=False) as s:
        research_combined = (
            f"SEARCH RESULTS:\n{state['search_results']}\n\n"
            f"DETAILED SCRAPED CONTENT:\n{state['scraped_content']}"
        )
        state["report"] = writer_chain.invoke({"topic": topic, "research": research_combined})
        s.update(label="Step 3: Report written ✅", state="complete")

    # Step 4 - Critic chain
    with st.status("Step 4: Critic is reviewing the report...", expanded=False) as s:
        state["feedback"] = critic_chain.invoke({"report": state["report"]})
        s.update(label="Step 4: Review complete ✅", state="complete")

    st.session_state["state"] = state
    st.session_state["topic"] = topic

# Show results (kept in session_state so they survive reruns, e.g. clicking download)
if "state" in st.session_state:
    state = st.session_state["state"]

    tab1, tab2, tab3, tab4 = st.tabs(["📄 Report", "🧐 Critic Feedback", "🔍 Search Results", "📰 Scraped Content"])

    with tab1:
        st.markdown(state["report"])
        st.download_button(
            "Download report (.md)",
            data=state["report"],
            file_name="research_report.md",
            mime="text/markdown",
        )
    with tab2:
        st.markdown(state["feedback"])
    with tab3:
        st.markdown(state["search_results"])
    with tab4:
        st.markdown(state["scraped_content"])