# Android Emulator Lab

`data/android-emulator/` 는 프리빌트 Android emulator 기반 feasibility 실험용 디렉터리입니다.

## 현재 상태

- Android command-line tools 설치 완료
- `platform-tools`, `emulator`, `system-images;android-34;google_apis;x86_64` 설치 완료
- AVD `test_avd` 생성 완료
- WSL 환경에서 `/dev/kvm` 사용 가능 확인
- KVM enabled 부팅 후 `adb devices` 에서 `emulator-5554` 연결 성공

## 한계

- 프리빌트 `google_apis` 이미지에서는 `adb shell` 은 가능하지만 `/sys/fs/pstore` 접근은 권한 제한으로 실패
- `adb root` 기반 panic/pstore 실험에는 `userdebug` 또는 `eng` 이미지가 필요

## Git 관리 원칙

- `sdk/`, `downloads/`, `logs/` 는 대용량 또는 파생 산출물이므로 Git에서 제외
- 문서, 설정, 실험 메모만 Git에 반영

## 다음 단계

- `data/aosp-lab/` 기준으로 AOSP `userdebug/eng` build 진행
- panic 유도 후 `console-ramoops`, `dmesg-ramoops`, `vmlinux` 수집
