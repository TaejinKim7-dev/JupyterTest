# Jupyter + LLM Kernel Dump Feasibility Analyzer

JupyterLab 환경에서 공개 LLM API와 로컬 memory dump 분석 코드를 연결해 Android/Linux 커널 디버깅 feasibility를 확인하는 프로젝트입니다.

## Current scope

- 사용자가 지정한 memory dump를 입력으로 사용하는 dump-only 분석
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
# venv 생성 및 활성화 (최초 1회)
python -m venv ~/jupyter-ai-env
source ~/jupyter-ai-env/bin/activate

# 의존성 설치 (전체: Jupyter AI + Jupyternaut + LiteLLM 포함)
pip install -r requirements-jupyter-ai.txt

# 또는 기본 패키지만
pip install -r requirements.txt
```

OpenRouter API 키 발급: https://openrouter.ai/keys

## Quick start

```bash
# API 키 설정 (최초 1회)
cp configs/jupyter_ai_openrouter.env.example configs/jupyter_ai_openrouter.env
# configs/jupyter_ai_openrouter.env 열어서 OPENROUTER_API_KEY 입력

# JupyterLab 시작 (venv 활성화 + 환경변수 설정 자동화)
./scripts/start_jupyter.sh
```

메모리 덤프 분석 스크립트:

```bash
source ~/jupyter-ai-env/bin/activate
python src/memory_analyzer.py /path/to/memory.vmem
python src/memory_kernel_analyzer.py /path/to/memory.vmem
python src/run_llm_feasibility.py /path/to/memory.vmem
```

## Testing

### 1. LLM API 연결 테스트

```bash
source ~/jupyter-ai-env/bin/activate
python src/test_llm_api.py
```

정상 응답이 오면 OpenRouter 연결 확인 완료입니다.

### 2. JupyterLab Chat UI 테스트 (Jupyternaut → OpenRouter)

```
./scripts/start_jupyter.sh
```

1. `File > New > Chat` 열기
2. 채팅창에 입력: `@Jupyternaut 어떤 모델로 응답하고 있는지 알려줘`
3. 기대 응답: `openrouter/nvidia/nemotron-3-super-120b-a12b` 모델 언급

> 자세한 설정 방법: [docs/jupyter_ai_jupyternaut_openrouter_summary.md](../docs/jupyter_ai_jupyternaut_openrouter_summary.md)

### 3. `%%ai` 매직 테스트 (노트북 셀)

```python
%load_ext jupyter_ai_magics
%%ai nemo           # alias (ipython_config.py에서 설정됨)
간단한 파이썬 예제 만들어줘
```

`nemo` alias 없이 전체 ID: `%%ai openai-chat-custom:nvidia/nemotron-3-super-120b-a12b`

> 자세한 사용법: [docs/jupyter_ai_magic_setup.md](docs/jupyter_ai_magic_setup.md)  
> 전체 데모: [notebooks/jupyter_ai_magic_demo.ipynb](notebooks/jupyter_ai_magic_demo.ipynb)

### 4. 노트북 기반 로그 분석 테스트

`notebooks/interactive_log_analyzer.ipynb` 열고 셀 순서대로 실행합니다.  
`/home/taejin/Jupyter/data/memory/` 경로의 vmem 파일이 분석 대상입니다.  
Step 3에서 `%%ai nemo` 셀과 `LLMAssistant` 셀 두 방식을 선택해 사용할 수 있습니다.

### LLM 호출 경로 비교

| 항목 | Chat UI (`@Jupyternaut`) | `%%ai` 매직 |
|------|--------------------------|-------------|
| 모델 ID 형식 | `openrouter/<model>` | `openai-chat-custom:<model>` 또는 alias |
| 환경변수 | `OPENROUTER_API_KEY` | `OPENAI_API_KEY` + `OPENAI_API_BASE` |
| 출력 위치 | Chat 사이드패널 | 노트북 셀 출력 |
| 변수 주입 | `@file:`, `@active-cell` | `{python_var}` |

### 트러블슈팅

| 증상 | 원인 | 해결 |
|------|------|------|
| `LLM Provider NOT provided` (매직) | `openai-chat:` 사용 | `openai-chat-custom:`으로 변경 |
| `LLM Provider NOT provided` (Chat UI) | config.json 구버전 형식 | `~/.local/share/jupyter/jupyter_ai/config.json`에서 `openrouter/<model>` 형식으로 수정 |
| `401 / 403` | API 키 미설정 | `./scripts/start_jupyter.sh`로 재시작 |
| `pip check` 경고 | langchain 버전 충돌 | 동작에 지장 없음 (확인됨 2026-05-16) |
| Jupyternaut가 목록에 없음 | 미설치 | `pip install "jupyter-ai[jupyternaut]==3.0.0" litellm` 후 JupyterLab 재시작 |

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

- model: `nvidia/nemotron-3-super-120b-a12b:free`
- base URL: `https://openrouter.ai/api/v1`
- fallback model: `poolside/laguna-m.1:free`

주의:

- free 모델은 지연이 있을 수 있으므로 기본 흐름은 `LLM 분석 1회`로 두고, 추가 계획 생성은 선택적으로 켜는 것이 좋습니다.
- 기본 모델 upstream이 비어 있으면 `poolside/laguna-m.1:free`로 한 번 더 재시도합니다.
- OpenRouter free tier 가용 모델은 수시로 변경되므로 응답 없을 경우 `configs/jupyter_ai_openrouter.env`에서 모델 교체 후 재시도합니다.

## Known limitations

- 현재는 구조체 단위 메모리 해석이나 진짜 심볼 resolution을 하지 않습니다.
- `vmlinux`가 없으므로 문자열/패턴/trace 후보 중심의 feasibility 분석입니다.
- LLM 결과는 참고용이며, root cause 확정은 아닙니다.
