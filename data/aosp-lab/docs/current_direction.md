# Current Direction

## Goal

현재 목표는 Android/Linux 메모리 덤프에서 **원인 분석이 가능한 디버깅 도구**를 만드는 것입니다.

핵심 요구사항:

- ramdump 또는 panic 이후 남는 crash artifact 수집
- 대응하는 `vmlinux` 확보
- call trace, symbol, panic reason 기반 분석
- 이후 `jupyter-ramdump-analyzer` 에 연결 가능한 테스트 데이터셋 구축

## Why AOSP Build

프리빌트 emulator 실험에서는 다음까지는 확인했습니다.

- KVM enabled emulator boot
- `adb` 연결 성공

하지만 다음 단계에서 막혔습니다.

- `/sys/fs/pstore` 접근 권한 부족
- `adb root` 기반 panic/pstore 실험 불가

그래서 현재 방향은 **AOSP `userdebug/eng` 이미지 빌드**로 전환하는 것입니다.

이 방향의 장점:

- `adb root` 가능성 높음
- panic trigger 실험 가능
- 대응하는 `vmlinux` 확보 가능
- 의도적으로 만든 crash case를 ground-truth 데이터셋으로 보관 가능

## Current Build Target

현재 선택한 target:

```bash
lunch aosp_cf_x86_64_only_phone-trunk_staging-userdebug
```

현재 의미:

- product: `aosp_cf_x86_64_only_phone`
- release: `trunk_staging`
- variant: `userdebug`

## Planned Test Sequence

### Phase 1. Pipeline validation

가장 먼저 `sysrq-trigger` 로 panic 수집 파이프라인을 검증합니다.

목표:

- `adb root`
- panic 발생
- reboot 후 `pstore` 수집
- `vmlinux` 매칭 확인

예상 명령:

```bash
adb root
adb shell 'echo c > /proc/sysrq-trigger'
adb pull /sys/fs/pstore ...
find out -name vmlinux
```

### Phase 2. Ground-truth crash cases

그 다음은 테스트 전용 커널 코드를 추가합니다.

후보 파일:

- `drivers/misc/ramdump_test.c`

추천 인터페이스:

- `debugfs`

추천 trigger:

- `panic`
- `null_deref`
- `bug`

예시:

```bash
echo panic > /sys/kernel/debug/ramdump_test/trigger
echo null_deref > /sys/kernel/debug/ramdump_test/trigger
echo bug > /sys/kernel/debug/ramdump_test/trigger
```

이 방식의 목적:

- 재현 가능한 crash
- 명확한 root cause label
- 툴/LLM 분석 정확도 평가

## Artifact Plan

케이스별로 아래를 보관합니다.

- `console-ramoops`
- `dmesg-ramoops`
- `vmlinux`
- build target
- trigger command
- expected root cause

권장 위치:

- `data/aosp-lab/artifacts/case-001/`
- `data/aosp-lab/artifacts/case-002/`
- ...

## Current Status

- AOSP `repo init` 완료
- `repo sync` 완료
- `lunch aosp_cf_x86_64_only_phone-trunk_staging-userdebug` 완료
- 현재 build 진행 중

## Immediate Next Steps

1. build 완료
2. `find out -name vmlinux`
3. built image boot
4. `adb root` 확인
5. `sysrq-trigger` 테스트
6. `pstore` 수집
7. `ramdump_test.c` 추가
