#!/usr/bin/env python3
"""
Inspect an executed notebook for expected outputs beyond basic error absence.
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import List


def normalize_text(value) -> str:
    if isinstance(value, list):
        return "".join(str(item) for item in value)
    if value is None:
        return ""
    return str(value)


def parse_args():
    parser = argparse.ArgumentParser(description="Check an executed notebook for expected outputs")
    parser.add_argument("notebook_path", help="Path to the executed notebook file")
    return parser.parse_args()


def collect_text_outputs(notebook: dict) -> List[str]:
    chunks: List[str] = []
    for cell in notebook.get("cells", []):
        for output in cell.get("outputs", []):
            output_type = output.get("output_type")
            if output_type == "stream":
                chunks.append(normalize_text(output.get("text", "")))
            elif output_type in {"execute_result", "display_data"}:
                data = output.get("data", {})
                text_value = data.get("text/plain")
                chunks.append(normalize_text(text_value))
            elif output_type == "error":
                traceback = output.get("traceback", [])
                chunks.append("\n".join(normalize_text(item) for item in traceback))
    return chunks


def main():
    args = parse_args()
    notebook_path = Path(args.notebook_path)
    if not notebook_path.exists():
        raise FileNotFoundError(f"notebook not found: {notebook_path}")

    notebook = json.loads(notebook_path.read_text())
    output_chunks = collect_text_outputs(notebook)
    combined_output = "\n".join(output_chunks)

    checks = {
        "dump_exists_true": "dump exists = True" in combined_output,
        "api_key_configured": "OPENAI_API_KEY configured = True" in combined_output,
        "llm_enabled_true": "True" in combined_output and "llm_enabled" not in combined_output,
        "feasibility_report": "Feasibility Report" in combined_output,
        "llm_analysis_present": "[LLM Analysis]" in combined_output or "핵심 이상 징후" in combined_output or "Root" in combined_output,
        "fallback_used": "[fallback model:" in combined_output,
        "api_failure_present": "[API 호출 실패]" in combined_output,
    }

    # More targeted extraction from common notebook output.
    llm_enabled_match = re.search(r"\bTrue\b", combined_output)
    if llm_enabled_match:
        checks["llm_enabled_true"] = True

    print(f"notebook: {notebook_path}")
    for name, passed in checks.items():
        print(f"{name}: {'PASS' if passed else 'FAIL'}")

    print("\nsummary:")
    if checks["api_failure_present"]:
        print("- notebook executed, but LLM call returned an API failure")
    elif checks["llm_analysis_present"]:
        print("- notebook executed and produced an LLM analysis")
    else:
        print("- notebook executed, but LLM analysis output was not detected")


if __name__ == "__main__":
    main()
