---
name: project-telegram-stop-hook-notify
description: PC별 Stop 훅 텔레그램 알림(telegram.json) 설정 현황 — 2026-09-01 기준
metadata: 
  node_type: memory
  type: project
  originSessionId: 0e05c84e-d662-4d13-bd35-011d354bdd2d
  modified: 2026-09-01T01:22:25.174Z
---

**Minwoo-Samsung-Laptop**(이 PC): `~/.claude/telegram.json`에 Notifier bot(`mw_claude_notifier_bot`) 토큰 + `chat_id 6814671341` 설정 완료. 2026-09-01 실조건검증(사용자가 폰 수신 확인)까지 마침. `toast.sh`→`toast.ps1`이 매 응답 완료(`Stop` 훅) 시 텔레그램으로도 알림을 보낸다.

**Why:** `telegram.json`은 `.gitignore` 대상이라 PC마다 따로 만들어야 한다(git sync로 안 넘어감). [[feedback-notification-design]]에 따르면 이 알림 디스패처(`toast.ps1`의 Telegram 발송 로직) 자체는 2026-07-22부터 존재했으나, 이 PC엔 파일이 없어 꺼져 있었을 뿐이었다.

**How to apply:** 다른 PC(HOME-DESKTOP·MW-Lenovo 등)에서 같은 요청을 받으면 그 PC에 `~/.claude/telegram.json`이 이미 있는지부터 확인 — 없으면 이 PC와 같은 절차([[reference-telegram-bot-tokens]] 폴더에서 Notifier bot 토큰 재사용)로 만든다. 있으면 이미 되는 것이니 새로 만들지 않는다.
