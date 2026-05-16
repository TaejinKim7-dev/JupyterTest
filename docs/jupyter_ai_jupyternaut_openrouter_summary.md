# Jupyter AI 3.x Chat UI에서 Jupyternaut + LiteLLM + OpenRouter 사용 정리

## 목적

JupyterLab의 **File > New > Chat**으로 열리는 Jupyter AI Chat UI에서 OpenRouter 모델을 사용해 LLM 도움을 받는 방법을 정리한다.

핵심 목표는 다음 흐름을 구성하는 것이다.

```text
Jupyter Chat UI → Jupyternaut → LiteLLM → OpenRouter → 선택한 LLM
```

---

## 핵심 결론

`jupyter-ai==3.0.0` 환경에서 OpenRouter를 Chat UI에 연결하려면, **OpenCode ACP 에이전트를 반드시 거칠 필요는 없다.**

Jupyter AI 3.x에는 선택 설치 가능한 **Jupyternaut**가 있으며, Jupyternaut는 **LiteLLM**을 통해 OpenRouter 모델을 사용할 수 있다.

따라서 가장 권장되는 경로는 다음과 같다.

| 경로 | 가능 여부 | 추천도 | 비고 |
|---|---:|---:|---|
| Chat UI → Jupyternaut → LiteLLM → OpenRouter | 가능 | 가장 추천 | Jupyter AI 3.x에서 목적에 가장 가까운 방식 |
| Chat UI → OpenCode ACP → OpenRouter | 가능 | 보조 경로 | OpenCode 설정을 별도로 구성해야 함 |
| Chat UI → OpenRouter v2 방식 직접 LangChain provider | 3.x 기준 비추천 | 낮음 | Jupyter AI 2.x 구조에 가까움 |
| `%%ai` 매직 → OpenRouter | 가능 | 보조 | Chat UI가 아니라 노트북 셀 방식 |

---

## 기존 이해에서 수정해야 할 부분

기존에는 다음과 같이 이해할 수 있었다.

> Jupyter AI 3.x Chat UI는 ACP 에이전트만 지원하므로 OpenRouter 직접 연결은 불가하다.

하지만 더 정확한 표현은 다음과 같다.

> Jupyter AI 3.x의 기본 Chat UI는 ACP 에이전트 중심으로 바뀌었지만, 선택 설치 가능한 Jupyternaut를 사용하면 LiteLLM을 통해 OpenRouter 모델을 Chat UI에서 사용할 수 있다.

즉, **3.x에서 OpenRouter 사용이 불가능한 것이 아니라, Jupyternaut 경로를 사용해야 한다.**

---

## 구성 요소 역할

### 1. Jupyter AI

JupyterLab에 Chat UI와 AI 관련 기능을 제공하는 확장이다.

Jupyter AI 3.x에서는 ACP 기반 에이전트 구조가 도입되었고, OpenCode, Claude Code, Codex CLI 같은 ACP 에이전트를 연결할 수 있다.

그러나 Jupyternaut를 추가로 설치하면, Chat UI에서 LiteLLM 기반 모델 provider를 사용할 수 있다.

### 2. Jupyternaut

Jupyter AI의 Chat UI에서 사용할 수 있는 AI persona 또는 assistant 역할을 한다.

Jupyternaut는 LiteLLM provider를 통해 여러 LLM 백엔드를 사용할 수 있으며, OpenRouter도 그중 하나로 연결할 수 있다.

### 3. LiteLLM

여러 LLM provider를 공통 인터페이스로 호출할 수 있게 해주는 라이브러리다.

OpenRouter 모델은 LiteLLM에서 다음 형식으로 지정한다.

```text
openrouter/<model-id>
```

예시:

```text
openrouter/nvidia/nemotron-3-super-120b-a12b
```

### 4. OpenRouter

OpenRouter는 여러 LLM 모델을 하나의 API로 사용할 수 있게 해주는 라우팅 서비스다.

OpenAI-compatible API 형식을 지원하므로 LiteLLM과 잘 맞는다.

---

## 권장 설치 방법

JupyterLab을 실행하는 **같은 Python 환경**에서 아래 명령을 실행한다.

```bash
python -m pip install --upgrade "jupyter-ai[jupyternaut]==3.0.0"
```

