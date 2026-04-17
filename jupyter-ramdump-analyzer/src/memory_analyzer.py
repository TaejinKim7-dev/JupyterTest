#!/usr/bin/env python3
"""
Basic memory dump analyzer for notebook/CLI smoke testing.
"""

from __future__ import annotations

from ramdump_loader import load_ramdump, resolve_default_dump_path


def main():
    loader = load_ramdump(resolve_default_dump_path())
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
