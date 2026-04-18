#!/usr/bin/env python3
"""
Basic memory dump analyzer for notebook/CLI smoke testing.
"""

from __future__ import annotations

import argparse

from ramdump_loader import load_ramdump, prompt_for_existing_path


def parse_args():
    parser = argparse.ArgumentParser(description="Basic memory dump analyzer")
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
    return parser.parse_args()


def main():
    args = parse_args()
    dump_path = args.dump_path or prompt_for_existing_path("dump_path")
    vmlinux_path = args.vmlinux_path
    if vmlinux_path and not vmlinux_path.strip():
        vmlinux_path = None
    loader = load_ramdump(dump_path, vmlinux_path=vmlinux_path)
    file_info = loader.get_file_info()
    header_info = loader.get_header_info()
    patterns = loader.find_kernel_patterns()
    strings = loader.extract_ascii_strings(limit=20)
    samples = loader.sample_chunks(sample_count=6, chunk_size=512)

    print("=" * 60)
    print("Memory Dump Basic Analyzer")
    print("=" * 60)
    print(f"file: {file_info['path']}")
    print(f"size_mb: {file_info['size_mb']}")
    print(f"is_elf: {header_info['is_elf']}")
    print(f"header_hex: {header_info['hex_preview']}")
    print(f"vmlinux: {vmlinux_path or '(not provided)'}")

    print("\n[keywords]")
    for category, values in patterns.items():
        if values:
            print(f"- {category}: {', '.join(values[:10])}")

    print("\n[strings]")
    for item in strings[:10]:
        print(f"- {item[:120]}")

    print("\n[samples]")
    for sample in samples[:3]:
        print(f"- offset={sample['offset']} ascii={sample['ascii_preview'][:80]}")

    print("\nanalysis complete")


if __name__ == "__main__":
    main()
