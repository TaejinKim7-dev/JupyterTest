# v4l2loopback snapshot vmcore archive

이 디렉터리는 `v4l2loopback` snapshot panic 실험의 대용량 산출물을 GitHub에서 복원 가능하도록 분할 압축한 보관소다.

원본 결과 디렉터리:

`/home/taejin/Jupyter/data/aosp-lab/ramdump-results/v4l2loopback-snapshot-vmcore-20260502-221716`

포함 대상:

- `vmcore.elf`
- `vmlinux`
- `vmlinux.uncompressed`
- `bzImage`
- `v4l2loopback_snapshot.ko`
- `vendor_ramdisk_6.12.77.img`
- `kernel.log`
- `launcher.log`
- `logcat`
- `qmp_transcript_paging_true.log`
- `gdb_snapshot_check.txt`
- `gdb_snapshot_dump.txt`
- `gdb_snapshot_bytes.txt`
- `module_sections.txt`

복원 예시:

```bash
7z x v4l2loopback-snapshot-vmcore-20260502-221716.7z.001
```

압축 파일은 같은 디렉터리의 `.7z.001`, `.7z.002` ... 형식으로 저장된다.

