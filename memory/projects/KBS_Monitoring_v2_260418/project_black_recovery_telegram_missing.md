---
name: project_black_recovery_telegram_missing
description: "블랙 진입 알림은 나가는데 복구 알림이 누락되는 버그. 확정·미해결, 다음 재발 관측 대기."
metadata: 
  node_type: memory
  type: project
  originSessionId: efd7edb7-ae82-4f8e-a4ba-65cfd1db0907
  modified: 2026-07-20T00:49:55.803Z
---

블랙 **진입** 텔레그램은 정상 발송되는데 **복구** 텔레그램이 안 나가는 사례 확정(2026-07-19 V7 모악2UHD, 2026-07-18 V5~V8). 사용자가 실제 복구를 육안 확인 → "블랙 안 풀림"이 아니라 **진짜 누락 버그**.

전송실패·정파억제·재spawn·큐드롭·rate-limit 전부 로그로 배제됨 → `processes/detection_process.py` `_process_alarms` 복구 분기(`elif not alerting and was:`) 발화 실패 또는 `telegram.notify(is_recovery=True)` 미인입으로 좁혀짐.

**계측 공백**: AlarmResolve·복구분기 판정이 어느 로그 파일에도 안 남아(화면 위젯에만) 로그로 더 못 팜. → **진단 로깅(`DIAG-복구추적`)을 v2.8.1에 반영해 2026-07-20 push함**(로직 무변경). 운영 PC에 배포(git pull+재시작) 후 재발 시 UI 로그에서 `grep DIAG-복구추적`으로 root-cause. 상세·판독법: `fix/260720_블랙복구_텔레그램_누락.md`.

7/18(캡처상실 8채널)과 7/19(단일 V7)는 다른 원인일 수 있음 — 로깅으로 분리 확인.