설치 확인:

```bash
python -m pip show jupyter-ai jupyter-ai-jupyternaut jupyter-ai-litellm litellm
python -m pip check
```

정상적으로 설치되었다면 다음 패키지들이 확인되어야 한다.

```text
jupyter-ai
jupyter-ai-jupyternaut
jupyter-ai-litellm
litellm
```

---

## OpenRouter API 키 설정

JupyterLab을 실행하기 전에 OpenRouter API 키를 환경변수로 설정한다.

```bash
export OPENROUTER_API_KEY="sk-or-v1-..."
```

그 다음 같은 터미널에서 JupyterLab을 실행한다.

```bash
jupyter lab
```

중요한 점은 API 키가 **노트북 커널 환경이 아니라 Jupyter 서버 프로세스 환경**에 들어가야 한다는 것이다.

따라서 키를 설정한 터미널에서 바로 `jupyter lab`을 실행하는 것이 가장 안전하다.

---

## 기본 모델 지정 예시

원하는 OpenRouter 모델을 기본 Chat model로 지정하고 JupyterLab을 실행하려면 다음처럼 실행할 수 있다.

```bash
export OPENROUTER_API_KEY="sk-or-v1-..."

jupyter lab \
  --AiExtension.initial_language_model="openrouter/nvidia/nemotron-3-super-120b-a12b"
```

모델 ID는 OpenRouter에서 사용하는 모델 ID를 그대로 넣되, 앞에 `openrouter/`를 붙인다.

예시:

```text
openrouter/openai/gpt-4o-mini
openrouter/anthropic/claude-3.5-sonnet
openrouter/google/gemini-2.5-pro
openrouter/nvidia/nemotron-3-super-120b-a12b
```

실제 사용 가능한 모델 ID는 OpenRouter 모델 목록에서 확인해야 한다.

---

## JupyterLab UI에서 설정하는 방법

JupyterLab을 실행한 뒤 다음 순서로 설정한다.

1. JupyterLab을 연다.
2. 상단 메뉴 또는 사이드바에서 **Settings**를 연다.
3. **Jupyternaut Settings**로 이동한다.
4. Chat model 또는 Language model 항목에 OpenRouter 모델을 입력한다.
5. 예를 들어 다음 값을 입력한다.

```text
openrouter/nvidia/nemotron-3-super-120b-a12b
```

6. **File > New > Chat**을 연다.
7. Chat UI에서 `@Jupyternaut`를 명시해 질문한다.

예시:

```text
@Jupyternaut 이 노트북의 코드를 설명해줘.
```

---

## `c.AiExtension.*` 설정에 대한 정리

Jupyter AI 2.x에서는 다음과 같은 설정을 통해 LangChain 기반 provider를 직접 지정하는 방식이 일반적이었다.

```python
c.AiExtension.default_language_model = "..."
c.AiExtension.default_api_keys = {...}
```

Jupyter AI 3.x에서는 Chat UI 구조가 ACP 중심으로 바뀌었기 때문에, 이 설정이 OpenCode 같은 ACP 에이전트의 백엔드를 바꾸지는 않는다.

하지만 Jupyternaut 경로에서는 다음 설정이 여전히 의미를 가질 수 있다.

```bash
jupyter lab \
  --AiExtension.initial_language_model="openrouter/nvidia/nemotron-3-super-120b-a12b"
```

정리하면 다음과 같다.

| 설정 | Jupyter AI 3.x에서의 의미 |
|---|---|
| `c.AiExtension.*`로 OpenCode 백엔드 변경 | 불가 |
| `AiExtension.initial_language_model`로 Jupyternaut 기본 모델 지정 | 가능 |
| UI에서 선택한 Jupyternaut 모델 | 보통 UI 설정이 우선 |

---

## OpenCode ACP 경로와의 차이

OpenCode를 사용하는 경우 흐름은 다음과 같다.

```text
Jupyter Chat UI → OpenCode ACP → OpenRouter
```

이 방식도 가능하지만, OpenCode 자체의 provider 설정을 별도로 구성해야 한다.

반면 Jupyternaut 경로는 다음과 같다.

```text
Jupyter Chat UI → Jupyternaut → LiteLLM → OpenRouter
```

