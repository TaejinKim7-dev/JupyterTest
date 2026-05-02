# AOSP/Cuttlefish vmcore Debugging Status - 2026-05-02

## 목적

Jupyter 기반 ramdump 분석 도구의 다음 입력 형태를 검증하기 위해, AOSP/Cuttlefish 환경에서 의도적인 kernel panic을 만들고 `vmcore.elf`, `vmlinux`, 커널 로그를 함께 확보했다. 목표는 단순 문자열 기반 메모리 분석을 넘어서 panic 원인, CPU 레지스터, kernel stack, 구조체 내부 값을 확인할 수 있는 분석 경로를 만드는 것이다.

## 현재까지 완료한 작업

- AOSP `aosp_cf_x86_64_only_phone-trunk_staging-userdebug` 빌드를 완료했다.
- Cuttlefish를 WSL2/KVM 환경에서 `qemu_cli` VM manager로 실행 가능하게 만들었다.
- Android common kernel 쪽에서 `v4l2loopback.ko`를 별도 빌드했다.
- `v4l2loopback`에 테스트용 sysfs trigger를 추가했다.
- trigger 종류는 `warn`, `oops`, `panic`으로 구성했다.
- custom `bzImage`, custom vendor ramdisk, matching `vmlinux` 조합으로 Cuttlefish를 부팅했다.
- guest에서 수정된 `v4l2loopback_fault.ko`를 `insmod`로 로드하고 `/sys/devices/virtual/video4linux/video42/fault_trigger`를 확인했다.
- `echo panic > .../fault_trigger`로 의도적인 kernel panic을 발생시켰다.
- QEMU QMP `dump-guest-memory`로 `vmcore.elf`를 수집했다.
- `gdb`와 `crash`를 설치 후 `vmcore.elf` 분석 가능성을 확인했다.

## 확보한 핵심 산출물

로컬 결과 디렉터리:

```text
/home/taejin/Jupyter/data/aosp-lab/ramdump-results/v4l2loopback-panic-vmcore-20260502
```

주요 파일:

- `vmcore.elf`: QMP로 수집한 full guest memory ELF core
- `vmlinux`: 테스트 커널과 맞는 심볼 파일
- `vmlinux.uncompressed`: debug section 압축을 해제한 vmlinux
- `bzImage`: 테스트에 사용한 커널 이미지
- `v4l2loopback_fault.ko`: sysfs fault trigger가 추가된 테스트 모듈
- `kernel.log`: panic reason, call trace, KASLR offset이 포함된 커널 로그
- `gdb_panic_cpu_thread2.txt`: panic CPU로 보이는 LWP 2의 레지스터와 stack dump
- `gdb_threads_registers_stacks.txt`: 4개 vCPU/LWP 전체의 레지스터와 backtrace
- `analysis_notes.md`: 결과 디렉터리 내부 상세 분석 노트

위 산출물은 대용량 로컬 실험 데이터이므로 GitHub에는 올리지 않는다.

## 확인된 panic 경로

커널 로그 기준 call trace:

```text
v4l2loopback ramdump test: panic trigger on video42
Kernel panic - not syncing: v4l2loopback ramdump test: sysfs-triggered panic
CPU: 1 UID: 0 PID: 4293 Comm: sh
panic+0xf1/0x310
attr_store_fault_trigger+0xfd/0x110 [v4l2loopback]
dev_attr_store+0x25/0x50
sysfs_kf_write+0x47/0x60
kernfs_fop_write_iter+0x123/0x210
ksys_write+0x297/0x5b0
__x64_sys_write+0x1a/0x30
do_syscall_64+0x58/0xf0
entry_SYSCALL_64_after_hwframe+0x76/0x7e
```

KASLR offset:

```text
Kernel Offset: 0x2b600000 from 0xffffffff81000000
```

따라서 runtime kernel address는 `runtime - 0x2b600000`으로 보정하면 `vmlinux` 심볼 주소와 매핑된다.

## gdb/crash 결과

`gdb`는 `vmcore.elf`를 열고 4개 LWP를 확인했다. 이는 4개 vCPU의 상태로 볼 수 있다. panic CPU로 보이는 `Thread 2 (LWP 2)`에서 다음 값을 확인했다.

```text
rip = 0xffffffffad9c443c
rsp = 0xffffabf5c44cbd20
rbp = 0xffffabf5c44cbd20
eflags = 0x246
```

