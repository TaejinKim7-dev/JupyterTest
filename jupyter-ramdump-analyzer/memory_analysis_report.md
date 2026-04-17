# Memory Dump Analysis Report

## 기본 정보

| 항목 | 값 |
|-------|-----|
| 파일 | data/memory/memory.vmem |
| 크기 | 4.00 GB (4,294,967,296 bytes) |
| 타입 | Linux Memory Dump (x86_64) |
| 발견된 Process | systemd, nginx, apache, bash |

---

## 발견된 항목

### 프로세스/서비스
- systemd (활성)
- nginx (활성)
- apache (활성)
- bash (활성)
- python (가능)

### 에러 빈도수
| 에러 유형 | 횟수 |
|----------|------|
| error | 358회 |
| Error | 450회 |
| failed | 46회 |
| Failed | 53회 |

### 발견된 URLs
- https://floor.pbxai.com
- https://accounts.google.com/gsi/iframe/select
- https://sdk.minutemedia-prebid.com
- https://sync.kueezrtb.com
- https://www.cnet.com
- https://fonts.gstatic.com
- https://www.redditstatic.com/shreddit
- https://cdn.confiant-integrations.net

### 사용자
- woreilly (uid=1000)
- syslog

---

## 분석 필요 사항

1. 에러 빈도수가 높음 (358+450회) - 원인은?
2. 외부 URLs 중 의심스러운 요청 있는지
3. 사용자 "woreilly"의 활동 패턴
4. 추가 메모리 오류 (OOM 등) 확인 필요
