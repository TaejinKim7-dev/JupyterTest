# AOSP Lab

`data/aosp-lab/` 는 AOSP 기반 `userdebug/eng` 이미지, panic 재현, `pstore` 수집, `vmlinux` 확보를 위한 실험 작업 디렉터리입니다.

## 목적

- 프리빌트 emulator 대신 `adb root` 가능한 빌드 사용
- `panic()`, `NULL deref`, `OOM` 시나리오 재현
- 각 케이스별 `console-ramoops`, `dmesg-ramoops`, `vmlinux` 보관
- 이후 `jupyter-ramdump-analyzer` 에 정답 데이터셋으로 연결

## 디렉터리 구조

- `artifacts/`
  - 케이스별 수집 산출물 보관
- `configs/`
  - manifest, lunch target, 커널/부팅 옵션 기록
- `docs/`
  - 실행 절차, 체크리스트, 분석 메모
- `logs/`
  - repo sync, build, emulator 실행 로그
- `scripts/`
  - 환경 변수 및 반복 실행용 헬퍼 스크립트
- `source/`
  - AOSP 소스 checkout 위치
- `out/`
  - AOSP build output
- `dist/`
  - 복사한 `vmlinux`, `boot.img`, 수집본 등 배포용 아티팩트

`source/`, `out/`, `dist/` 는 용량이 크므로 Git에서 제외합니다.

## 현재 목표

1. `repo` 설치 및 AOSP checkout 준비
2. `userdebug` 또는 `eng` 대상 빌드
3. KVM 가능한 현재 WSL 환경에서 emulator 재실행
4. `adb root` 확인
5. `echo c > /proc/sysrq-trigger` 또는 커널 버그 재현
6. 재부팅 후 `pstore` 수집
7. 대응하는 `vmlinux` 와 함께 케이스 정리
