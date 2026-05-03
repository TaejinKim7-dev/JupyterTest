# v4l2loopback Snapshot -> vmcore -> gdb 검증 절차

이 문서는 Cuttlefish(QEMU) 게스트에서 커널 패닉을 의도적으로 만들고, `vmcore.elf`에서 커널/모듈 구조체 내부 값을 확인하는 재현 절차를 정리합니다.

핵심 아이디어는 panic 직전에 모듈 전역(static) snapshot 구조체에 필요한 포인터/값을 저장해 두고, dump 분석 시 그 snapshot을 anchor로 사용해 구조체를 따라가는 것입니다.

## 산출물(로컬)

본 실험에서 사용한 결과 디렉터리 예시:

`/home/taejin/Jupyter/data/aosp-lab/ramdump-results/v4l2loopback-snapshot-vmcore-20260502-221716`

## 커널 모듈 패치

GitHub에는 대용량 Android kernel tree를 올리지 않고, patch 파일로만 기록합니다.

- patch: `patches/android-kernel-virtual-device-v4l2loopback-snapshot.patch`
- 기능:
  - sysfs `fault_trigger` 추가: `warn`, `oops`, `panic`
  - `static struct ramdump_test_snapshot ramdump_test_snapshot` 추가
  - trigger 직전에 snapshot에 `magic/version/video_nr/dev/vdev/task/pid/comm/trigger/marker` 저장

## 빌드(호스트)

Android kernel tree에서 모듈 빌드:

```bash
cd /home/taejin/Jupyter/data/android-kernel
tools/bazel build //common-modules/virtual-device:x86_64/v4l2loopback
```

빌드 산출물 예시:

- `.ko`: `/home/taejin/Jupyter/data/android-kernel/bazel-bin/common-modules/virtual-device/x86_64/v4l2loopback/v4l2loopback.ko`
- `bzImage`: `/home/taejin/Jupyter/data/android-kernel/bazel-bin/common-modules/virtual-device/virtual_device_x86_64_kbuild_mixed_tree/bzImage`
- `vmlinux`: `/home/taejin/Jupyter/data/android-kernel/bazel-bin/common-modules/virtual-device/virtual_device_x86_64_kbuild_mixed_tree/vmlinux`

## Cuttlefish 부팅(호스트)

custom kernel + vendor ramdisk로 부팅:

```bash
cd /home/taejin/Jupyter/data/aosp-lab/source
source build/envsetup.sh
lunch aosp_cf_x86_64_only_phone-trunk_staging-userdebug
export PATH="$PWD/out/host/linux-x86/bin:$PATH"

launch_cvd --daemon --vm_manager=qemu_cli --report_anonymous_usage_stats=n --noresume \
  --kernel_path=/path/to/bzImage \
  --initramfs_path=/path/to/vendor_ramdisk.img \
  --extra_kernel_cmdline=panic=0
```

## 모듈 로드(guest)

```bash
adb root
adb push v4l2loopback_snapshot.ko /data/local/tmp/v4l2loopback_snapshot.ko
adb shell 'rmmod v4l2loopback 2>/dev/null || true'
adb shell 'insmod /data/local/tmp/v4l2loopback_snapshot.ko devices=1 video_nr=42 card_label=ramdump_snapshot exclusive_caps=1'
adb shell 'cat /sys/devices/virtual/video4linux/video42/fault_trigger'
```

## module section 주소 확보(중요)

`gdb add-symbol-file`에 필요한 `.text/.data/.bss` 주소가 Android에서 `kptr_restrict=2`이면 `0x0`으로 마스킹됩니다.

실험용으로 일시 해제 후 주소를 읽고, 즉시 원복합니다.

```bash
adb root
adb shell 'cat /proc/sys/kernel/kptr_restrict'

adb shell 'echo 0 > /proc/sys/kernel/kptr_restrict'
adb shell 'for s in .text .data .bss; do echo "$s=$(cat /sys/module/v4l2loopback/sections/$s)"; done'
adb shell 'echo 2 > /proc/sys/kernel/kptr_restrict'
```

## panic 유도 + vmcore 수집(QMP)

panic은 ADB가 hang될 수 있으므로, QMP로 VM을 `stop`한 뒤 `dump-guest-memory`를 실행합니다.

QMP 소켓:

`/tmp/cf_avd_1000/cvd-1/internal/qemu_monitor.sock`

예시(호스트):

```bash
adb shell 'echo 1 > /proc/sys/kernel/sysrq; echo panic > /sys/devices/virtual/video4linux/video42/fault_trigger' &
PANIC_PID=$!

SOCK=/tmp/cf_avd_1000/cvd-1/internal/qemu_monitor.sock
{
  printf '{"execute":"qmp_capabilities"}\n'
  printf '{"execute":"stop"}\n'
  printf '{"execute":"dump-guest-memory","arguments":{"paging":true,"protocol":"file:/path/to/vmcore.elf"}}\n'
  printf '{"execute":"query-status"}\n'
} | nc -U -N "$SOCK" > qmp_transcript.log

kill $PANIC_PID 2>/dev/null || true
```

## gdb로 snapshot 확인

주의: `.ko`에 DWARF 타입 정보가 없을 수 있어 `p ramdump_test_snapshot`은 타입 에러가 날 수 있습니다.
이 경우 `&ramdump_test_snapshot` 주소를 얻고 바이트 덤프로 구조체를 확인합니다.

```bash
VMLINUX=vmlinux.uncompressed
VMCORE=vmcore.elf
KO=v4l2loopback_snapshot.ko

TEXT=0xffffffffc0......   # /sys/module/.../sections/.text 값
DATA=0xffffffffc0......
BSS=0xffffffffc0......

gdb -q "$VMLINUX" "$VMCORE" -batch \
  -ex "add-symbol-file $KO $TEXT -s .data $DATA -s .bss $BSS" \
  -ex 'p/x &ramdump_test_snapshot' \
  -ex 'set $snap=(char*)&ramdump_test_snapshot' \
  -ex 'x/96bx $snap' \
  -ex 'x/16cb $snap+44' \
  -ex 'x/16cb $snap+60' \
  -ex 'x/16cb $snap+76'
```

이 dump에서 다음을 확인할 수 있어야 합니다.

- `magic == 0x52414d44` ("RAMD")
- `version == 1`
- `video_nr == 42`
- `pid`와 `comm`이 panic 프로세스와 일치 (예: `sh`)
- `trigger == "panic"`
- `marker == "RAMDUMP_TEST"`

