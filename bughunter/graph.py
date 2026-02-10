"""LangGraph workflow assembly for the BugHunter pipeline."""

from __future__ import annotations

from langgraph.graph import StateGraph, END

from bughunter.state import BugHunterState
from bughunter.nodes.code_analyzer import code_analyzer_node
from bughunter.nodes.doc_retriever import doc_retriever_node
from bughunter.nodes.verifier import verifier_node, should_retry
from bughunter.nodes.reporter import reporter_node


def build_graph():
    """Construct and compile the BugHunter LangGraph.

    Flow:
        code_analyzer -> doc_retriever -> verifier -> reporter -> END
        verifier loops back to doc_retriever on low confidence (up to max_iterations).
    """
    graph = StateGraph(BugHunterState)

    graph.add_node("code_analyzer", code_analyzer_node)
    graph.add_node("doc_retriever", doc_retriever_node)
    graph.add_node("verifier", verifier_node)
    graph.add_node("reporter", reporter_node)

    graph.set_entry_point("code_analyzer")
    graph.add_edge("code_analyzer", "doc_retriever")
    graph.add_edge("doc_retriever", "verifier")

    graph.add_conditional_edges(
        "verifier",
        should_retry,
        {
            "reporter": "reporter",
            "doc_retriever": "doc_retriever",
        },
    )

    graph.add_edge("reporter", END)

    return graph.compile()
