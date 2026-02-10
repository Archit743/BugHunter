"""verifier node - cross-references code against documentation to confirm bugs."""

from __future__ import annotations

from langchain_core.messages import SystemMessage, HumanMessage

from bughunter.llm import get_llm, invoke_with_retry
from bughunter.state import BugHunterState


SYSTEM_PROMPT = """\
You are a precise C++ RDI semiconductor bug verifier.

You receive BUGGY CODE (numbered), CONTEXT, CANDIDATE LINES, DOCS, and STATIC hints.

RULES:
- Only flag a line if you can point to a CONCRETE error (wrong name, wrong value,
  wrong argument order, wrong API, wrong lifecycle order, wrong pin name, etc.).
- Do NOT flag a line just because you are "unsure" or it "may" be wrong.
- Do NOT flag lines that are correct according to the docs and context.
- If the same logical statement spans multiple physical lines (method chaining),
  report the FIRST line of that statement only.
- Keep the explanation SHORT (2-3 sentences max). State WHAT is wrong and WHAT it
  should be. No hedging, no "may", no "should be verified".

Output format (no markdown, no fences):

CONFIDENCE: high|low
BUG_LINES: <comma-separated line numbers>
EXPLANATION: <concise explanation of each bug>
"""

MAX_DOC_CHARS = 6000
MAX_CODE_CHARS = 4000


def _truncate(text: str, max_chars: int) -> str:
    if len(text) <= max_chars:
        return text
    return text[:max_chars] + "\n... [truncated]"


def _number_lines(code: str) -> str:
    """Add line numbers to code for reference."""
    lines = code.splitlines()
    return "\n".join(f"{i}: {line}" for i, line in enumerate(lines, 1))


def verifier_node(state: BugHunterState) -> dict:
    """Verify the bug by comparing code against docs."""
    code = state["code"]
    numbered_code = _number_lines(code)
    numbered_code = _truncate(numbered_code, MAX_CODE_CHARS)
    context = state.get("context", "")[:1000]
    candidates = state.get("candidate_lines", [])[:5]
    doc_results = state.get("doc_results", [])
    static_analysis = state.get("static_analysis", "")[:500]
    iteration = state.get("iteration", 0)

    cand_text = "\n".join(
        f"L{c['line_no']}: {c['content']} - {c['reason']}" for c in candidates
    )

    doc_snippets = []
    total_doc_chars = 0
    for d in doc_results[:5]:
        snippet = d.get("text", "")[:1200]
        if total_doc_chars + len(snippet) > MAX_DOC_CHARS:
            break
        doc_snippets.append(f"[{d.get('score', '?')}] {snippet}")
        total_doc_chars += len(snippet)
    doc_text = "\n---\n".join(doc_snippets) if doc_snippets else "No docs found."

    user_content = (
        f"BUGGY CODE (with line numbers):\n{numbered_code}\n\n"
        f"CONTEXT: {context}\n\n"
        f"CANDIDATES:\n{cand_text}\n\n"
        f"DOCS:\n{doc_text}\n\n"
        f"STATIC: {static_analysis}"
    )

    llm = get_llm(temperature=0)
    text = invoke_with_retry(
        llm,
        [SystemMessage(content=SYSTEM_PROMPT), HumanMessage(content=user_content)],
    )

    confidence = "low"
    bug_line = ""
    bug_explanation = ""
    refined_queries: list[str] = []

    for line in text.splitlines():
        line_stripped = line.strip()
        if line_stripped.startswith("CONFIDENCE:"):
            confidence = line_stripped.split(":", 1)[1].strip().lower()
        elif line_stripped.startswith("BUG_LINES:"):
            bug_line = line_stripped.split(":", 1)[1].strip()
        elif line_stripped.startswith("BUG_LINE:"):
            bug_line = line_stripped.split(":", 1)[1].strip()

    if "EXPLANATION:" in text:
        expl_section = text.split("EXPLANATION:", 1)[1]
        if "REFINED_QUERIES:" in expl_section:
            expl_section = expl_section.split("REFINED_QUERIES:")[0]
        bug_explanation = expl_section.strip()

    if "REFINED_QUERIES:" in text:
        rq_section = text.split("REFINED_QUERIES:")[1].strip()
        refined_queries = [q.strip() for q in rq_section.splitlines() if q.strip()]

    iteration += 1
    print(f"  Verified (iter {iteration}): confidence={confidence}, lines={bug_line}")

    result: dict = {
        "bug_line": bug_line,
        "bug_explanation": bug_explanation,
        "confidence": confidence,
        "iteration": iteration,
    }

    if confidence == "low" and refined_queries:
        result["search_queries"] = refined_queries

    return result


def should_retry(state: BugHunterState) -> str:
    """Conditional edge: route back to doc_retriever or forward to reporter."""
    confidence = state.get("confidence", "low")
    iteration = state.get("iteration", 0)
    max_iter = state.get("max_iterations", 2)

    if confidence == "high" or iteration >= max_iter:
        return "reporter"
    return "doc_retriever"
