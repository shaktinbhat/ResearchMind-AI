from agents import build_reader_agent, build_search_agent, writer_chain, critic_chain


def run_research_pipeline(topic: str, on_update=None) -> dict:
    """
    Runs the 4-stage multi-agent research pipeline:
    search -> read -> write -> critique.

    Args:
        topic: the research topic to investigate.
        on_update: optional callable(stage: str, content) invoked right
            after each stage finishes. Stage names are:
            "search", "scraped", "report", "feedback".
            Lets a UI (e.g. Streamlit) show live progress without
            waiting for the whole pipeline to finish.

    Returns:
        dict with keys: search_results, scraped_content, report, feedback
    """

    def notify(stage, content):
        if on_update:
            on_update(stage, content)

    state = {}

    # step-1 searcher agent
    search_agent = build_search_agent()
    search_result = search_agent.invoke({
        "messages": [("user", f"Find recent, reliable and detailed infromation about: {topic}")]
    })

    state["search_results"] = search_result["messages"][-1].content
    print("\n Search Results", state['search_results'])
    notify("search", state["search_results"])

    # step-2 Reader agent
    reader_agent = build_reader_agent()
    reader_results = reader_agent.invoke({
        "messages": [("user",
                      f"Based on th following search results about '{topic}',"
                      f"Pick the most relevent URL and scrape it for deeper content.\n\n"
                      f"Search Results:\n{state['search_results'][:800]}")]
    })

    state["scraped_content"] = reader_results['messages'][-1].content
    print("\n scraped content \n", state['scraped_content'])
    notify("scraped", state["scraped_content"])

    # step-3 writer
    print("\n Writer Drafting  Report\n")

    research_combined = (
        f"SEARCH RESULTS : \n {state['search_results']}\n\n"
        f"Detailed SCRAPED CONTENT: \n {state['scraped_content']}"
    )

    state["report"] = writer_chain.invoke({
        "topic": topic,
        "research": research_combined
    })

    print("\n Final Report \n", state["report"])
    notify("report", state["report"])

    # step-4 critic report
    print("\n critic is reviiewing the report \n")

    state["feedback"] = critic_chain.invoke({
        "report": state["report"]
    })

    print("\n critic report \n", state["feedback"])
    notify("feedback", state["feedback"])

    return state


if __name__ == "__main__":
    topic = input("\n Enter the research topic: ")
    run_research_pipeline(topic)