# HANDOFF.md

업데이트: 2026-05-16 (2차)

---

## 1. 프로젝트 개요

JupyterLab + OpenRouter(LLM) 으로 Android/Linux 커널 ramdump를 분석하는 feasibility 프로젝트.
주 분석 대상: `/home/taejin/Jupyter/data/memory/memory.vmem` (4GB, Linux 6.5.0-41-generic, user: woreilly)

---

## 2. 주요 파일 경로

| 파일 | 역할 |
|------|------|
| `src/llm_assistant.py` | OpenRouter 직접 호출 클라이언트 (requests 기반) |
| `src/memory_kernel_analyzer.py` | vmem 분석 → `build_analysis_context()`, `summarize_findings()` |
| `notebooks/interactive_log_analyzer.ipynb` | 메인 분석 노트북. %%ai 매직 + ipywidgets 채팅 UI |
| `notebooks/dump_debug_examples.ipynb` | 덤프 기반 디버깅 예시 10개 (%%ai 5 + Chat UI 5). memory.vmem 로드 없이 실행 가능 |
| `notebooks/jupyter_ai_magic_demo.ipynb` | %%ai 매직 사용법 데모 |
| `scripts/start_jupyter.sh` | venv 활성화 + env 파일 로드 + jupyter lab 실행 |
| `configs/jupyter_ai_openrouter.env` | API 키 (gitignore, .example만 커밋됨) |
| `requirements-jupyter-ai.txt` | 전체 의존성 (jupyternaut + litellm 포함) |
| `docs/jupyter_ai_magic_setup.md` | %%ai 매직 설정 가이드 |
| `docs/jupyter_ai_jupyternaut_openrouter_summary.md` | Chat UI 설정 가이드 (상위 `docs/` 디렉토리) |

로컬 전용 설정 (repo 외부, 재현 시 수동 생성 필요):
- `~/.jupyter/jupyter_server_config.py` — API 키, 모델, root_dir
- `~/.local/share/jupyter/jupyter_ai/config.json` — Jupyternaut 모델 (`openrouter/nvidia/nemotron-3-super-120b-a12b`)

---

## 3. 핵심 결정사항

**jupyter-ai 3.x Chat UI 연결 방식**
- `jupyter-ai[jupyternaut]==3.0.0` + `litellm` 조합
- 모델 ID 형식: `openrouter/<model-id>` (LiteLLM 형식)
- Chat UI → Jupyternaut → LiteLLM → OpenRouter

**%%ai 매직 방식**
- `jupyter-ai-magics` 제거 (langchain<0.4.0 요구 vs 환경의 langchain 1.x 충돌)
- 대신 `register_cell_magic` + `litellm.completion()` 으로 직접 구현
- `cell.format_map(get_ipython().user_ns)` 로 `{python_var}` 보간 지원
- 구현 위치: `interactive_log_analyzer.ipynb` 셀 7 / `jupyter_ai_magic_demo.ipynb` 셀 2

**현재 동작 모델**
- OpenRouter: `nvidia/nemotron-3-super-120b-a12b` (free tier, ~7s)
- Fallback: `poolside/laguna-m.1:free`

---

## 4. 현재 상태

**완료된 것 (2026-05-16 1차)**
- Chat UI (`@Jupyternaut`) → OpenRouter 응답 확인
- `%%ai` 매직 → `{context_summary}` 보간 포함 응답 확인
- `interactive_log_analyzer.ipynb` 전체 실행 (Step 1~4) 확인
- README에 초기 설정 재현 절차(4단계) + 덤프 기반 디버깅 예시 추가
- GitHub `TaejinKim7-dev/JupyterTest` main 반영 (`aca9d0d`)

**완료된 것 (2026-05-16 2차)**
- `notebooks/dump_debug_examples.ipynb` 신규 생성 및 사용자 테스트 완료
  - %%ai 5개 셀 (alloc magic+oops / OOM↔grub / 네트워크 / 계정 / 종합 triage) — `{변수}` 보간 포함
  - Chat UI 질문 5개 markdown 셀 (bash 도구 / @file 첨부 / Telnet-FTP / woreilly 계정 / OOM 가설)
  - memory.vmem 로드 없이 하드코딩 변수로 즉시 실행 가능
- README 덤프 예시 5개 → 10개로 교체 (%%ai 5 + @Jupyternaut 5)
- GitHub main 반영 (`ae6e403`)

**바로 다음 할 일**
- `jupyter_ai_magic_demo.ipynb` 실제 실행 테스트 (작성만 됨, 미실행)
- Jupyternaut bash 도구로 vmem 직접 분석 명령 실행 테스트 (보안 주의)
- `src/llm_assistant.py`의 `OPENAI_API_KEY` 의존을 `OPENROUTER_API_KEY`로 통일

---

## 5. TODO (우선순위 순)

1. `jupyter_ai_magic_demo.ipynb` 전체 셀 실행 검증 (미실행)
2. Jupyternaut bash 도구로 vmem 직접 분석 명령 실행 테스트 (보안 주의)
3. `src/llm_assistant.py`의 `OPENAI_API_KEY` 의존을 `OPENROUTER_API_KEY`로 통일
4. 다른 무료 OpenRouter 모델 가용성 재확인 (deepseek, gemma 등 간헐적 404)
5. Chat UI `@file:` 첨부 기능 심층 활용 (노트북 분석 결과 자동 요약)

---

## 6. 실패한 접근 (재시도 금지)

| 시도 | 실패 원인 |
|------|-----------|
| `jupyter-ai-magics` + `langchain 1.x` 공존 | magics가 `langchain<0.4.0` 요구, import 단계에서 `ImportError` |
| `openai-chat:nvidia/nemotron-...` 형식으로 %%ai | `openai-chat:` provider는 GPT-3.5/4만 허용 |
| `c.AiExtension.default_language_model` (2.x 설정) | jupyter-ai 3.x에서 silently ignored |
| `~/.jupyter/lab/user-settings/@jupyter-ai/core/plugin.jupyterlab-settings` | 3.x schema 불일치로 거부됨 |
| `langchain 0.x`로 다운그레이드 | langgraph 1.x가 langchain-core>=1.0.0 요구, Jupyternaut 깨짐 |

---

## 7. 핵심 명령어

```bash
# JupyterLab 시작 (모든 환경변수 자동 설정)
cd ~/Jupyter/jupyter-ramdump-analyzer && ./scripts/start_jupyter.sh

# %%ai 매직 등록 (노트북 시작 셀)
# → interactive_log_analyzer.ipynb 셀 7 참고

# Jupyternaut 모델 확인
cat ~/.local/share/jupyter/jupyter_ai/config.json

# 환경변수 확인
echo $OPENROUTER_API_KEY && echo $OPENAI_API_BASE
```

**모델 ID 형식 요약**

| 경로 | 형식 |
|------|------|
| Chat UI (`@Jupyternaut`) | `openrouter/nvidia/nemotron-3-super-120b-a12b` |
| `%%ai` 매직 | `openrouter/nvidia/nemotron-3-super-120b-a12b` |
| `src/llm_assistant.py` | `nvidia/nemotron-3-super-120b-a12b:free` (직접 requests) |
