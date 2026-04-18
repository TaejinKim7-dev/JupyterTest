# Jupyter + LLM Kernel Dump Feasibility Analyzer

JupyterLab 환경에서 공개 LLM API와 로컬 memory dump 분석 코드를 연결해 Android/Linux 커널 디버깅 feasibility를 확인하는 프로젝트입니다.

## Current scope

- `data/memory/memory.vmem`를 실제 입력으로 사용하는 dump-only 분석
- OpenAI-compatible LLM API 연동
- Notebook-first 데모와 재현 가능한 Python 파이프라인
- `vmlinux` 없이도 동작하는 기본 뼈대

## Project structure

```text
jupyter-ramdump-analyzer/
├── README.md
├── docs/
├── notebooks/
│   └── pilot_test_notebook.ipynb
├── src/
│   ├── analysis_pipeline.py
│   ├── llm_assistant.py
│   ├── memory_analyzer.py
│   ├── memory_kernel_analyzer.py
│   └── ramdump_loader.py
└── tests/
```

## Requirements

```bash
pip install jupyterlab requests ipython volatility3
```

환경 변수:

```bash
export OPENAI_API_KEY="sk-..."
export OPENAI_API_BASE="https://api.openai.com/v1"  # optional
```

## Quick start

기본 smoke test:

```bash
python src/memory_analyzer.py
python src/memory_kernel_analyzer.py
python src/run_llm_feasibility.py
python -m unittest discover -s tests
```

Jupyter demo:

```bash
jupyter lab
```

그 다음 [notebooks/pilot_test_notebook.ipynb](/home/taejin/Jupyter/jupyter-ramdump-analyzer/notebooks/pilot_test_notebook.ipynb)를 실행합니다.

## Sample data source

- 공개된 Linux 메모리 덤프 샘플은 13Cubed의 Ubuntu 22.04 메모리 포렌식 챌린지 자료를 사용했습니다.
- 다운로드: https://cdn.13cubed.com/downloads/linux_challenge.zip

## What the pipeline does

1. dump 파일 메타데이터와 헤더를 확인합니다.
2. panic/oops/error/network/process 관련 신호를 로컬에서 추출합니다.
3. 추출 결과를 `AnalysisContext`와 summary dict로 구조화합니다.
4. 선택적으로 샘플 chunk 일부를 포함해 공개 LLM API로 분석을 요청합니다.
5. root cause 후보와 다음 단계 조사 계획을 notebook에서 확인합니다.

기본 LLM 설정:

- model: `openai/gpt-oss-120b:free`
- base URL: `https://openrouter.ai/api/v1`

주의:

- free 모델은 지연이 있을 수 있으므로 기본 흐름은 `LLM 분석 1회`로 두고, 추가 계획 생성은 선택적으로 켜는 것이 좋습니다.

## Known limitations

- 현재는 구조체 단위 메모리 해석이나 진짜 심볼 resolution을 하지 않습니다.
- `vmlinux`가 없으므로 문자열/패턴/trace 후보 중심의 feasibility 분석입니다.
- LLM 결과는 참고용이며, root cause 확정은 아닙니다.
