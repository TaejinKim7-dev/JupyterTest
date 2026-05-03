# Session Log - 2026-05-03

이 문서는 이번 세션에서 진행한 대화와 작업을 시간순으로 요약한 기록이다.  
핵심 목표는 `jupyter-ramdump-analyzer`를 중심으로 Android/Cuttlefish panic 재현, `vmcore.elf` 확보, `vmlinux` 매핑, 그리고 분석 자동화 방향을 정리하는 것이었다.

## 1. 초기 정리

- `bubblewrap` 경고의 의미를 확인했다.
- `memory` 폴더에 샘플 dump와 `vmlinux`가 있어 테스트가 가능한 상태임을 전제로 잡았다.
- 공개된 LLM API를 연결 대상으로 두고, 기본 뼈대와 feasibility 분석만 먼저 다루기로 했다.
- 문서 요약본과 계획 파일을 만들고, 이후 작업 흐름을 Git으로 관리하도록 정리했다.

## 2. LLM 연결

- OpenRouter + `openai/gpt-oss-120b:free`를 선택했다.
- `~/.bashrc`의 `OPENAI_API_KEY`와 base URL 설정을 점검했다.
- 간단한 LLM 연결 테스트를 수행했고, 503 응답 같은 가용성 문제는 fallback 모델로 우회하는 방향을 잡았다.
- 이후 LLM 분석 결과가 실제로 LLM이 작성한 것인지, 어떤 입력을 줬을 때 그런 응답이 나오는지 점검했다.

## 3. Jupyter/Notebook 검증

- `nbconvert`로 notebook 실행을 테스트했다.
- 실행 결과가 `NO_ERRORS`면 셀 실행 자체는 성공했지만, 기대한 분석 결과가 모두 채워졌는지는 별도 검사 스크립트로 확인해야 한다는 점을 정리했다.
- `check_notebook_expectations.py`를 통해 `feasibility_report`, `fallback_used`, `api_failure_present` 같은 기대 조건을 점검했다.

## 4. AOSP/Cuttlefish 실험 환경

- `/home/taejin/Jupyter/data/aosp-lab` 아래에 AOSP lab 디렉터리를 구성했다.
- AOSP `repo sync`를 수행했고, `aosp_cf_x86_64_only_phone-trunk_staging-userdebug`를 빌드 대상으로 선택했다.
- Cuttlefish 실행에 필요한 `cuttlefish-base`, `cuttlefish-defaults`, `cuttlefish-integration`, `cuttlefish-metrics`를 설치했다.
- `launch_cvd --vm_manager=qemu_cli`로 Cuttlefish를 구동했고, `adb root`, `adb shell`, `kptr_restrict` 확인 같은 기본 검증을 했다.

## 5. 커널 panic 재현

- `v4l2loopback.ko`를 대상으로 sysfs trigger를 추가했다.
- trigger 이름은 `fault_trigger`로 만들고, `warn`, `oops`, `panic` 경로를 정의했다.
- `panic` 경로는 실제 kernel panic을 발생시키도록 구성했다.
- custom `bzImage`, custom vendor ramdisk, matching `vmlinux` 조합으로 Cuttlefish를 부팅한 뒤 panic을 유도했다.
- `echo panic > /sys/devices/virtual/video4linux/video42/fault_trigger`로 panic을 재현했다.

## 6. vmcore 확보

- QMP `dump-guest-memory`를 사용해 `vmcore.elf`를 수집했다.
- `paging:true` 옵션으로 전체 guest memory를 ELF core 형태로 덤프했다.
- `qmp_transcript_paging_true.log`에 `DUMP_COMPLETED`와 `paused` 상태를 확인했다.
- `vmcore.elf`, `vmlinux`, `bzImage`, `kernel.log`를 함께 보관하는 결과 디렉터리를 구성했다.

## 7. crash / gdb 분석

- `crash`와 `gdb`를 설치했다.
- `crash 8.0.0`은 현재 Android 6.12 계열 `vmcore.elf`와 `vmlinux` 조합에서 안정적으로 동작하지 않았고, slab cache 초기화 단계에서 segfault가 발생했다.
- `vmlinux`의 debug section 압축을 해제한 뒤 `gdb`로 vmcore를 읽어 레지스터와 스택을 확인했다.
- panic CPU로 보이는 thread에서 `rip`, `rsp`, `rbp`, backtrace, stack memory를 확인했다.
- `Kernel Offset`을 이용해 KASLR 보정을 수행했고, kernel log와 심볼을 맞춰 `panic`, `attr_store_fault_trigger`, `sysfs_kf_write` 같은 경로를 확인했다.

## 8. snapshot 방식 결정

- raw memory dump만으로는 구조체 필드 추적이 불편하다는 점을 확인했다.
- `vmcore.elf` 자체가 이미 메모리 내용을 포함하므로, 우선순위는 `vmcore.elf + vmlinux + .ko + kernel.log`로 정했다.
- full dump를 대체하는 대신, panic 직전에 관심 값을 전역 `snapshot` 구조체에 저장하는 방식을 채택했다.
- `snapshot`은 dump에서 구조체 값을 찾기 위한 anchor로 사용한다.

## 9. 실제 구현

- `v4l2loopback.c`에 `ramdump_test_snapshot` 전역 구조체를 추가했다.
- `magic`, `version`, `video_nr`, `dev`, `vdev`, `task`, `pid`, `comm`, `trigger`, `marker`를 저장하도록 했다.
- `RAMDUMP_TEST` marker를 넣어 raw/ELF 양쪽에서 검색 가능하게 했다.
- panic 직전에 snapshot을 채우고, 이후 deliberate panic으로 이어지게 했다.
- `kptr_restrict=2` 때문에 `/sys/module/v4l2loopback/sections/*`가 0으로 보이는 문제를 실험 중에만 `0`으로 낮춰 주소를 얻고, 다시 `2`로 원복했다.

## 10. 검증 결과

- 모듈 빌드는 성공했다.
- guest에서 `insmod`가 성공했고, `/sys/devices/virtual/video4linux/video42/fault_trigger`가 생성됐다.
- `vmcore.elf`에서 `RAMDUMP_TEST` marker를 실제로 검색했다.
- `gdb`에서 `ramdump_test_snapshot`의 raw 바이트를 읽어 `magic`, `version`, `video_nr`, `pid`, `comm`, `trigger`, `marker`를 확인했다.
- `comm`은 `sh`, `trigger`는 `panic`, `video_nr`는 `42`였다.

## 11. Git 기록

- 작업 요약 문서와 patch 파일을 GitHub에 올렸다.
- 대용량 소스/덤프 산출물은 `.gitignore`로 제외했다.
- 이후 세션에서 재현 가능한 절차를 `docs/v4l2loopback_snapshot_vmcore_test.md`에 정리했다.

## 12. 현재 상태

- Cuttlefish 실험은 종료했다.
- `vmcore.elf` 기반 분석 경로가 확보됐다.
- 다음 단계는 이 snapshot-based vmcore 분석 흐름을 Jupyter 파이프라인에 자동화로 붙이는 것이다.

