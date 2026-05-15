# Jupyter AI + OpenRouter Workflow

이 문서는 `jupyter-ramdump-analyzer`에서 `jupyter-ai`를 두 가지 방식으로 쓰는 방법을 정리한다.

- `%%ai` notebook magic 중심
- JupyterLab chat UI 보조 사용

권장 기본값은 `%%ai` 중심이다. 분석 과정이 notebook에 재현 가능하게 남기 쉽기 때문이다.  
chat UI는 탐색, 프롬프트 수정, 빠른 실험용으로 같이 쓰면 된다.

## 설치

JupyterLab 4 계열과 `jupyter-ai` 최신 계열을 함께 설치한다.

```bash
pip install -r requirements-jupyter-ai.txt
```

추가로 `jupyter-ai`가 OpenRouter/OpenAI-compatible endpoint를 쓰려면 `langchain-openai`가 필요하다.

## 설정 파일

환경 변수 수동 설정 대신 설정 파일을 사용할 수 있다.

```bash
# 설정 파일 로딩 (bash)
source configs/jupyter_ai_openrouter.env

# 또는 Python에서
from dotenv import load_dotenv
load_dotenv("configs/jupyter_ai_openrouter.env")
```

설정 파일 목록:
- `configs/jupyter_ai_openrouter.env` - API 키 및 모델 설정
- `configs/jupyter_ai_openrouter.env.example` - 템플릿 (실제 키 제외)

## 환경 변수

OpenRouter free model 기준:

```bash
export OPENROUTER_API_KEY="YOUR_OPENROUTER_KEY"
export OPENAI_API_KEY="YOUR_OPENROUTER_KEY"
export OPENAI_API_BASE="https://openrouter.ai/api/v1"
export OPENAI_MODEL="nvidia/nemotron-3-super-120b-a12b:free"
export OPENAI_FALLBACK_MODEL="poolside/free"
```

주의:

- `OPENROUTER_API_KEY`는 Jupyter AI OpenRouter provider용 키다.
- `OPENAI_API_KEY`는 notebook magic이나 OpenAI-compatible SDK 경로에서 재사용할 수 있다.
- `OPENAI_API_BASE`는 OpenRouter API base URL을 사용한다.
- free 모델은 upstream 가용성에 따라 fallback이 필요하다.

## `%%ai` Notebook Magic

Notebook 셀에서 아래처럼 시작한다.

```python
%load_ext jupyter_ai
```

그 다음 `%%ai` 셀을 사용한다.

```python
%%ai openai-chat:nvidia/nemotron-3-super-120b-a12b:free
이 vmcore 분석 요약을 5줄로 정리해줘.
```

이 방식은 다음에 유리하다.

- 셀 단위로 프롬프트와 결과가 함께 저장된다.
- notebook 실행 로그를 그대로 재현할 수 있다.
- `nbconvert`/CI와 연결하기 쉽다.

## JupyterLab Chat UI

chat UI는 JupyterLab 좌측 패널의 Chat 항목에서 연다.

설정 흐름:

1. `jupyter lab` 실행 (또는 특정 노트북과 함께 실행 예: `jupyter lab notebooks/debug_chatbot.ipynb`)
2. Chat 패널 열기
3. `AI Settings`에서 `OpenRouter` provider 선택
4. `OPENROUTER_API_KEY` 또는 환경변수 값 입력
5. model id를 `nvidia/nemotron-3-super-120b-a12b:free`로 지정
6. base URL을 `https://openrouter.ai/api/v1`로 지정

이 방식은 다음에 유리하다.

- 파일과 대화를 빠르게 오가며 탐색할 수 있다.
- 프롬프트를 여러 번 수정하면서 실험하기 쉽다.
- notebook 밖에서도 같은 AI 작업 흐름을 유지할 수 있다.

## 이번 과제의 권장 사용법

- 분석 로직과 결과 기록은 `%%ai` notebook magic으로 남긴다.
- 프롬프트 실험과 빠른 질의는 chat UI로 보조한다.
- dump/vmlinux 같은 민감한 파일은 필요한 최소 결과만 LLM에 전달한다.
