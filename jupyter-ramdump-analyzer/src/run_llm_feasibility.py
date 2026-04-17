#!/usr/bin/env python3
"""
Run the full dump -> findings -> LLM feasibility path.
"""

from __future__ import annotations

from analysis_pipeline import FeasibilityOptions, format_feasibility_summary, run_feasibility_analysis
from llm_assistant import LLMAssistant
from ramdump_loader import resolve_default_dump_path


def main():
    dump_path = resolve_default_dump_path()
    assistant = LLMAssistant()
    report = run_feasibility_analysis(
        dump_path=dump_path,
        llm_assistant=assistant,
        options=FeasibilityOptions(
            dump_path=dump_path,
            allow_raw_chunk_excerpt=True,
            raw_chunk_limit=2,
        ),
    )
    print(format_feasibility_summary(report))


if __name__ == "__main__":
    main()
