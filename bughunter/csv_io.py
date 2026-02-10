"""CSV input/output helpers."""

from __future__ import annotations

import pandas as pd
from pathlib import Path


def load_input_csv(path: str | Path) -> list[dict]:
    """Read the input CSV and return a list of row-dicts.

    Expected columns: ID, Code, Context
    Optional columns: Correct Code, Explanation (used if present)
    """
    df = pd.read_csv(path)
    required = {"ID", "Code", "Context"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"Input CSV is missing columns: {missing}")

    rows: list[dict] = []
    for _, row in df.iterrows():
        rows.append(
            {
                "id": str(row["ID"]),
                "code": str(row["Code"]),
                "correct_code": str(row.get("Correct Code", "")),
                "context": str(row["Context"]),
                "explanation": str(row.get("Explanation", "")),
            }
        )
    return rows


def write_output_csv(results: list[dict], path: str | Path) -> None:
    """Write the output CSV with columns: ID, Bug Line, Explanation."""
    df = pd.DataFrame(results)
    df = df.rename(
        columns={
            "id": "ID",
            "bug_line": "Bug Line",
            "bug_explanation": "Explanation",
        }
    )
    df = df[["ID", "Bug Line", "Explanation"]]
    df.to_csv(path, index=False)
    print(f"Output written to {path} ({len(df)} rows)")
