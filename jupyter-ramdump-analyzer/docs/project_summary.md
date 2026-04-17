# 프로젝트 요약: Jupyter 기반 커널 디버깅 AI 분석 시스템

## 프로젝트 개요

주피터(JupyterLab) 환경에 대규모 언어 모델(LLM)을 통합하여 Android/Linux 커널 메모리 덤프(ramdump) 및 vmlinux 파일 분석을 자동화하는 시스템을 구축합니다.

## 핵심 목표

| 순위 | 목표 | 기대 효과 |
|------|------|-----------|
| 1 | 대화형 장애 원인 분석 | 메모리 플립, 커널 패닉 등 문제의 자연어 해석 |
| 2 | 반복 분석 작업 스크립트 자동 생성 | 수동 분석 시간 단축 |
| 3 | 레지스터/메모리 덤프 데이터의 자연어 해석 | 16진수 데이터의直이해 용이 |
| 4 | 사내 보안 환경 (오프라인/에어갭) 지원 | 민감 데이터 외부 유출 방지 |
| 5 | 메모리 비트 플립探测器 | 하드웨어 결함 자동 탐지 |

## 현재 환경

- **플랫폼**: JupyterLab (탭 기반 멀티 노트북)
- **분석 도구**: ramdump 로딩, vmlinux 심볼 파싱, 레지스터/변수 조회용 Python 코드
- **보안 제약**: ramdump/vmlinux 데이터는 사내 네트워크 밖 전송 불가
- **사용 가능 자원**: 확장 설치 권한, 사내 LLM API

## 기술 아키텍처

```
┌─────────────────────────────────────────────────────────────┐
│                     JupyterLab UI                          │
├─────────────────────────────────────────────────────────────┤
│  Jupyter AI / Notebook Intelligence / Custom MCP Server      │
├─────────────────────────────────────────────────────────────┤
│              LLM (Ollama / 사내 API / vLLM)                  │
├─────────────────────────────────────────────────────────────┤
│  분석 도구 (PyKdump, GDB, RAMParser, vmlinux)             │
├─────────────────────────────────────────────────────────────┤
│         데이터 (ramdump, vmlinux, 커널 로그)                │
└─────────────────────────────────────────────────────────────┘
```

## 구현 방식 (4가지 옵션)

### 방식 A: Jupyter AI (공식 확장)
- **장점**: 공식 프로젝트, ACP/MCP 지원, 채팅 UI 내장
- **적용**: OpenAI-compatible API 사용 시

### 방식 B: Notebook Intelligence (NBI)
- **장점**: Claude Code 통합, 인라인 코드 생성, 다양한 LLM 지원
- **적용**: 커스텀 LLM 프로바이더 유연하게 전환 필요 시

### 방식 C: Python 직접 통합 (커스텀 헬퍼)
- **장점**: 가장 유연함, 사내 API 규격 무관
- **적용**: 비표준 API or 세밀한 제어 필요 시

### 방식 D: 커스텀 MCP 서버
- **장점**: 도메인 특화 도구 제공, 에이전트가 직접 분석 함수 호출
- **적용**: 팀 전체가 쓸 표준 도구 구축 시

## 핵심 도구 목록

| 분류 | 도구 | 용도 |
|--------|------|------|
| ramdump 분석 | RAMParser (Qualcomm) | 커널 덤프 파싱 |
| | PyKdump |Crash Python 바인딩 |
| | GDB + pygdbmi | 디버깅 및 메모리 조회 |
| vmlinux 분석 | pyELFtools | ELF 심볼 파싱 |
| | vmlinux | 커널 심볼 파일 |
| LLM 연동 | Ollama | 로컬 LLM 서빙 |
| | LangChain | 에이전트/도구 호출 |
| | MCP (Model Context Protocol) | 에이전트-도구 통신 |

## 제공 도구 예시 (MCP 서버)

```python
@tool
def get_registers(cpu_id: str) -> dict:
    """특정 CPU의 레지스터 값을 조회"""

@tool
def read_memory(address: str, size: int) -> dict:
    """특정 메모리 주소의 값을 읽음"""

@tool
def lookup_symbol(address: str) -> dict:
    """주소에 해당하는 커널 심볼을 찾음"""

@tool
def get_callstack(cpu_id: str) -> dict:
    """특정 CPU의 콜스택을 추출"""

@tool
def detect_bitflip(start: str, end: str) -> dict:
    """메모리 영역에서 비트 플립 검출"""
```

## 보안 요구사항

1. **데이터 격리**: ramdump/vmlinux는 외부 전송 금지
2. **로컬 LLM**: Ollama 기반 사내 서빙
3. **오프라인 설치**: wheelhouse 기법 활용
4. **API 키 관리**: 환경 변수 또는 시크릿 매니저 사용
5. **프롬프트 인젝션 방지**: 시스템 프롬프트/데이터 분리

## 3단계 분석 라우팅

| 계층 | 역할 | 적용 모델 |
|--------|------|----------|
| 1층 (반사) | 간단한 패턴 추출 (정규식) | 파이썬 기본 |
| 2층 (빠른 사고) | 간단한 헥사 덤프 이상 판별 | Qwen2.5-Coder (7B) |
| 3층 (전문가) | 복합 근본 원인 분석 | MiMo-V2 / DeepSeek-Coder |

## 추천 LLM

| 모델 | 파라미터 | 특장점 |
|--------|----------|--------|
| Qwen2.5-Coder | 7B~32B | 로컬 코딩, 빠른 응답 |
| MiMo-V2-Flash | ~30B | 에이전트/tool calling |
| DeepSeek-Coder | ~33B | C/C++ 파싱, 버그 수정 |

## 구현 로드맵

| 단계 | 작업 | 예상 기간 |
|------|------|----------|
| 1 | 사내 LLM API 연결 테스트 | 1-2일 |
| 2 | LLMAssistant 헬퍼 클래스 개발 | 2-3일 |
| 3 | 매직 커맨드 개발 | 1-2일 |
| 4 | Jupyter AI/NBI 설치/설정 | 1일 |
| 5 | 프롬프트 템플릿 라이브러리 구축 | 3-5일 |
| 6 | 팀 배포 및 피드백 수집 | 1주 |
| 7 | MCP 서버 개발 (선택) | 2-3주 |

## 파일 출처

- `gemini_주피터 노트북 LLM 연동 개발 환경.md`
- `claude_jupyterlab_llm_integration_guide.md`
- `deep-research-report.md`