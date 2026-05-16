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

## 초기 설정 (클론 후 최초 1회)

GitHub에서 클론한 직후 아래 4단계를 순서대로 완료해야 테스트가 재현됩니다.

### Step 1. venv 생성 및 패키지 설치

```bash
python -m venv ~/jupyter-ai-env
source ~/jupyter-ai-env/bin/activate
pip install -r requirements-jupyter-ai.txt
```

OpenRouter API 키 발급: https://openrouter.ai/keys

### Step 2. API 키 설정

```bash
cp configs/jupyter_ai_openrouter.env.example configs/jupyter_ai_openrouter.env
```

`configs/jupyter_ai_openrouter.env`를 열어 `OPENROUTER_API_KEY`에 발급받은 키를 입력합니다.

### Step 3. Jupyter 서버 설정 (`~/.jupyter/jupyter_server_config.py`)

아래 내용으로 파일을 생성합니다 (API 키는 Step 2의 키로 교체):

```python
import os

c.AiExtension.initial_language_model = "openrouter/nvidia/nemotron-3-super-120b-a12b"

_key = "여기에_OPENROUTER_API_KEY_입력"
os.environ.setdefault("OPENROUTER_API_KEY", _key)
os.environ.setdefault("OPENAI_API_KEY", _key)
os.environ.setdefault("OPENAI_API_BASE", "https://openrouter.ai/api/v1")

c.ServerApp.open_browser = False
c.ServerApp.root_dir = '/home/taejin/Jupyter/jupyter-ramdump-analyzer'
c.ServerApp.default_url = '/lab/tree/notebooks'
```

### Step 4. Jupyternaut 모델 설정 (`~/.local/share/jupyter/jupyter_ai/config.json`)

```bash
mkdir -p ~/.local/share/jupyter/jupyter_ai
```

아래 내용으로 파일을 생성합니다:

```json
{
    "model_provider_id": "openrouter/nvidia/nemotron-3-super-120b-a12b",
    "embeddings_provider_id": null,
    "completions_model_provider_id": null,
    "api_keys": {},
    "send_with_shift_enter": false,
    "fields": {},
    "embeddings_fields": {},
    "completions_fields": {}
}
```

> **이 파일이 없으면** Chat UI(`@Jupyternaut`)가 구버전 모델 형식을 사용해 `LLM Provider NOT provided` 오류가 발생합니다.

---

## Quick start

```bash
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

노트북 시작 셀에 아래 코드를 실행해 LiteLLM 기반 `%%ai` 매직을 등록합니다:

```python
from IPython.core.magic import register_cell_magic
from litellm import completion
from IPython.display import display, Markdown
import os

@register_cell_magic
def ai(line, cell):
    parts = line.strip().split()
    model = parts[0] if parts else 'openrouter/nvidia/nemotron-3-super-120b-a12b'
    fmt = parts[parts.index('-f') + 1] if '-f' in parts else 'markdown'
    resp = completion(model=model, messages=[{'role': 'user', 'content': cell}],
                      api_key=os.environ.get('OPENROUTER_API_KEY'))
    text = resp.choices[0].message.content
    display(Markdown(text) if fmt in ('markdown', 'md') else text)
