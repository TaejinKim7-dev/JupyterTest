# AGENTS.md

## Project Overview

This is a JupyterLab + LLM-based kernel debugging analysis system for Android/Linux memory dumps (ramdump/vmlinux).

## Key Commands

```bash
# Run basic memory analysis
python src/memory_analyzer.py

# Run kernel-focused analysis
python src/memory_kernel_analyzer.py

# Start JupyterLab
jupyter lab
```

## Project Structure

```
jupyter-ramdump-analyzer/
├── src/                    # Python source
│   ├── llm_assistant.py    # LLM helper class
│   ├── ramdump_loader.py   # Ramdump loader
│   ├── memory_analyzer.py  # Basic memory analysis
│   └── memory_kernel_analyzer.py  # Kernel analysis
├── notebooks/              # Jupyter notebooks
├── memory/                 # Test data (memory.vmem)
└── docs/                   # Design documents
```

## Environment

- Python packages: `jupyterlab`, `openai`, `langchain`, `langchain-core`, `ipython`, `volatility3`
- API key: Set via `OPENAI_API_KEY` environment variable

## Test Data

`data/memory/memory.vmem` (4GB Linux memory dump) is used for validation. It contains:
- Kernel: Linux 6.5.0-41-generic
- Kernel panic detected
- 36 users, 1400+ IP addresses
