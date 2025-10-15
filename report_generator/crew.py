from __future__ import annotations
from langgraph.graph import StateGraph, END, START
from langgraph.prebuilt import ToolNode, tools_condition
from langchain_core.messages import HumanMessage

from .crew_agents import State, CrewAgent
from .tools import web_search, generate_pdf_report, pushover_notify

# ~~~ Per-agent tool permissions ~~~
researcher_tools = [web_search]
reporter_tools = [generate_pdf_report]
reviewer_tools = [pushover_notify]

#~~~ Agents ~~~
researcher = CrewAgent("researcher_agent", "researcher.yaml", tools=researcher_tools, temperature=1.0)
reporter = CrewAgent("reporter_agent",  "reporter.yaml", tools=reporter_tools, temperature=1.0)
reviewer = CrewAgent("reviewer_agent", "reviewer.yaml", tools=reviewer_tools, temperature=1.0)

#~~~ ToolNodes for each agent
researcher_tool_node = ToolNode(researcher_tools)
reporter_tool_node = ToolNode(reporter_tools)
reviewer_tool_node = ToolNode(reviewer_tools)

def CreateCrew():
    graph = StateGraph(State)

    # Graph nodes:
    graph.add_node("researcher", researcher)
    graph.add_node("researcher_tools", researcher_tool_node)
    graph.add_node("reporter", reporter)
    graph.add_node("reporter_tools", reporter_tool_node)
    graph.add_node("reviewer", reviewer)
    graph.add_node("reviewer_tools", reviewer_tool_node)

    graph.set_entry_point("researcher")

    graph.add_conditional_edges(
        "researcher", tools_condition,
        {"tools": "researcher_tools", END: "reporter"}
    )
    graph.add_edge("researcher_tools", "researcher")

    graph.add_conditional_edges(
        "reporter", tools_condition,
        {"tools": "reporter_tools", END: "reviewer"}
    )
    graph.add_edge("reporter_tools", "reporter")

    graph.add_conditional_edges(
        "reviewer", tools_condition,
        {"tools": "reviewer_tools", END: END}
    )
    graph.add_edge("reviewer_tools", "reviewer")
    return graph.compile()