```

이후 사용:
```
%%ai openrouter/nvidia/nemotron-3-super-120b-a12b
간단한 파이썬 예제 만들어줘
```

> 전체 데모: [notebooks/jupyter_ai_magic_demo.ipynb](notebooks/jupyter_ai_magic_demo.ipynb)

### 4. 노트북 기반 로그 분석 테스트

`notebooks/interactive_log_analyzer.ipynb` 열고 셀 순서대로 실행합니다.  
`/home/taejin/Jupyter/data/memory/` 경로의 vmem 파일이 분석 대상입니다.  
Step 3에서 `%%ai` 셀(LiteLLM)과 `LLMAssistant` 셀 두 방식을 선택해 사용할 수 있습니다.

### LLM 호출 경로 비교

| 항목 | Chat UI (`@Jupyternaut`) | `%%ai` 매직 (LiteLLM) |
|------|--------------------------|----------------------|
| 모델 ID 형식 | `openrouter/<model>` | `openrouter/<model>` |
| 환경변수 | `OPENROUTER_API_KEY` | `OPENROUTER_API_KEY` |
| 출력 위치 | Chat 사이드패널 | 노트북 셀 출력 |
| 변수 주입 | `@file:`, `@active-cell` | `{python_var}` |

### 트러블슈팅

| 증상 | 원인 | 해결 |
|------|------|------|
| `%%ai` 셀에서 `Cell magic not found` | 매직 미등록 | 노트북 시작 셀의 `register_cell_magic` 코드를 먼저 실행 |
| `LLM Provider NOT provided` (Chat UI) | config.json 구버전 형식 | `~/.local/share/jupyter/jupyter_ai/config.json`에서 `openrouter/<model>` 형식으로 수정 |
| `401 / 403` | API 키 미설정 | `./scripts/start_jupyter.sh`로 재시작 |
| Jupyternaut가 목록에 없음 | 미설치 | `pip install "jupyter-ai[jupyternaut]==3.0.0" litellm` 후 JupyterLab 재시작 |

## 덤프 기반 디버깅 예시

`memory.vmem` 분석 결과 (`Linux 6.5.0-41-generic`, user: `woreilly`)를 바탕으로 한 실제 사용 예시입니다.

> 아래 모든 예시는 [notebooks/dump_debug_examples.ipynb](notebooks/dump_debug_examples.ipynb) 에서 셀 단위로 바로 실행 가능합니다.

### `%%ai` 노트북 셀 예시 (5개)

**예시 1. alloc magic + kernel_oops root cause 추적**

```
%%ai openrouter/nvidia/nemotron-3-super-120b-a12b -f markdown
커널 메모리 덤프에서 'alloc magic is broken at %p: %lx' 문자열과
'kernel_oops:BUG:' 패턴이 동시에 발견됐어.
Linux 6.5.0-41-generic 환경에서 이 두 신호가 함께 나타날 때
가장 가능성 높은 root cause와 확인해야 할 커널 함수를 알려줘.
표 형식으로 우선순위 순으로 정리해줘.
```

**예시 2. OOM ↔ grub 할당자 손상 시나리오**

```
%%ai openrouter/nvidia/nemotron-3-super-120b-a12b -f markdown
메모리 덤프에서 아래 패턴들이 동시에 검출됐어:
- 'out of memory' 문자열
- grub_malloc / grub_realloc / grub_calloc 함수 패턴
- crashes:crash 신호

OOM killer가 개입했을 가능성과, grub 관련 할당자가 커널 패닉과 연결되는
시나리오를 단계별로 설명해줘. 각 단계에서 확인할 수 있는 커널 로그 패턴도 알려줘.
```

**예시 3. 외부 통신 위험도 평가 (변수 보간)**

노트북 셀에서 먼저 변수 준비:
```python
network_info = {
    "external_ip_count": 17,
    "internal_ip_count": 8,
    "interesting_ports": ["20 (FTP-data)", "22 (SSH)", "23 (Telnet)", "25 (SMTP)", "53 (DNS)"],
    "note": "Telnet/FTP-data는 평문 프로토콜로 보안 위험"
}
```

이후 `%%ai` 셀:
```
%%ai openrouter/nvidia/nemotron-3-super-120b-a12b -f markdown
아래 네트워크 정보를 분석해줘. 외부 IP와의 통신 패턴, 활성 포트를 보고
공격자 침투 또는 데이터 유출 가능성을 평가해줘.
특히 Telnet(23)과 FTP-data(20) 포트가 동시에 활성화된 위험도와
공격자가 이를 악용하는 구체적인 시나리오를 알려줘.

