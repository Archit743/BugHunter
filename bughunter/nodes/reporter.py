"""reporter node - formats final output for the CSV."""

from __future__ import annotations

import re

from bughunter.state import BugHunterState


def _clean_line_numbers(raw: str) -> str:
    """Extract and normalize line numbers to a clean comma-separated string."""
    numbers = re.findall(r'\d+', raw)
    if not numbers:
        return "1"
    seen: set[str] = set()
    unique: list[str] = []
    for n in numbers:
        if n not in seen:
            seen.add(n)
            unique.append(n)
    return ",".join(unique)


def _clean_explanation(text: str) -> str:
    """Remove hedging phrases and keep explanation concise."""
    hedges = [
        r"Note:.*$",
        r"However,? without.*$",
        r"Further verification.*$",
        r"These potential.*$",
        r"It is essential to verify.*$",
        r"The exact allowed ranges.*$",
        r"This would need to be verified.*$",
    ]
    lines = text.strip().splitlines()
    cleaned = []
    for line in lines:
        skip = False
        for hedge in hedges:
            if re.search(hedge, line.strip(), re.IGNORECASE):
                skip = True
                break
        if not skip and line.strip():
            cleaned.append(line.strip())
    result = " ".join(cleaned)
    result = re.sub(r'\s+', ' ', result).strip()
    return result


def reporter_node(state: BugHunterState) -> dict:
    """Produce the final bug report fields for the output CSV."""
    bug_line = state.get("bug_line", "").strip()
    bug_explanation = state.get("bug_explanation", "").strip()

    if bug_line and bug_line != "ERROR":
        bug_line = _clean_line_numbers(bug_line)

    bug_explanation = _clean_explanation(bug_explanation)

    if not bug_line or bug_line == "1":
        candidates = state.get("candidate_lines", [])
        if candidates:
            line_nos = [str(c.get("line_no", "")) for c in candidates if c.get("line_no")]
            if line_nos:
                bug_line = ",".join(line_nos[:3])
            if not bug_explanation:
                bug_explanation = "; ".join(
                    c.get("reason", "") for c in candidates[:3] if c.get("reason")
                )

    if not bug_line:
        bug_line = "Unable to identify"
    if not bug_explanation:
        bug_explanation = "Analysis inconclusive."

    return {
        "bug_line": bug_line,
        "bug_explanation": bug_explanation,
    }
