#!/usr/bin/env python3
"""
Kernel-focused feasibility analysis for a memory dump.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Dict, List, Tuple
import os
import re

from ramdump_loader import resolve_default_dump_path


DEFAULT_DUMP_FILE = resolve_default_dump_path()
DEFAULT_SAMPLE_COUNT = 12
DEFAULT_SCAN_CHUNK_SIZE = 2 * 1024 * 1024


def _iter_chunks(
    dump_path: str,
    chunk_size: int = DEFAULT_SCAN_CHUNK_SIZE,
    overlap: int = 256,
    sample_count: int = DEFAULT_SAMPLE_COUNT,
):
    file_size = os.path.getsize(dump_path)
    if file_size == 0:
        return

    positions = sorted(
        {
            min(file_size - 1, i * max(1, file_size // sample_count))
            for i in range(max(1, sample_count))
        }
    )
    with open(dump_path, "rb") as f:
        for pos in positions:
            read_start = max(0, pos - overlap)
            f.seek(read_start)
            chunk = f.read(chunk_size + overlap * 2)
            if not chunk:
                continue
            yield read_start, chunk


@dataclass
class AnalysisContext:
    file_info: Dict[str, object]
    header_info: Dict[str, object]
    kernel_patterns: Dict[str, List[str]]
    panic_signals: Dict[str, List[Dict[str, str]]]
    call_traces: List[Dict[str, object]]
    interesting_strings: List[str]
    network_indicators: Dict[str, List[object]]
    process_indicators: Dict[str, List[str]]
    raw_chunk_samples: List[Dict[str, object]]
    limitations: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, object]:
        return asdict(self)


def scan_for_crashes(dump_path: str) -> Dict[str, List[Dict[str, str]]]:
    patterns = {
        "kernel_panic": [b"Kernel panic", b"panic - not syncing", b"Fatal exception"],
        "kernel_oops": [b"Kernel Oops", b"BUG:", b"Oops:"],
        "memory_errors": [b"Out of memory", b"OOM killer", b"kmem_cache_alloc", b"ENOMEM"],
        "crashes": [b"crash", b"segfault", b"SIGSEGV", b"SIGBUS", b"double fault"],
        "hardware": [b"hardware error", b"machine check", b"thermal", b"CPUdead"],
    }
    found = {name: [] for name in patterns}
    seen = {name: set() for name in patterns}

    for _, chunk in _iter_chunks(dump_path):
        for category, pattern_list in patterns.items():
            for pattern in pattern_list:
                pattern_str = pattern.decode("ascii", errors="ignore")
                if pattern_str in seen[category]:
                    continue
                idx = chunk.find(pattern)
                if idx == -1:
                    continue
                context = chunk[max(0, idx - 100): idx + 150].replace(b"\x00", b" ")
                clean = context.decode("utf-8", errors="ignore").strip()
                if not clean:
                    continue
                found[category].append({"pattern": pattern_str, "context": clean[:200]})
                seen[category].add(pattern_str)

    return found


def find_call_traces(dump_path: str, limit: int = 20) -> List[Dict[str, object]]:
    addr_trace = re.compile(rb"\[<([0-9a-fA-F]{8,16})>\]\s+([\w.:@$<>-]+\+0x[0-9a-fA-F]+/0x[0-9a-fA-F]+)")
    plain_trace = re.compile(rb"\b([\w.:@$<>-]{4,64}\+0x[0-9a-fA-F]+/0x[0-9a-fA-F]+)")
    call_trace_header = re.compile(rb"Call Trace:", re.IGNORECASE)
    traces: Dict[str, Dict[str, object]] = {}

    for _, chunk in _iter_chunks(dump_path):
        for match in addr_trace.finditer(chunk):
            addr = match.group(1).decode("ascii", errors="ignore")
            symbol = match.group(2).decode("ascii", errors="ignore").strip()
            entry = traces.setdefault(symbol, {"symbol": symbol, "addr": addr, "count": 0})
            entry["count"] += 1

        if call_trace_header.search(chunk):
            for match in plain_trace.finditer(chunk):
                symbol = match.group(1).decode("ascii", errors="ignore").strip()
                entry = traces.setdefault(symbol, {"symbol": symbol, "addr": "?", "count": 0})
                entry["count"] += 1

    return sorted(traces.values(), key=lambda item: (-int(item["count"]), item["symbol"]))[:limit]


def find_process_info(dump_path: str) -> Dict[str, List[str]]:
    proc_pattern = re.compile(rb"/[\w/]+/([\w][\w.-]{1,63})")
    user_pattern = re.compile(rb"/(home|root)/([\w][\w.-]{0,31})")
    skip_names = frozenset(("bin", "usr", "lib", "lib64", "dev", "proc", "sys", "var", "etc", "tmp", "home"))
    processes = set()
    usernames = set()

    for _, chunk in _iter_chunks(dump_path):
        for match in proc_pattern.finditer(chunk):
            name = match.group(1).decode("ascii", errors="ignore")
            if name and name not in skip_names and name.isprintable():
                processes.add(name)
        for match in user_pattern.finditer(chunk):
            name = match.group(2).decode("ascii", errors="ignore")
            if name and name not in skip_names and name.isprintable():
                usernames.add(name)

    return {"processes": sorted(processes)[:50], "users": sorted(usernames)[:50]}


def find_kernel_info(dump_path: str) -> Dict[str, List[str]]:
    version_pattern = re.compile(rb"Linux version [\d]+\.[\d]+\.[\d]+[\w.\-+]*(?:\s+\([^)]*\))?")
    mount_pattern = re.compile(rb"/dev/[\w]+ on /[\w/]* type ([\w]+)")
    versions = set()
    mounts = set()

    for _, chunk in _iter_chunks(dump_path):
        for match in version_pattern.finditer(chunk):
            versions.add(match.group(0).decode("ascii", errors="ignore"))
        for match in mount_pattern.finditer(chunk):
            mounts.add(match.group(1).decode("ascii", errors="ignore"))

    return {"versions": sorted(versions)[:10], "filesystems": sorted(mounts)[:20]}


def find_network_info(dump_path: str) -> Dict[str, List[object]]:
    ip_pattern = re.compile(rb"\b(?:\d{1,3}\.){3}\d{1,3}\b")
    port_pattern = re.compile(rb":(\d{2,5})\b")
    ips = set()
    ports = set()

    for _, chunk in _iter_chunks(dump_path):
        for match in ip_pattern.finditer(chunk):
            ip = match.group(0).decode("ascii", errors="ignore")
            parts = ip.split(".")
            if all(part.isdigit() and 0 <= int(part) <= 255 for part in parts):
                if not ip.startswith(("0.", "255.", "127.", "169.254.")):
                    ips.add(ip)
        for match in port_pattern.finditer(chunk):
            port = int(match.group(1).decode("ascii", errors="ignore"))
            if 1 <= port <= 65535:
                ports.add(port)

    internal_ips = sorted(ip for ip in ips if ip.startswith(("10.", "192.168.", "172.")))
    external_ips = sorted(ip for ip in ips if ip not in internal_ips and not ip.startswith(("127.", "169.254.")))
    common_ports = {20: "FTP-data", 21: "FTP", 22: "SSH", 23: "Telnet", 25: "SMTP", 53: "DNS", 80: "HTTP", 110: "POP3", 143: "IMAP", 443: "HTTPS", 3306: "MySQL", 5432: "PostgreSQL", 6379: "Redis", 27017: "MongoDB"}
    interesting_ports = [f"{port} ({common_ports[port]})" for port in sorted(ports) if port in common_ports]

    return {
        "internal_ips": internal_ips[:50],
        "external_ips": external_ips[:50],
        "interesting_ports": interesting_ports,
    }


def extract_interesting_strings(dump_path: str, limit: int = 80) -> List[str]:
    pattern = re.compile(rb"[\x20-\x7e]{8,}")
    interesting = []
    seen = set()
    keywords = ("panic", "linux version", "memory", "alloc", "tcp", "udp", "ssh", "http", "ext4", "nfs")

    for _, chunk in _iter_chunks(dump_path, chunk_size=1024 * 1024):
        for match in pattern.findall(chunk):
            text = match.decode("ascii", errors="ignore").strip()
            if text and text not in seen and any(token in text.lower() for token in keywords):
                seen.add(text)
                interesting.append(text[:160])
                if len(interesting) >= limit:
                    return interesting

    return interesting


def sample_chunks(dump_path: str, sample_count: int = 8, chunk_size: int = 256) -> List[Dict[str, object]]:
    file_size = os.path.getsize(dump_path)
    if file_size == 0:
        return []

    positions = sorted({min(file_size - 1, i * max(1, file_size // sample_count)) for i in range(sample_count)})
    samples = []

    with open(dump_path, "rb") as f:
        for pos in positions:
            f.seek(pos)
            chunk = f.read(chunk_size)
            ascii_preview = "".join(chr(byte) if 32 <= byte <= 126 else "." for byte in chunk[:120])
            samples.append(
                {
                    "offset": pos,
                    "size": len(chunk),
                    "hex_preview": chunk[:32].hex(),
                    "ascii_preview": ascii_preview,
                }
            )

    return samples


def build_analysis_context(dump_path: str = DEFAULT_DUMP_FILE) -> AnalysisContext:
    if not os.path.exists(dump_path):
        raise FileNotFoundError(f"dump file not found: {dump_path}")

    dump_path = str(Path(dump_path).resolve())
    file_size = os.path.getsize(dump_path)
    with open(dump_path, "rb") as f:
        header = f.read(256)

    kernel_info = find_kernel_info(dump_path)
    panic_signals = scan_for_crashes(dump_path)
    limitations = [
        "vmlinux 심볼 파일 없이 dump-only 분석을 수행함",
        "현재 결과는 문자열/패턴 기반 feasibility 분석이며 정밀한 구조체 해석은 하지 않음",
    ]
    if file_size > 1024 * 1024 * 1024:
        limitations.append("대용량 dump는 파일 전역 샘플 chunk를 사용해 빠르게 feasibility만 확인함")

    return AnalysisContext(
        file_info={
            "path": dump_path,
            "size_bytes": file_size,
            "size_mb": round(file_size / 1024 / 1024, 2),
            "size_gb": round(file_size / 1024 / 1024 / 1024, 2),
        },
        header_info={
            "hex_preview": header[:16].hex(),
            "is_elf": header[:4] == b"\x7fELF",
            "ascii_preview": header[:64].decode("ascii", errors="ignore"),
        },
        kernel_patterns={
            **kernel_info,
            "keywords": sorted({item["pattern"] for items in panic_signals.values() for item in items})[:30],
        },
        panic_signals=panic_signals,
        call_traces=find_call_traces(dump_path),
        interesting_strings=extract_interesting_strings(dump_path),
        network_indicators=find_network_info(dump_path),
        process_indicators=find_process_info(dump_path),
        raw_chunk_samples=sample_chunks(dump_path),
        limitations=limitations,
    )


def summarize_findings(context: AnalysisContext) -> Dict[str, object]:
    panic_patterns = []
    for category, items in context.panic_signals.items():
        for item in items:
            panic_patterns.append(f"{category}:{item['pattern']}")

    return {
        "file_info": context.file_info,
        "kernel_versions": context.kernel_patterns.get("versions", []),
        "panic_pattern_count": len(panic_patterns),
        "panic_patterns": panic_patterns[:10],
        "top_call_traces": [item["symbol"] for item in context.call_traces[:10]],
        "interesting_strings_preview": context.interesting_strings[:10],
        "network_summary": {
            "internal_ip_count": len(context.network_indicators.get("internal_ips", [])),
            "external_ip_count": len(context.network_indicators.get("external_ips", [])),
            "interesting_ports": context.network_indicators.get("interesting_ports", []),
        },
        "process_summary": {
            "process_count": len(context.process_indicators.get("processes", [])),
            "user_count": len(context.process_indicators.get("users", [])),
            "users": context.process_indicators.get("users", [])[:10],
        },
        "limitations": context.limitations,
    }


def _print_section(title: str):
    print("\n" + "=" * 60)
    print(title)
    print("=" * 60)


def main():
    dump_path = DEFAULT_DUMP_FILE
    if not os.path.exists(dump_path):
        print(f"[ERROR] 덤프 파일을 찾을 수 없습니다: {dump_path}")
        return

    context = build_analysis_context(dump_path)
    summary = summarize_findings(context)

    _print_section("Memory Dump Deep Analysis")
    print(f"파일: {summary['file_info']['path']}")
    print(f"크기: {summary['file_info']['size_gb']} GB")

    _print_section("Kernel Versions")
    versions = summary["kernel_versions"] or ["(없음)"]
    for item in versions:
        print(f"- {item}")

    _print_section("Panic Signals")
    for item in summary["panic_patterns"] or ["(없음)"]:
        print(f"- {item}")

    _print_section("Top Call Traces")
    for item in summary["top_call_traces"] or ["(없음)"]:
        print(f"- {item}")

    _print_section("Process Summary")
    print(f"processes: {summary['process_summary']['process_count']}")
    print(f"users: {summary['process_summary']['user_count']}")
    for user in summary["process_summary"]["users"]:
        print(f"- {user}")

    _print_section("Network Summary")
    network_summary = summary["network_summary"]
    print(f"internal IPs: {network_summary['internal_ip_count']}")
    print(f"external IPs: {network_summary['external_ip_count']}")
    for port in network_summary["interesting_ports"]:
        print(f"- {port}")

    _print_section("Limitations")
    for item in summary["limitations"]:
        print(f"- {item}")


if __name__ == "__main__":
    main()