이 경로는 Jupyter AI Chat UI에서 OpenRouter LLM을 쓰려는 목적에 더 직접적으로 맞는다.

---

## `%%ai` 매직과의 차이

`%%ai` 매직은 노트북 셀에서 LLM을 호출하는 방식이다.

예상 흐름:

```text
Notebook cell → %%ai magic → LiteLLM/OpenRouter → LLM
```

하지만 이 방식은 Chat UI가 아니다.

따라서 목적이 **File > New > Chat에서 OpenRouter LLM과 대화하기**라면, `%%ai` 매직보다 Jupyternaut 설정이 우선이다.

---

## 문제 발생 시 확인할 항목

### 1. Jupyternaut가 Chat UI에 보이지 않을 때

다음 명령으로 설치 상태를 확인한다.

```bash
python -m pip show jupyter-ai-jupyternaut jupyter-ai-litellm
```

서버 확장 상태도 확인한다.

```bash
jupyter server extension list | grep -E "jupyter_ai|jupyternaut"
jupyter labextension list | grep -E "jupyter-ai|jupyternaut"
```

설치 후에는 JupyterLab 서버를 완전히 재시작해야 한다.

---

### 2. OpenRouter 모델이 UI 목록에 안 보일 때

모델 목록 검색에 의존하지 말고 모델 ID를 직접 입력한다.

```text
openrouter/nvidia/nemotron-3-super-120b-a12b
```

---

### 3. 401 또는 403 오류가 날 때

OpenRouter API 키가 Jupyter 서버 프로세스에 전달되었는지 확인한다.

잘못된 예:

```bash
jupyter lab
# 이후 다른 터미널에서 export OPENROUTER_API_KEY=...
```

올바른 예:

```bash
export OPENROUTER_API_KEY="sk-or-v1-..."
jupyter lab
```

---

### 4. 패키지 충돌이 의심될 때

다음을 확인한다.

```bash
python -m pip check
python -m pip show litellm
```

`jupyter-ai[jupyternaut]==3.0.0` 설치 시 필요한 Jupyternaut 및 LiteLLM 관련 패키지가 같이 설치되어야 한다.

---

## 최종 권장 작업 순서

```bash
# 1. JupyterLab 실행 환경에서 Jupyternaut 포함 설치
python -m pip install --upgrade "jupyter-ai[jupyternaut]==3.0.0"

# 2. 설치 확인
python -m pip show jupyter-ai jupyter-ai-jupyternaut jupyter-ai-litellm litellm
python -m pip check

# 3. OpenRouter API 키 설정
export OPENROUTER_API_KEY="sk-or-v1-..."

# 4. 원하는 OpenRouter 모델을 기본값으로 지정하고 JupyterLab 실행
jupyter lab \
  --AiExtension.initial_language_model="openrouter/nvidia/nemotron-3-super-120b-a12b"
```

JupyterLab이 뜨면:

```text
File > New > Chat
```

그리고 Chat UI에서:

```text
@Jupyternaut OpenRouter 모델로 응답 중인지 확인해줘.
```

---

## 최종 요약

Jupyter AI 3.x에서 OpenRouter를 Chat UI에 연결하려면 다음 경로가 가장 적합하다.

```text
Jupyter Chat UI → Jupyternaut → LiteLLM → OpenRouter → 선택한 LLM
```

따라서 OpenCode ACP를 반드시 거칠 필요는 없으며, `jupyter-ai[jupyternaut]` 설치 후 Jupyternaut 모델을 `openrouter/<model-id>` 형식으로 지정하는 방식이 가장 간단하다.

---

## 참고 링크

- Jupyter AI Jupyternaut 문서: https://jupyter-ai.readthedocs.io/en/v3/users/jupyternaut/index.html
- Jupyter AI GitHub 저장소: https://github.com/jupyterlab/jupyter-ai
- Jupyter AI PyPI: https://pypi.org/project/jupyter-ai/
- LiteLLM OpenRouter provider 문서: https://docs.litellm.ai/docs/providers/openrouter
- OpenRouter OpenAI-compatible API 문서: https://openrouter.ai/docs/guides/community/openai-sdk
- OpenCode ACP 문서: https://opencode.ai/docs/ko/acp/
