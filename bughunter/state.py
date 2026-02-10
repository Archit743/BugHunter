"""LangGraph state schema for the BugHunter pipeline."""

from __future__ import annotations
from typing import TypedDict


class BugHunterState(TypedDict, total=False):
    """Shared state that flows through every node in the graph."""

    # ── Input fields (populated from CSV row) ──────────────────────────
    id: str
    code: str
    correct_code: str
    context: str
    explanation: str  # ground-truth explanation from input

    # ── Intermediate fields ────────────────────────────────────────────
    extracted_apis: list[str]        # API/function names found in code
    candidate_lines: list[dict]      # [{line_no, content, reason}, ...]
    doc_results: list[dict]          # [{text, score}, ...] from MCP
    static_analysis: str             # raw cppcheck / heuristic output
    search_queries: list[str]        # queries sent to MCP search

    # ── Output fields ──────────────────────────────────────────────────
    bug_line: str                    # identified bug line content
    bug_explanation: str             # explanation of the bug

    # ── Control fields ─────────────────────────────────────────────────
    iteration: int                   # current retrieval-verify cycle
    max_iterations: int              # cap for the loop (default 2)
    confidence: str                  # "high" | "low"
    error: str                       # error message if something fails
