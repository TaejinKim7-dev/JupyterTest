#!/usr/bin/env python3
"""
Check a Jupyter notebook file for cell execution errors.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def parse_args():
    parser = argparse.ArgumentParser(description="Check a notebook for execution errors")
    parser.add_argument("notebook_path", help="Path to the executed notebook file")
    return parser.parse_args()


def main():
    args = parse_args()
    notebook_path = Path(args.notebook_path)
    if not notebook_path.exists():
        raise FileNotFoundError(f"notebook not found: {notebook_path}")

    notebook = json.loads(notebook_path.read_text())
    errors = []
    output_cell_count = 0

    for index, cell in enumerate(notebook.get("cells", [])):
        outputs = cell.get("outputs", [])
        if outputs:
            output_cell_count += 1
        for output in outputs:
            if output.get("output_type") == "error":
                errors.append(
                    {
                        "cell_index": index,
                        "ename": output.get("ename"),
                        "evalue": output.get("evalue"),
                    }
                )

    print(f"notebook: {notebook_path}")
    print(f"cells_with_output: {output_cell_count}")
    if errors:
        print("errors:")
        for item in errors:
            print(f"- cell {item['cell_index']}: {item['ename']} - {item['evalue']}")
    else:
        print("NO_ERRORS")


if __name__ == "__main__":
    main()
