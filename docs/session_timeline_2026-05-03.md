# Session Timeline - 2026-05-03

짧은 흐름만 남긴 타임라인 요약이다.

- 세션 초반에 `bubblewrap` 경고와 LLM 연결 상태를 정리했다.
- OpenRouter `openai/gpt-oss-120b:free`를 사용해 Jupyter/LLM 분석 경로를 검증했다.
- `nbconvert`와 기대값 검사 스크립트로 notebook 실행 결과를 확인했다.
- AOSP/Cuttlefish 환경을 구성하고 `aosp_cf_x86_64_only_phone-trunk_staging-userdebug` 빌드를 완료했다.
- `v4l2loopback.ko`에 `fault_trigger` sysfs 경로를 추가해 `warn`, `oops`, `panic` 트리거를 만들었다.
- custom `bzImage`와 ramdisk로 Cuttlefish를 부팅하고, guest에서 모듈을 `insmod`했다.
- `echo panic > /sys/devices/virtual/video4linux/video42/fault_trigger`로 kernel panic을 재현했다.
- QMP `dump-guest-memory`로 `vmcore.elf`를 수집했고, `DUMP_COMPLETED`를 확인했다.
- `crash`는 slab cache 초기화 단계에서 segfault가 나서, `gdb` 중심 경로로 전환했다.
- `gdb`에서 `ramdump_test_snapshot`을 확인했고, `RAMDUMP_TEST` marker와 `magic/version/video_nr/pid/comm/trigger`를 읽었다.
- 세션 결과를 문서화하고 GitHub에 커밋/푸시했다.