stack dump에는 `panic`, `_printk`, `dev_attr_store`, `sysfs_kf_write`, `kernfs_fop_write_iter` 등으로 이어지는 주소가 남아 있었다. KASLR 보정 후 `llvm-addr2line`로 심볼 매핑이 가능했다.

`crash 8.0.0`은 현재 Android 6.12 계열 `vmcore.elf`와 `vmlinux` 조합에서 안정적으로 동작하지 않았다.

- 원본 `vmlinux`는 zstd 압축 debug section 때문에 debug data 인식에 문제가 있었다.
- `vmlinux.uncompressed`로 압축 해제 후에는 초기 로딩은 진행됐다.
- 하지만 `gathering kmem slab cache data` 단계에서 segfault가 발생했다.

따라서 현재 기본 분석 경로는 `gdb + kernel.log + KASLR 보정 + llvm-addr2line`로 잡는다. `crash`는 선택 경로 또는 추후 최신 버전 빌드 검토 대상으로 둔다.

## raw memory dump 필요성 판단

현재 목적이 panic 원인, CPU 레지스터, kernel stack, call trace, 구조체 값을 확인하는 것이라면 우선 입력은 `vmcore.elf + vmlinux + kernel.log + .ko`가 맞다.

`vmcore.elf`는 단순 레지스터 파일이 아니라 QEMU guest memory segment와 CPU 상태를 포함한 ELF core다. 따라서 구조체 내부 값을 확인하는 데 필요한 메모리 내용도 포함되어 있다.

`qemu.mem.raw` 같은 raw physical memory dump는 다음 경우에 보조적으로 필요하다.

- Volatility류 포렌식 분석
- 문자열/바이트 패턴 기반 스캔
- ELF vmcore가 깨졌을 때 fallback
- 물리 주소 중심 분석

하지만 커널 디버깅 관점에서는 raw dump만 있으면 레지스터, ELF note, 심볼 매핑, 가상주소 해석이 더 불편하다.

## 다음 단계

다음 실험은 구조체 내부 값을 안정적으로 확인하기 위한 snapshot 방식으로 진행한다.

테스트 모듈에 static/global snapshot 구조체를 추가한다.

```c
struct ramdump_test_snapshot {
    u32 magic;
    int video_nr;
    struct v4l2_loopback_device *dev;
    struct video_device *vdev;
    struct task_struct *task;
    pid_t pid;
    char comm[TASK_COMM_LEN];
    char marker[16];
};
```

panic 직전에 snapshot에 값을 저장한다.

```c
snapshot.magic = 0x52414d44;
snapshot.dev = dev;
snapshot.vdev = dev->vdev;
snapshot.task = current;
snapshot.pid = current->pid;
strscpy(snapshot.comm, current->comm, TASK_COMM_LEN);
strscpy(snapshot.marker, "RAMDUMP_TEST", sizeof(snapshot.marker));
panic("...");
```

이렇게 하면 두 가지 분석이 가능하다.

- `vmcore.elf + vmlinux + .ko`: `p snapshot`, `p *snapshot.dev`처럼 타입 기반 구조체 해석
- raw memory dump: `RAMDUMP_TEST`나 magic pattern으로 snapshot 위치 검색

## 도구 구현 방향

Jupyter 분석 도구에는 다음 입력 경로를 추가한다.

- `--vmcore`: QEMU/Kdump ELF core
- `--vmlinux`: matching vmlinux
- `--kernel-log`: panic log와 KASLR offset 추출용 로그
- `--module`: panic path에 포함된 `.ko` 심볼

초기 자동화 범위:

- kernel log에서 panic reason, CPU/PID/Comm, call trace 추출
- `Kernel Offset` 자동 파싱
- `gdb` batch로 vCPU별 register/stack dump 생성
- stack 내 kernel runtime address를 KASLR 보정 후 symbolization
- module frame은 `.ko` 심볼과 kernel log의 module frame을 함께 사용해 보정
- `crash` 실행은 optional로 두고 실패 시 gdb fallback 사용

## Git 관리 원칙

GitHub에는 코드, 문서, 작은 설정 파일만 올린다.

로컬에만 보관할 항목:

- AOSP source tree
- Android common kernel checkout
- Cuttlefish source/build tree
- `vmcore.elf`, `vmlinux`, `bzImage`, custom ramdisk, `.ko` 같은 빌드/덤프 산출물
- 대용량 로그 묶음

이 원칙에 맞춰 `.gitignore`에 `data/android-kernel/`, `android-cuttlefish/`, `data/aosp-lab/custom-ramdisks/`, `data/aosp-lab/ramdump-results/`를 제외 대상으로 추가했다.