{network_info}
```

**예시 4. woreilly 계정 침해 가능성 평가 (변수 보간)**

노트북 셀에서 먼저 변수 준비:
```python
account_info = {
    "user": "woreilly",
    "external_contacts": 17,
    "kernel_errors_present": True,
    "crash_signals": ["kernel_oops:BUG:", "crashes:crash", "alloc magic is broken"]
}
```

이후 `%%ai` 셀:
```
%%ai openrouter/nvidia/nemotron-3-super-120b-a12b -f markdown
아래는 Linux 시스템의 계정 및 에러 정보야.
이 계정이 공격자 계정이거나 탈취됐을 가능성을 평가하고,
메모리 덤프에서 추가로 확인할 수 있는 아티팩트의 확인 방법을 알려줘.
(bash 히스토리 잔재, 열린 파일 디스크립터, 소켓 상태 등)

{account_info}
```

**예시 5. 전체 신호 종합 triage (context_summary 변수)**

노트북 셀에서 먼저 변수 준비:
```python
import json
context_summary = json.dumps({
    "kernel": "Linux 6.5.0-41-generic", "user": "woreilly",
    "panic_signals": ["alloc magic is broken at %p: %lx", "kernel_oops:BUG:", "crashes:crash"],
    "memory_patterns": ["out of memory", "grub_malloc", "grub_realloc", "grub_calloc"],
    "network": {"external_ip_count": 17, "ports": ["20 FTP-data", "22 SSH", "23 Telnet", "25 SMTP", "53 DNS"]},
}, ensure_ascii=False, indent=2)
```

이후 `%%ai` 셀:
```
%%ai openrouter/nvidia/nemotron-3-super-120b-a12b -f markdown
아래는 Linux 메모리 덤프 전체 분석 요약이야.
발견된 모든 신호를 검토하고 P0(즉시)/P1(24h 내)/P2(이번 주 내) 우선순위로 분류해줘.
각 항목마다 다음 조사를 위한 구체적인 명령어 또는 확인 방법도 포함해줘.

{context_summary}
```

---

### Chat UI (`@Jupyternaut`) 질문 예시 (5개)

JupyterLab 우측 Chat UI를 열고 (`File > New > Chat`) 아래 텍스트를 붙여넣어 사용하세요.

**질문 6. bash 도구 가용성 확인**

```
@Jupyternaut bash 도구로 /home/taejin/Jupyter/data/memory/memory.vmem 파일의 크기와 MD5 해시를 확인해줘.
```

**질문 7. 이 노트북 첨부 분석**

```
@Jupyternaut @file:notebooks/dump_debug_examples.ipynb 이 노트북의 %%ai 결과 중 가장 위험한 신호가 뭔지 요약해줘.
```

**질문 8. Telnet/FTP 공격 시나리오 심층 분석**

```
@Jupyternaut 이 덤프에서 Telnet(포트 23)과 FTP-data(포트 20)가 동시에 활성 상태였고 외부 IP 17개와 통신 흔적이 있어. Linux 6.5.0 서버에서 이 두 포트가 열려있을 때 공격자가 취할 수 있는 구체적인 공격 시나리오와 추가로 확인해야 할 프로세스/로그 위치를 알려줘.
```

**질문 9. woreilly 계정 후속 조사**

```
@Jupyternaut 덤프에서 유일한 사용자 계정인 woreilly가 외부 IP 17개와 통신했고 kernel_oops도 발생했어. 메모리 덤프에서 bash 히스토리 잔재, 열린 파일 디스크립터, 소켓 상태를 확인하려면 어떤 Volatility 플러그인이나 문자열 검색 패턴을 써야 해?
```

**질문 10. OOM killer 가설 검증 명령 생성**

```
@Jupyternaut 덤프에서 'out of memory' 신호와 grub 할당자 손상이 동시에 발견됐어. OOM killer 트리거를 검증하기 위해 memory.vmem에서 검색해야 할 커널 심볼 목록과 strings 명령 패턴을 구체적으로 알려줘.
```

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
