import os
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from analysis_pipeline import FeasibilityOptions, format_feasibility_summary, run_feasibility_analysis
from llm_assistant import LLMAssistant
from memory_kernel_analyzer import build_analysis_context, summarize_findings
from ramdump_loader import resolve_default_dump_path


class AnalysisPipelineTests(unittest.TestCase):
    def setUp(self):
        self.dump_path = resolve_default_dump_path()
        self.assertTrue(os.path.exists(self.dump_path), f"missing dump file: {self.dump_path}")

    def test_build_analysis_context_has_expected_shape(self):
        context = build_analysis_context(self.dump_path)
        self.assertTrue(context.file_info["size_bytes"] > 0)
        self.assertIn("hex_preview", context.header_info)
        self.assertIn("versions", context.kernel_patterns)
        self.assertIsInstance(context.call_traces, list)
        self.assertIsInstance(context.limitations, list)

    def test_summarize_findings_contains_counts(self):
        context = build_analysis_context(self.dump_path)
        summary = summarize_findings(context)
        self.assertIn("panic_pattern_count", summary)
        self.assertIn("network_summary", summary)
        self.assertIn("process_summary", summary)

    def test_run_feasibility_analysis_without_llm(self):
        report = run_feasibility_analysis(
            dump_path=self.dump_path,
            llm_assistant=None,
            options=FeasibilityOptions(dump_path=self.dump_path, allow_raw_chunk_excerpt=True),
        )
        self.assertFalse(report.llm_enabled)
        self.assertIsNone(report.llm_analysis)
        self.assertIn("raw_chunk_samples", report.findings)

    def test_format_feasibility_summary(self):
        report = run_feasibility_analysis(
            dump_path=self.dump_path,
            llm_assistant=None,
            options=FeasibilityOptions(dump_path=self.dump_path, allow_raw_chunk_excerpt=False),
        )
        text = format_feasibility_summary(report)
        self.assertIn("Feasibility Report", text)
        self.assertIn("panic_pattern_count", text)

    def test_llm_assistant_reports_missing_api_key(self):
        assistant = LLMAssistant(api_key="")
        self.assertFalse(assistant.is_configured())
        result = assistant.ask("ping")
        self.assertIn("OPENAI_API_KEY", result)


if __name__ == "__main__":
    unittest.main()
