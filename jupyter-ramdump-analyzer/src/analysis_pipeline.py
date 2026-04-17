from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Dict, Optional

from llm_assistant import LLMAssistant
from memory_kernel_analyzer import AnalysisContext, build_analysis_context, summarize_findings


@dataclass
class FeasibilityOptions:
    dump_path: str
    allow_raw_chunk_excerpt: bool = False
    raw_chunk_limit: int = 2
    include_full_context: bool = False
    generate_next_steps: bool = False


@dataclass
class FeasibilityReport:
    context: AnalysisContext
    findings: Dict[str, object]
    llm_analysis: Optional[str]
    next_steps: Optional[str]
    llm_enabled: bool

    def to_dict(self) -> Dict[str, object]:
        return {
            "context": asdict(self.context),
            "findings": self.findings,
            "llm_analysis": self.llm_analysis,
            "next_steps": self.next_steps,
            "llm_enabled": self.llm_enabled,
        }


def format_feasibility_summary(report: FeasibilityReport) -> str:
    findings = report.findings
    lines = [
        "Feasibility Report",
        f"- llm_enabled: {report.llm_enabled}",
        f"- file: {findings['file_info']['path']}",
        f"- kernel_versions: {', '.join(findings.get('kernel_versions', [])[:3]) or '(none)'}",
        f"- panic_pattern_count: {findings.get('panic_pattern_count', 0)}",
        f"- top_call_traces: {', '.join(findings.get('top_call_traces', [])[:5]) or '(none)'}",
        f"- external_ip_count: {findings.get('network_summary', {}).get('external_ip_count', 0)}",
        f"- process_count: {findings.get('process_summary', {}).get('process_count', 0)}",
    ]
    if report.llm_analysis:
        lines.extend(["", "[LLM Analysis]", report.llm_analysis])
    if report.next_steps:
        lines.extend(["", "[Next Steps]", report.next_steps])
    return "\n".join(lines)


def _prepare_findings_for_llm(context: AnalysisContext, allow_raw_chunk_excerpt: bool, raw_chunk_limit: int) -> Dict[str, object]:
    findings = summarize_findings(context)
    if allow_raw_chunk_excerpt:
        findings["raw_chunk_samples"] = context.raw_chunk_samples[:raw_chunk_limit]
    return findings


def run_feasibility_analysis(
    dump_path: str,
    llm_assistant: Optional[LLMAssistant] = None,
    options: Optional[FeasibilityOptions] = None,
) -> FeasibilityReport:
    options = options or FeasibilityOptions(dump_path=dump_path)
    context = build_analysis_context(dump_path=dump_path)
    findings = _prepare_findings_for_llm(
        context,
        allow_raw_chunk_excerpt=options.allow_raw_chunk_excerpt,
        raw_chunk_limit=options.raw_chunk_limit,
    )

    llm_enabled = bool(llm_assistant and llm_assistant.is_configured())
    llm_analysis = None
    next_steps = None

    if llm_enabled and llm_assistant:
        llm_analysis = llm_assistant.analyze_findings(
            findings,
            task="이 memory dump의 핵심 이상 징후와 root cause 후보를 요약해줘.",
        )
        if options.generate_next_steps:
            next_steps = llm_assistant.generate_analysis_plan(findings)

    return FeasibilityReport(
        context=context,
        findings=findings,
        llm_analysis=llm_analysis,
        next_steps=next_steps,
        llm_enabled=llm_enabled,
    )
