# 테스트 가이드

`jupyter-ramdump-analyzer` 로컬 변경사항 검증을 위한 단계별 테스트 가이드입니다.

---

## 0. 사전 준비

### 환경 변수 설정

```bash
cd jupyter-ramdump-analyzer

# 템플릿 복사
cp configs/jupyter_ai_openrouter.env.example configs/jupyter_ai_openrouter.env

# 실제 API 키와 모델로 수정
# OPENAI_API_KEY=<your_openrouter_key>
# OPENAI_MODEL=nvidia/nemotron-3-super-120b-a12b:free
# OPENAI_FALLBACK_MODEL=poolside/free
```

### 패키지 설치

```bash
pip install -r requirements.txt
pip install openai  # test_llm_api.py 용
```

---

## 1. API 연결 테스트 — `test_llm_api.py`

OpenRouter API 키와 poolside 모델이 정상 응답하는지 확인합니다.

```bash
python test_llm_api.py
```

**기대 출력:**

```
=== First Response ===
Content: There are 3 r's in the word 'strawberry'.
Reasoning: ...

=== Second Response ===
Content: ...
Reasoning: ...
```

**확인 포인트:**
- `Content`가 비어있지 않으면 API 연결 성공
- `Reasoning`이 출력되면 reasoning 기능 동작 확인
- 오류 발생 시 `configs/jupyter_ai_openrouter.env`의 `OPENAI_API_KEY` 값 확인

---

## 2. LLMAssistant 클래스 테스트

기본 모델(`nvidia/nemotron-3-super-120b-a12b:free`)과 fallback(`poolside/free`)을 확인합니다.

```bash
python - <<'EOF'
import os
from dotenv import load_dotenv
load_dotenv("configs/jupyter_ai_openrouter.env")

from src.llm_assistant import LLMAssistant

ai = LLMAssistant()
print("모델:", ai.model)
print("Fallback:", ai.fallback_models)
print("API 키 설정됨:", ai.is_configured())

# 간단한 질문 테스트
response = ai.ask("커널 패닉이란 무엇인지 한 줄로 설명해줘.")
print("응답:", response[:200])
EOF
```

**확인 포인트:**
- `모델: nvidia/nemotron-3-super-120b-a12b:free`
- `Fallback: ['poolside/free']`
- `API 키 설정됨: True`
- 응답이 `[API 호출 실패]`로 시작하지 않으면 정상

---

## 3. 기존 파이프라인 유닛 테스트

```bash
python -m unittest discover -s tests -v
```

**기대 출력:** 모든 테스트 `OK`

---

## 4. Jupyter AI `%%ai` magic 테스트

```bash
source configs/jupyter_ai_openrouter.env
jupyter lab notebooks/jupyter_ai_openrouter_demo.ipynb
```

노트북에서 아래 셀 실행:

```python
%load_ext jupyter_ai
```

```python
%%ai openai-chat:nvidia/nemotron-3-super-120b-a12b:free
커널 패닉의 가장 흔한 원인 3가지를 짧게 설명해줘.
```

**확인 포인트:**
- `%%ai` 셀 실행 후 셀 아래에 LLM 응답이 렌더링되면 정상

---

## 5. JupyterLab 챗봇 실행 테스트

```bash
bash run_debug_chatbot.sh
```

브라우저에서 `http://localhost:8888` 접속 후:
1. 좌측 Chat 패널 열기
2. `AI Settings` → Provider: `OpenRouter`, Model: `nvidia/nemotron-3-super-120b-a12b:free`
3. 간단한 질문 입력 후 응답 확인

---

## 6. 파일럿 노트북 실행 테스트

```bash
jupyter lab notebooks/pilot_test_notebook.ipynb
```

노트북 전체 셀 순차 실행 (`Run All Cells`) 후:
- LLM 분석 결과 셀에 오류 없이 출력되면 정상
- vmcore/dump 파일 없이도 mock 데이터로 기본 흐름 확인 가능

---

## 7. 모델 변경 확인

`llm_assistant.py`에서 변경된 기본 모델이 실제로 적용되는지 확인합니다.

```bash
python -c "from src.llm_assistant import LLMAssistant; print(LLMAssistant.DEFAULT_MODEL)"
```

**기대 출력:**

```
nvidia/nemotron-3-super-120b-a12b:free
```

---

## 체크리스트

| # | 항목 | 통과 조건 |
|---|------|-----------|
| 1 | `test_llm_api.py` | Content/Reasoning 출력 확인 |
| 2 | LLMAssistant 기본 모델 | `nvidia/nemotron-3-super-120b-a12b:free` |
| 3 | LLMAssistant fallback 모델 | `['poolside/free']` |
| 4 | 유닛 테스트 | 모든 테스트 OK |
| 5 | `%%ai` magic | LLM 응답 렌더링 |
| 6 | 챗봇 스크립트 | JupyterLab 정상 기동 |
| 7 | 파일럿 노트북 | 오류 없이 전체 실행 |

---

## 트러블슈팅

**API 키 오류 (`401 Unauthorized`)**
- `configs/jupyter_ai_openrouter.env`에서 `OPENAI_API_KEY` 확인
- OpenRouter 대시보드에서 키 유효 여부 확인

**모델 응답 없음 (`upstream 없음`)**
- free 모델은 일시적으로 가용 불가 상태일 수 있음
- fallback 모델 `poolside/free`가 자동으로 시도됨
- 지속 실패 시 OpenRouter 모델 목록에서 대체 free 모델 선택

**`%%ai` magic 인식 안 됨**
- `pip install jupyter-ai langchain-openai` 재실행
- 환경 변수 `source configs/jupyter_ai_openrouter.env` 후 Jupyter 재시작
