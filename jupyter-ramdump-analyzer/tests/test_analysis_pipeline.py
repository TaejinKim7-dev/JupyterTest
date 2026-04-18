import os
import sys
import unittest
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from analysis_pipeline import FeasibilityOptions, format_feasibility_summary, run_feasibility_analysis
from llm_assistant import LLMAssistant
import memory_analyzer
import memory_kernel_analyzer
from memory_kernel_analyzer import build_analysis_context, summarize_findings
import run_llm_feasibility
class AnalysisPipelineTests(unittest.TestCase):
    def setUp(self):
        self.dump_path = str((ROOT.parent / "data" / "memory" / "memory.vmem").resolve())
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
        with mock.patch.dict(os.environ, {}, clear=True):
            assistant = LLMAssistant(api_key="")
            self.assertFalse(assistant.is_configured())
            result = assistant.ask("ping")
        self.assertIn("OPENAI_API_KEY", result)

    def test_memory_analyzer_parse_args(self):
        with mock.patch.object(sys, "argv", ["memory_analyzer.py", "/tmp/dump.bin", "--vmlinux", "/tmp/vmlinux"]):
            args = memory_analyzer.parse_args()
        self.assertEqual(args.dump_path, "/tmp/dump.bin")
        self.assertEqual(args.vmlinux_path, "/tmp/vmlinux")

    def test_memory_kernel_analyzer_parse_args(self):
        with mock.patch.object(sys, "argv", ["memory_kernel_analyzer.py", "/tmp/dump.bin", "--vmlinux", "/tmp/vmlinux"]):
            args = memory_kernel_analyzer.parse_args()
        self.assertEqual(args.dump_path, "/tmp/dump.bin")
        self.assertEqual(args.vmlinux_path, "/tmp/vmlinux")

    def test_run_llm_feasibility_parse_args(self):
        with mock.patch.object(sys, "argv", ["run_llm_feasibility.py", "/tmp/dump.bin", "--vmlinux", "/tmp/vmlinux", "--next-steps"]):
            args = run_llm_feasibility.parse_args()
        self.assertEqual(args.dump_path, "/tmp/dump.bin")
        self.assertEqual(args.vmlinux_path, "/tmp/vmlinux")
        self.assertTrue(args.next_steps)


if __name__ == "__main__":
    unittest.main()
