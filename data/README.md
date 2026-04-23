# Data

`data/` 는 로컬 분석에 사용하는 입력 데이터 보관 폴더입니다.

## 현재 구성

- `android-emulator/`
  - 프리빌트 Android emulator feasibility 실험 디렉터리
  - 문서만 Git 관리, `sdk/` 와 로그는 제외
- `aosp-lab/`
  - AOSP `userdebug/eng` 실험용 작업 디렉터리
  - `README.md`, `docs/`, `scripts/` 포함
- `memory/`
  - `memory.vmem`
  - `memory.vmsn`
  - `memory.vmem.7z.001` 등 분할 압축본

## 주의

- 원본 `memory.vmem` 는 로컬 전용으로 유지합니다.
- GitHub 공유용으로는 `7z` 분할 압축본과 `memory.vmsn` 를 사용합니다.
- 기존 `xz` 같은 임시 압축 산출물은 로컬 파생 파일로 취급합니다.
- 루트 `.gitignore` 는 원본 `.vmem` 와 `.xz` 를 기본적으로 제외합니다.
- `android-emulator/sdk`, `android-emulator/downloads`, `android-emulator/logs` 는 Git에서 제외합니다.
- `aosp-lab/source`, `aosp-lab/out`, `aosp-lab/dist` 는 대용량이므로 Git에서 제외합니다.
