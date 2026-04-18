#!/usr/bin/env python3
"""
Run the full dump -> findings -> LLM feasibility path.
"""

from __future__ import annotations

import argparse

from analysis_pipeline import FeasibilityOptions, format_feasibility_summary, run_feasibility_analysis
from llm_assistant import LLMAssistant
from ramdump_loader import prompt_for_existing_path


def parse_args():
    parser = argparse.ArgumentParser(description="Run the full dump -> findings -> LLM feasibility path")
    parser.add_argument(
        "dump_path",
        nargs="?",
        help="Path to the memory dump file",
    )
    parser.add_argument(
        "--vmlinux",
        dest="vmlinux_path",
        default=None,
        help="Optional path to a vmlinux symbol file",
    )
    parser.add_argument(
        "--next-steps",
        action="store_true",
        help="Also request a follow-up investigation plan from the LLM",
    )
    return parser.parse_args()


def main():
    args = parse_args()
    dump_path = args.dump_path or prompt_for_existing_path("dump_path")
    assistant = LLMAssistant()
    report = run_feasibility_analysis(
        dump_path=dump_path,
        llm_assistant=assistant,
        options=FeasibilityOptions(
            dump_path=dump_path,
            allow_raw_chunk_excerpt=True,
            raw_chunk_limit=2,
            generate_next_steps=args.next_steps,
        ),
    )
    if args.vmlinux_path:
        print(f"vmlinux: {args.vmlinux_path}")
    print(format_feasibility_summary(report))


if __name__ == "__main__":
    main()
