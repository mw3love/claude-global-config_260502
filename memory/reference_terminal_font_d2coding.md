---
name: reference-terminal-font-d2coding
description: "터미널 한글 깨짐의 원인은 폰트 폴백 — HOME-DESKTOP은 D2Coding 적용 완료, MW-Lenovo는 미적용"
metadata: 
  node_type: memory
  type: project
  originSessionId: 166d242f-05d9-4203-8e52-62303f19e93d
  modified: 2026-08-09T13:26:45.687Z
---

Windows Terminal에 폰트 지정이 없으면 기본 `Cascadia Mono`가 쓰이는데 여기엔 한글 글리프가 0개라, 가변폭 `맑은 고딕`으로 폴백되어 한글 행의 폭이 ASCII 행과 어긋난다. 질문창(`AskUserQuestion`)처럼 테두리 박스 + 매 키 입력 재렌더인 UI에서만 이게 눈에 띈다.

**2026-08-09 HOME-DESKTOP 조치 완료** — `naver/d2-coding-font` VER1.3.3을 사용자 범위로 설치(`%LOCALAPPDATA%\Microsoft\Windows\Fonts` + HKCU `...\CurrentVersion\Fonts` 등록 + `WM_FONTCHANGE` 브로드캐스트, 관리자 권한 불필요)하고 WT `settings.json`의 `profiles.defaults.font.face`를 `D2Coding`으로 지정. 백업은 같은 폴더 `settings.json.bak-20260809`. 재시작 없이 즉시 적용됐고, 한글/ASCII 테두리 정렬은 캡처 확대로 실조건검증함.

⚠ **MW-Lenovo는 아직 미적용** — 폰트 설치는 PC마다 따로 해야 한다. 같은 증상이 보이면 위 절차를 그대로 반복.

폰트로 해결되지 **않는** 잔여 문제: 컬러 이모지는 셀보다 크게 렌더돼 박스 테두리를 덮고, `✓✗⚠→`는 폴백에서 1칸 폭으로 그려진다. 이건 전역 `CLAUDE.md`의 이모지 규약(테두리 안 금지)으로 회피한다.

관련: [[feedback-answer-shape]], [[feedback-askuserquestion-preference]]
