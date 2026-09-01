---
name: reference-telegram-bot-tokens
description: "텔레그램 봇 토큰 저장 위치(Google Drive)와 봇별 용도 구분(Notifier=알림, Telegram=양방향 채널)"
metadata: 
  node_type: memory
  type: reference
  originSessionId: 0e05c84e-d662-4d13-bd35-011d354bdd2d
  modified: 2026-09-01T01:22:20.804Z
---

봇 토큰 원본은 Google Drive `G:\내 드라이브\1. 개인 자료\A1. AI 연습\260221 ★ Telegram Bot 모음\`에 봇별 `.txt` 파일로 저장돼 있다.

- `260520 Claude Notifier bot.txt` — 봇 `mw_claude_notifier_bot`. **용도: Stop 훅 답변완료 알림**(`~/.claude/telegram.json`이 이 토큰을 씀). [[feedback-notification-design]] 참고.
- `260520 Claude Telegram bot.txt` — 봇 `mw_claude_telegram_bot`. **용도: 양방향 대화**(`telegram` 플러그인 채널, `~/.claude/channels/telegram/.env`). ※ 2026-09-01 확인 시 Minwoo-Samsung-Laptop의 `.env` 토큰은 이 파일과 불일치 — 플러그인이 세 번째 봇으로 설정돼 있었음. 재설정할 땐 재확인할 것.
- 두 봇 모두 `chat_id`(=텔레그램 유저 ID) `6814671341`을 공용으로 쓸 수 있다(같은 사람이지만, 봇마다 유저가 먼저 그 봇에게 메시지를 한 번 보낸 적이 있어야 봇이 먼저 알림을 보낼 수 있음).

**적용:** 텔레그램 알림·채널 관련 요청을 받으면 토큰을 사용자에게 되묻기 전에 이 폴더부터 확인한다.
