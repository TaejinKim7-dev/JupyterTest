# jupyter-ai 3.x Chat UI ↔ OpenRouter 직접 연결 가능 여부

**작성일**: 2026-05-16  
**목적**: jupyter-ai 3.0.0에서 `File > New > Chat`으로 열리는 Chat UI가 OpenRouter에 직접 연결되는지 조사

---

## 결론 요약

| 방법 | 가능 여부 | 비고 |
|------|-----------|------|
| Chat UI → OpenRouter 직접 | **불가** (3.x 기준) | 3.x는 ACP 에이전트만 지원 |
| Chat UI → ACP Agent (OpenCode) → OpenRouter | **가능** | OpenCode 백엔드를 OpenRouter로 설정 |
| `%%ai` 매직 → OpenRouter | **가능** | `jupyter-ai-magics` 2.x는 OpenAI-compatible 지원 |

---

## jupyter-ai 버전별 아키텍처 차이

### 2.x (구버전)
- Chat UI가 **LangChain 기반 LLM 프로바이더에 직접 연결**
- 지원 프로바이더: OpenAI, Anthropic, Cohere, Ollama 등
- OpenRouter는 OpenAI-compatible URL로 연결 가능 (`OPENAI_API_BASE` 환경변수)
- `c.AiExtension.default_language_model`, `c.AiExtension.default_api_keys` 설정 사용

### 3.x (현재 설치됨: 3.0.0)
- Chat UI가 **ACP (Agent Client Protocol) 에이전트에만 연결**
- LLM 직접 연결 설정 제거됨
- 지원 ACP 에이전트: OpenCode, Claude Code, Codex CLI
- `c.AiExtension.*` 설정은 **무시됨** (silently ignored)

---

## 현재 환경 상태

```
pip show jupyter-ai → 3.0.0
pip show jupyter-ai-magics → 2.31.7
```

- `~/.jupyter/jupyter_server_config.py`의 `c.AiExtension.*` 설정 → 3.x에서 무효
- Chat UI에 연결된 에이전트: **OpenCode** (ACP)
- OpenCode 현재 백엔드: Google AI (auth.json에 `AIzaSy...` 키 확인됨)

---

## OpenRouter 연결 경로 분석

### 경로 A: jupyter-ai 2.x로 다운그레이드
- `pip install "jupyter-ai==2.24.0" "jupyter-ai-magics==2.24.0"`
- OpenAI-compatible 프로바이더로 OpenRouter 직접 연결 가능
- **단점**: pydantic v1/v2 충돌 발생 이력 있음, 3.x 기능 포기

### 경로 B: OpenCode 백엔드를 OpenRouter로 설정
- `~/.config/opencode/config.json` 또는 `auth.json` 수정
- OpenCode가 OpenRouter API를 백엔드로 사용하도록 구성
- Chat UI → OpenCode → OpenRouter 흐름
- **현재 가장 현실적인 경로**

### 경로 C: jupyter-ai 3.x에서 커스텀 ACP 에이전트 구현
- OpenRouter를 백엔드로 사용하는 ACP 서버를 직접 구현
- **복잡도 높음**, 공식 문서 부족

### 경로 D: `%%ai` 매직 사용 (Chat UI 포기)
- `jupyter-ai-magics` 2.31.7이 OpenAI-compatible 지원
- 노트북 셀에서 `%%ai openai-chat:nvidia/nemotron-3-super-120b-a12b` 사용
- **Chat UI가 아닌 매직 명령어 방식**

---

## 확인이 필요한 사항

1. **jupyter-ai 3.x 공식 로드맵**: OpenAI-compatible 직접 연결 재지원 계획이 있는지
   - https://github.com/jupyterlab/jupyter-ai/issues 에서 확인
   - 키워드: "openrouter", "custom provider", "3.x direct llm"

2. **OpenCode config 구조**: OpenRouter를 provider로 추가하는 정확한 설정 형식
   - `~/.config/opencode/config.json` 스키마
   - OpenCode 공식 문서: https://opencode.ai/docs

3. **jupyter-ai 3.x ACP 커스텀 에이전트**: 최소 구현 방법
   - https://jupyter-ai.readthedocs.io/en/latest/

---

## 참고 로그 증거

`0516_1029.log` 발췌:
```
404 GET /api/ai/completion/inline   ← 2.x 엔드포인트, 3.x에 없음
404 GET /api/ai/chats               ← 브라우저 캐시가 2.x API 호출
```
→ 3.x에서는 `/api/ai/` 경로 자체가 다르거나 없음을 시사

---

## 권장 다음 단계

1. OpenCode `config.json`에 OpenRouter provider 추가 테스트 (경로 B)
2. jupyter-ai GitHub Issues에서 "OpenRouter 3.x" 관련 이슈 검색
3. `%%ai` 매직으로 OpenRouter 동작 검증 후, Chat UI 필요 여부 재판단
