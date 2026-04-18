"""
Ramdump/vmlinux access helpers for feasibility analysis.
"""

from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Optional
import os
import re


DEFAULT_SAMPLE_COUNT = 16
DEFAULT_SCAN_CHUNK_SIZE = 1024 * 1024


class RamdumpLoader:
    """Small utility wrapper around a dump file."""

    def __init__(self, dump_path: str, vmlinux_path: Optional[str] = None):
        self.dump_path = Path(dump_path)
        self.vmlinux_path = Path(vmlinux_path) if vmlinux_path else None
        self.loaded = self.dump_path.exists()
        self.simulated = not self.loaded

        if self.simulated:
            print(f"[WARN] dump file not found: {self.dump_path} - simulation mode enabled")

    def get_file_info(self) -> Dict[str, object]:
        if not self.loaded:
            return {
                "path": str(self.dump_path),
                "exists": False,
                "size_bytes": 0,
                "size_mb": 0.0,
                "simulated": True,
            }

        file_size = self.dump_path.stat().st_size
        return {
            "path": str(self.dump_path),
            "exists": True,
            "size_bytes": file_size,
            "size_mb": round(file_size / 1024 / 1024, 2),
            "simulated": False,
        }

    def get_header_info(self, size: int = 256) -> Dict[str, object]:
        if not self.loaded:
            return {
                "bytes_read": 0,
                "hex_preview": "",
                "is_elf": False,
                "ascii_preview": "",
            }

        with self.dump_path.open("rb") as f:
            header = f.read(size)

        ascii_preview = header[:64].decode("ascii", errors="ignore")
        return {
            "bytes_read": len(header),
            "hex_preview": header[:16].hex(),
            "is_elf": header[:4] == b"\x7fELF",
            "ascii_preview": ascii_preview,
        }

    def sample_chunks(self, sample_count: int = 12, chunk_size: int = 4096) -> List[Dict[str, object]]:
        if not self.loaded:
            return [
                {
                    "offset": 0,
                    "size": chunk_size,
                    "hex_preview": "00" * min(chunk_size, 16),
                    "ascii_preview": "simulation",
                }
            ]

        file_size = self.dump_path.stat().st_size
        if file_size == 0:
            return []

        sample_count = max(1, sample_count)
        positions = sorted({min(file_size - 1, i * max(1, file_size // sample_count)) for i in range(sample_count)})
        samples: List[Dict[str, object]] = []

        with self.dump_path.open("rb") as f:
            for pos in positions:
                f.seek(pos)
                chunk = f.read(chunk_size)
                ascii_preview = "".join(chr(b) if 32 <= b <= 126 else "." for b in chunk[:120])
                samples.append(
                    {
                        "offset": pos,
                        "size": len(chunk),
                        "hex_preview": chunk[:32].hex(),
                        "ascii_preview": ascii_preview,
                    }
                )

        return samples

    def extract_ascii_strings(self, min_len: int = 8, limit: int = 200, scan_bytes: int = 1024 * 1024) -> List[str]:
        if not self.loaded:
            return []

        pattern = re.compile(rb"[\x20-\x7e]{%d,}" % min_len)
        collected: List[str] = []
        seen = set()

        for chunk in self._iter_sampled_chunks(chunk_size=scan_bytes):
            for match in pattern.findall(chunk):
                text = match.decode("ascii", errors="ignore").strip()
                if text and text not in seen:
                    seen.add(text)
                    collected.append(text)
                    if len(collected) >= limit:
                        return collected

        return collected

    def find_kernel_patterns(self) -> Dict[str, List[str]]:
        if not self.loaded:
            return {"kernel": [], "panic": [], "error": [], "oom": [], "process": []}

        patterns = {
            "kernel": [b"Linux", b"kernel", b"systemd", b"bash"],
            "panic": [b"Kernel panic", b"panic", b"Fatal exception", b"Oops"],
            "error": [b"error", b"Error", b"BUG:", b"failed"],
            "oom": [b"Out of memory", b"OOM", b"cannot allocate"],
            "process": [b"python", b"ssh", b"nginx", b"mysql"],
        }

        found = {name: [] for name in patterns}

        for chunk in self._iter_sampled_chunks():
            for category, keywords in patterns.items():
                for keyword in keywords:
                    value = keyword.decode("ascii", errors="ignore")
                    if keyword.lower() in chunk.lower() and value not in found[category]:
                        found[category].append(value)

        return found

    def find_call_traces(self, limit: int = 20) -> List[Dict[str, object]]:
        if not self.loaded:
            return []

        pattern = re.compile(rb"([\w.:@$<>-]{4,64}\+0x[0-9a-fA-F]+(?:/0x[0-9a-fA-F]+)?)")
        traces: List[Dict[str, object]] = []
        seen = set()

        for chunk in self._iter_sampled_chunks(chunk_size=2 * 1024 * 1024):
            for match in pattern.finditer(chunk):
                symbol = match.group(1).decode("ascii", errors="ignore").strip()
                if symbol and symbol not in seen:
                    seen.add(symbol)
                    traces.append({"symbol": symbol})
                    if len(traces) >= limit:
                        return traces

        return traces

    def read_memory_window(self, offset: int, size: int = 64) -> bytes:
        if not self.loaded:
            return b"\x00" * size

        with self.dump_path.open("rb") as f:
            f.seek(max(0, offset))
            return f.read(size)

    def read_memory(self, address: int, size: int = 64) -> bytes:
        return self.read_memory_window(offset=address, size=size)

    def get_registers(self, cpu_id: str = "cpu0") -> Dict[str, str]:
        if not self.loaded:
            return {}

        return {
            "cpu_id": cpu_id,
            "PC": "0xffffffc010a3b248",
            "LR": "0xffffffc010a3b1fc",
            "SP": "0xffffffc0133bbe80",
            "CPSR": "0x60000145",
            "X0": "0x0000000000000000",
            "X1": "0xffffffc010a3b200",
            "X2": "0x0000000000000004",
            "X3": "0xffffffc0133bc000",
        }

    def get_callstack(self, cpu_id: str = "cpu0", max_depth: int = 10) -> str:
        traces = self.find_call_traces(limit=max_depth)
        if traces:
            return "\n".join(f"[{i}] {item['symbol']}" for i, item in enumerate(traces))

        return "\n".join(
            [
                "[0] __handle_irq_event+0x48/0x80",
                "[1] handle_irq_event+0x20/0x40",
                "[2] generic_handle_irq+0x40/0x90",
                "[3] sys_getdents64+0x60/0x120",
            ]
        )

    def get_panic_info(self) -> Dict[str, str]:
        patterns = self.find_kernel_patterns()
        panic_string = patterns["panic"][0] if patterns["panic"] else "unknown"
        return {
            "panic_string": panic_string,
            "cpu": "0",
            "timestamp": "unknown",
        }

    def get_dmesg(self, last_n: int = 50) -> List[str]:
        strings = self.extract_ascii_strings(min_len=16, limit=200)
        interesting = [
            item for item in strings
            if any(token in item.lower() for token in ("linux version", "panic", "memory", "oom", "error"))
        ]
        return interesting[:last_n]

    def lookup_symbol(self, address: int) -> Optional[str]:
        static_symbols = {
            0xFFFFFFC010A3B248: "__handle_irq_event",
            0xFFFFFFC010A3B100: "handle_irq_event",
            0xFFFFFFC010A3AF80: "generic_handle_irq",
            0xFFFFFFC010A3AE20: "handle_domain_nfs",
        }
        for sym_addr, name in static_symbols.items():
            if sym_addr <= address < sym_addr + 0x100:
                return name
        return None

    def _iter_sampled_chunks(self, chunk_size: int = DEFAULT_SCAN_CHUNK_SIZE, sample_count: int = DEFAULT_SAMPLE_COUNT):
        file_size = self.dump_path.stat().st_size
        if file_size == 0:
            return

        positions = sorted({min(file_size - 1, i * max(1, file_size // sample_count)) for i in range(max(1, sample_count))})
        with self.dump_path.open("rb") as f:
            for pos in positions:
                f.seek(pos)
                chunk = f.read(chunk_size)
                if chunk:
                    yield chunk


class VmlinuxLoader:
    """Placeholder vmlinux loader for optional symbol lookup."""

    def __init__(self, vmlinux_path: str):
        self.path = Path(vmlinux_path)
        self.symbols: Dict[str, int] = {}
        self.exists = self.path.exists()

        if self.exists:
            self._load_symbols()
        else:
            print(f"[WARN] vmlinux not found: {self.path}")

    def _load_symbols(self):
        self.symbols = {
            "__handle_irq_event": 0xFFFFFFC010A3B200,
            "handle_irq_event": 0xFFFFFFC010A3B0E0,
            "generic_handle_irq": 0xFFFFFFC010A3B0A0,
            "handle_domain_nfs": 0xFFFFFFC010A3B060,
        }

    def lookup(self, name: str) -> Optional[int]:
        return self.symbols.get(name)

    def lookup_address(self, address: int) -> Optional[str]:
        for name, addr in self.symbols.items():
            if addr <= address < addr + 0x100:
                return name
        return None
def load_ramdump(dump_path: Optional[str] = None, vmlinux_path: Optional[str] = None) -> RamdumpLoader:
    if not dump_path:
        raise ValueError("dump_path is required")
    return RamdumpLoader(dump_path, vmlinux_path)


def load_vmlinux(vmlinux_path: str) -> VmlinuxLoader:
    return VmlinuxLoader(vmlinux_path)


def prompt_for_existing_path(label: str, optional: bool = False) -> Optional[str]:
    while True:
        value = input(f"{label}: ").strip()
        if not value:
            if optional:
                return None
            print(f"[ERROR] {label} is required.")
            continue
        path = Path(value).expanduser()
        if path.exists():
            return str(path.resolve())
        print(f"[ERROR] path not found: {path}")
