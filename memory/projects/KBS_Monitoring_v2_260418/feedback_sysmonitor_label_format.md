---
name: SysMonitorWidget 레이블 2줄 형식 유지
description: top_bar.py SysMonitorWidget의 CPU/RAM/GPU 레이블은 2줄 형식 유지 — 단일행 시도 후 사용자가 되돌림
type: feedback
originSessionId: 29b2b35c-8cf9-464f-b283-1274f0cd937b
---
"CPU\n45%" 형식(2줄)을 유지할 것. 단일행("CPU  45%")으로 변경 시도했으나 사용자가 "별로"라고 판단하고 원복 요청.

**Why:** 2줄이 시각적으로 더 잘 읽힘 (레이블과 값이 세로 분리).

**How to apply:** top_bar.py SysMonitorWidget._setup_ui 및 _update_stats에서 레이블 형식 변경 제안 금지.
