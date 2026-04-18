# Data

`data/` 는 로컬 분석에 사용하는 입력 데이터 보관 폴더입니다.

## 현재 구성

- `memory/`
  - `memory.vmem`
  - `memory.vmsn`
  - `memory.vmem.7z.001` 등 분할 압축본

## 주의

- 원본 `memory.vmem` 는 로컬 전용으로 유지합니다.
- GitHub 공유용으로는 `7z` 분할 압축본과 `memory.vmsn` 를 사용합니다.
- 기존 `xz` 같은 임시 압축 산출물은 로컬 파생 파일로 취급합니다.
- 루트 `.gitignore` 는 원본 `.vmem` 와 `.xz` 를 기본적으로 제외합니다.
