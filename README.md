# Jupyter Workspace

이 저장소는 Jupyter 기반 커널 메모리 덤프 분석 프로젝트와 관련 문서, 데이터, 아카이브를 함께 관리하기 위한 루트 워크스페이스입니다.

## 구조

```text
Jupyter/
├── AGENTS.md
├── README.md
├── docs/
│   └── research/              # 조사/요약 문서
├── data/
│   └── memory/                # 로컬 전용 대용량 샘플 데이터
├── archive/
│   └── git-metadata/          # 이전 개별 프로젝트 Git 메타데이터 보관
└── jupyter-ramdump-analyzer/  # 메인 분석 프로젝트
```

## 관리 원칙

- 메인 개발 대상은 `jupyter-ramdump-analyzer/` 입니다.
- `data/memory/` 의 대용량 바이너리 덤프는 GitHub에 올리지 않고 로컬에서만 유지합니다.
- `docs/research/` 는 참고 문서와 조사 결과를 보관합니다.
- `archive/git-metadata/` 는 루트 Git 통합 전에 존재하던 하위 프로젝트의 `.git` 디렉터리를 보관합니다.

## 시작점

- 프로젝트 문서: [jupyter-ramdump-analyzer/README.md](/home/taejin/Jupyter/jupyter-ramdump-analyzer/README.md)
- 연구 문서: [docs/research](/home/taejin/Jupyter/docs/research)
- 데이터 안내: [data/README.md](/home/taejin/Jupyter/data/README.md)

## Sample Data Source

- 공개된 Linux 메모리 덤프 샘플은 13Cubed의 Ubuntu 22.04 메모리 포렌식 챌린지 자료를 사용했습니다.
- 다운로드: https://cdn.13cubed.com/downloads/linux_challenge.zip
