#!/usr/bin/env bash
set -euo pipefail

ROOT="${1:-/home/taejin/Jupyter/data/aosp-lab/out}"

find "$ROOT" -type f -name vmlinux | sort
