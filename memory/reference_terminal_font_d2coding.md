---
name: reference-terminal-font-d2coding
description: "터미널 한글 깨짐의 원인은 폰트 폴백 — HOME-DESKTOP·MW-Lenovo·MOAK-MINWOO·MW-Samsung26 모두 D2Coding 적용 완료"
metadata: 
  node_type: memory
  type: project
  originSessionId: 166d242f-05d9-4203-8e52-62303f19e93d
  modified: 2026-09-04T05:45:55.143Z
---

Windows Terminal에 폰트 지정이 없으면 기본 `Cascadia Mono`가 쓰이는데 여기엔 한글 글리프가 0개라, 가변폭 `맑은 고딕`으로 폴백되어 한글 행의 폭이 ASCII 행과 어긋난다. 질문창(`AskUserQuestion`)처럼 테두리 박스 + 매 키 입력 재렌더인 UI에서만 이게 눈에 띈다.

**2026-08-09 HOME-DESKTOP 조치 완료** — `naver/d2-coding-font` VER1.3.3을 사용자 범위로 설치(`%LOCALAPPDATA%\Microsoft\Windows\Fonts` + HKCU `...\CurrentVersion\Fonts` 등록 + `WM_FONTCHANGE` 브로드캐스트, 관리자 권한 불필요)하고 WT `settings.json`의 `profiles.defaults.font.face`를 `D2Coding`으로 지정. 백업은 같은 폴더 `settings.json.bak-20260809`. 재시작 없이 즉시 적용됐고, 한글/ASCII 테두리 정렬은 캡처 확대로 실조건검증함.

**2026-08-10 MW-Lenovo 조치 완료** — 같은 절차 반복(회사 PC). `api.github.com/repos/.../releases/latest`가 그 시점에 IP 레이트리밋에 걸려, 대신 `github.com/naver/d2-coding-font/archive/refs/tags/VER1.3.3.zip`(codeload, API 아님)로 소스 아카이브를 받아 `fonts/ttf/D2Coding-{Regular,Bold}.ttf`만 설치(ligature 변형은 제외). README 스니펫엔 `WM_FONTCHANGE` 브로드캐스트가 누락돼 있어(이 메모리엔 있었는데 README로 옮겨적을 때 빠짐) README도 함께 보완. 한글 8자행·ASCII 16자행 테두리 정렬을 새 WT 창 캡처로 실조건검증함(픽셀 단위로 `|`·`+` 우측 정렬 확인).

**2026-08-11 MOAK-MINWOO 조치 완료** — 새 PC(기존 두 대와 별개 호스트명)라 세 번째 대상이었음. 같은 codeload 절차로 설치, WT `settings.json`의 `profiles.defaults`가 원래 빈 객체(`{}`)라 `font.face`만 추가. 전체화면 캡처로 이미 열려있던 다른 WT 창들의 한글 정렬이 즉시 고정폭으로 바뀐 것을 실조건검증함(재시작 없이 반영).

⚠ **함정: `Get-Process WindowsTerminal | Stop-Process -Force`로 검증용 창을 정리하려다 사용자가 보고 있던 실제 창까지 전부 죽음** — WT는 창마다 별도 프로세스가 아니라 단일 프로세스(모나크/피어전트 구조)라 "테스트 창만 골라 죽이기"가 프로세스 단위로는 불가능하다. 새 창 검증이 필요하면 기존 프로세스를 절대 죽이지 말고, `-w new`로 새 창을 띄운 뒤 `Get-Process`가 새로 보고하는 `MainWindowHandle`만 골라 캡처하고, 남은 테스트 탭은 사용자가 직접 닫게 안내한다.

폰트로 해결되지 **않는** 잔여 문제: 컬러 이모지는 셀보다 크게 렌더돼 박스 테두리를 덮고, `✓✗⚠→`는 폴백에서 1칸 폭으로 그려진다. 이건 전역 `CLAUDE.md`의 이모지 규약(테두리 안 금지)으로 회피한다.

⚠ **폰트로도 안 풀리는 별도 버그 있음** — 글자가 다른 글자로 바뀌는 증상(정렬 어긋남이 아니라)이면 이 파일이 아니라 [[reference-claude-code-cjk-encoding-bug]] 참고. Claude Code 자체의 미해결 Windows 인코딩 버그라 여기 절차로는 안 고쳐진다(2026-08-10 확인).

**2026-09-04 MW-Samsung26 조치 완료** — 새 PC 온보딩 점검 중 발견(폰트 미설치, WT `profiles.defaults` 비어있음). 같은 codeload 절차로 설치, `profiles.defaults`가 빈 객체(`{}`)라 `font.face`만 추가(MOAK-MINWOO와 동일 패턴). 실행 중인 PowerShell 도구가 `-NoProfile`이라 새 창 캡처로 실조건검증은 못 했음(폰트 파일·레지스트리 등록·WT 설정 반영 자체는 확인) — 사용자가 다음에 새 터미널을 열 때 육안 확인 필요.

관련: [[feedback-answer-shape]], [[feedback-askuserquestion-preference]], [[reference-claude-code-cjk-encoding-bug]]
