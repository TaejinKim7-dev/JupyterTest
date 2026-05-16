# `%%ai` 매직 + OpenRouter 설정 가이드

## 개요

`jupyter-ai-magics`의 `%%ai` 셀 매직으로 노트북 셀에서 직접 LLM을 호출할 수 있습니다.  
Chat UI(`@Jupyternaut`)와 달리 노트북 셀 결과로 응답이 렌더링됩니다.

```
노트북 셀 → %%ai 매직 → openai-chat-custom 프로바이더 → OpenRouter API → LLM
```

---

## 모델 ID 형식 비교

| 호출 경로 | 형식 | 예시 |
|-----------|------|------|
| Chat UI (`@Jupyternaut`) | `openrouter/<model-id>` | `openrouter/nvidia/nemotron-3-super-120b-a12b` |
| `%%ai` 매직 | `openai-chat-custom:<model-id>` | `openai-chat-custom:nvidia/nemotron-3-super-120b-a12b` |
| `%%ai` 매직 (alias) | `<alias>` | `nemo` |

> **왜 다른가?**  
> Chat UI는 LiteLLM이 OpenRouter 전용 형식을 처리하고,  
> `%%ai` 매직은 `langchain-openai`의 `ChatOpenAI`가 `OPENAI_API_BASE`로 라우팅합니다.

---

## 환경변수 설정

| 변수 | 용도 | 설정 위치 |
|------|------|-----------|
| `OPENROUTER_API_KEY` | Jupyternaut Chat UI | `jupyter_server_config.py` |
| `OPENAI_API_KEY` | `%%ai` 매직 | `jupyter_server_config.py` |
| `OPENAI_API_BASE` | `%%ai` 매직 엔드포인트 | `jupyter_server_config.py` |

`./scripts/start_jupyter.sh`으로 JupyterLab을 시작하면 세 변수가 모두 자동 설정됩니다.

---

## `ipython_config.py` 설정

위치: `~/.ipython/profile_default/ipython_config.py`

```python
# 기본 모델 (%%ai 만 쓸 때 provider:model 생략 가능)
c.AiMagics.initial_language_model = "openai-chat-custom:nvidia/nemotron-3-super-120b-a12b"

# 대화 히스토리 유지 교환 수 (기본값: 2)
c.AiMagics.max_history = 4

# alias 정의
c.AiMagics.aliases = {
    "nemo":     "openai-chat-custom:nvidia/nemotron-3-super-120b-a12b",
    "deepseek": "openai-chat-custom:deepseek/deepseek-chat",
    "claude35": "openai-chat-custom:anthropic/claude-3.5-sonnet",
}
```

alias 추가는 이 파일에서 `c.AiMagics.aliases` 딕셔너리에 항목을 추가하면 됩니다.  
JupyterLab 재시작 없이 노트북 커널 재시작만으로 반영됩니다.

---

## 주요 사용법

### 기본 호출
```python
%load_ext jupyter_ai_magics

%%ai nemo
Android 커널 패닉 원인 분석 방법을 설명해줘.
```

### 출력 포맷 (`-f`)
```python
%%ai nemo -f code       # 코드 블록
%%ai nemo -f markdown   # 마크다운 렌더링
%%ai nemo -f text       # 일반 텍스트
```

### Python 변수 주입
```python
findings = {"panic": ["NULL pointer at 0x0"], "processes": 312}

%%ai nemo -f markdown
분석 결과를 요약해줘: {findings}
```

### 셀 히스토리 참조
```python
%%ai nemo
방금 실행한 코드({In[-2]})의 결과({Out[-1]})를 설명해줘.
```

### 에러 디버깅
```python
# 에러가 발생한 셀 실행 후:
%ai fix nemo
```

### 컨텍스트 초기화
```python
%ai reset
```

### provider/model 목록 확인
```python
%ai list
```

---

## 트러블슈팅

### `LLM Provider NOT provided` 오류
모델 ID 형식이 잘못된 경우입니다.

| 잘못된 형식 | 올바른 형식 |
|-------------|-------------|
| `%%ai openai-chat:nvidia/nemotron-...` | `%%ai openai-chat-custom:nvidia/nemotron-...` |
| `%%ai openrouter/nvidia/nemotron-...` | `%%ai openai-chat-custom:nvidia/nemotron-...` |

`openai-chat:` 프로바이더는 GPT-3.5/4 등 고정된 모델만 허용합니다.  
OpenRouter 모델은 반드시 `openai-chat-custom:`을 사용하세요.

### `401 Unauthorized`
`OPENAI_API_KEY`가 설정되지 않은 경우입니다.

```bash
# 확인
echo $OPENAI_API_KEY
echo $OPENAI_API_BASE

# 수동 설정 후 JupyterLab 재시작
export OPENAI_API_KEY="sk-or-v1-..."
export OPENAI_API_BASE="https://openrouter.ai/api/v1"
```

또는 `./scripts/start_jupyter.sh`으로 재시작하세요.

### alias가 `%ai list`에 없음
`~/.ipython/profile_default/ipython_config.py`가 없거나 잘못된 경로입니다.

```bash
ls ~/.ipython/profile_default/ipython_config.py
```

파일이 있어도 반영이 안 되면 노트북 커널을 재시작하세요.

### `pip check` 경고 (langchain 버전 충돌)
```
langchain-openai 0.3.35 has requirement langchain-core<1.0.0, but you have langchain-core 1.4.0
jupyter-ai-magics 2.31.7 has requirement langchain<0.4.0, but you have langchain 1.3.1
```
이는 `jupyter-ai[jupyternaut]`이 `langgraph`를 통해 `langchain 1.x`를 설치하기 때문입니다.  
Chat UI(Jupyternaut)와 `%%ai` 매직 모두 실제 동작에는 지장 없음이 확인됐습니다(2026-05-16).

---

## 참고 링크

- [jupyter-ai-magics 공식 문서](https://jupyter-ai.readthedocs.io/en/latest/users/magic_commands/index.html)
- [Chat UI 설정 가이드](../docs/jupyter_ai_jupyternaut_openrouter_summary.md)  
  (상위 디렉토리: `docs/jupyter_ai_jupyternaut_openrouter_summary.md`)
- [데모 노트북](../notebooks/jupyter_ai_magic_demo.ipynb)
