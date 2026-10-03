---
name: gui-key-injection-focus-risk
description: 이 PC(7make)에서 PasteFlow 키 주입 테스트 시 포커스가 원격 데스크톱 창으로 넘어가 입력이 새는 위험
metadata:
  node_type: memory
  type: feedback
  originSessionId: 3e735556-2949-4523-8509-6a36918a7e4f
  modified: 2026-10-03T07:01:48.598Z
---

이 PC(사용자 7make, 3모니터)에는 다른 Claude 세션·Chrome for Testing 자동화·Chrome 원격 데스크톱("송출센터 멀티뷰 감시", 원격 PC의 KBS On-Air Monitoring + Claude Code)이 동시에 떠 있어 포그라운드가 수시로 바뀐다. 2026-10-03 점검 중 메모장에 보낸 Ctrl+V·Enter가 원격 데스크톱 창으로 들어갔을 수 있었다.

**Why:** SendInput은 "지금 앞에 있는 창"으로 가므로, 원격 창이 앞이면 원격 PC(방송 감시 앱 포함)에 입력이 들어간다.

**How to apply:** PasteFlow 실기 키 주입 테스트는 ① 매 키 전송 직전에 포그라운드가 대상 창(PID)인지 확인하고 아니면 중단, ② Enter 같은 확정 키는 쓰지 않거나, ③ 사용자에게 다른 창을 잠시 최소화해 달라고 먼저 부탁한다.
