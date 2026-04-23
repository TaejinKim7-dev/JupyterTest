# AOSP Userdebug Plan

기준 문서:

- Android build: https://source.android.com/docs/setup/build/building
- Android kernel build: https://source.android.com/setup/build/building-kernels
- Cuttlefish kernel development: https://source.android.com/docs/devices/cuttlefish/kernel-dev

## 추천 방향

현재 목표는 `adb root`, `panic trigger`, `pstore`, `vmlinux` 를 한 세트로 확보하는 것입니다. 이 목적에는 프리빌트 `google_apis` 이미지보다 `userdebug` 또는 `eng` 빌드가 맞습니다.

추천 우선순위:

1. AOSP `userdebug` emulator target 빌드
2. 필요 시 `eng` 변형으로 전환
3. 커널 수정이 필요하면 공통 커널 또는 Cuttlefish용 커널 빌드 추가

## 후보 타깃

공식 build 문서 예시는 다음 형태를 사용합니다.

```bash
lunch aosp_cf_x86_64_only_phone-aosp_current-userdebug
```

`cf` 는 Cuttlefish 계열 타깃입니다. emulator 실험이 목적이라면 먼저 이 계열 `userdebug` 타깃으로 가고, 실제로 어떤 lunch target 이 제공되는지는 checkout 후 `lunch` 목록으로 확정합니다.

## 필요한 산출물

케이스별로 아래를 보관합니다.

- `console-ramoops`
- `dmesg-ramoops`
- `vmlinux`
- `boot.img` 또는 커널 이미지 참조
- `lunch` target
- 커널 브랜치/manifest 정보
- panic 재현 절차
- 기대 root cause

## 기본 흐름

### 1. repo 설치

```bash
mkdir -p ~/bin
curl https://storage.googleapis.com/git-repo-downloads/repo > ~/bin/repo
chmod a+x ~/bin/repo
export PATH=~/bin:$PATH
```

### 2. AOSP checkout

```bash
cd /home/taejin/Jupyter/data/aosp-lab/source
repo init -u https://android.googlesource.com/platform/manifest -b android-latest-release
repo sync -c -j$(nproc)
```

### 3. build 환경 로드

```bash
cd /home/taejin/Jupyter/data/aosp-lab/source
source build/envsetup.sh
lunch aosp_cf_x86_64_only_phone-aosp_current-userdebug
m -j$(nproc)
```

### 4. emulator 실행 후 root 확인

```bash
adb root
adb shell id
```

### 5. panic 유도

```bash
adb shell 'echo c > /proc/sysrq-trigger'
```

### 6. pstore 수집

```bash
adb root
adb shell ls -la /sys/fs/pstore
adb pull /sys/fs/pstore /home/taejin/Jupyter/data/aosp-lab/artifacts/case-001/pstore
```

### 7. vmlinux 복사

`out/` 아래 실제 위치는 빌드 타깃과 커널 구성에 따라 달라질 수 있으므로, 빌드 후 `find out -name vmlinux` 로 확정합니다.

```bash
find out -name vmlinux
```

찾은 파일을 케이스 폴더나 `dist/` 로 복사합니다.

## 성공 기준

- `adb root` 가능
- panic 재현 가능
- 재부팅 후 `console-ramoops` 또는 동등한 pstore 로그 존재
- 대응하는 `vmlinux` 파일 확보
