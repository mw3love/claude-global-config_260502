# Claude Code 전역 설정

여러 PC에서 동일한 Claude Code 환경을 유지하기 위한 전역 설정 저장소.

## 사전 요건

- **Windows + PowerShell** (Windows PowerShell 5.1 또는 PowerShell 7)
- **Git for Windows (Git Bash 포함)** — 필수. statusLine 명령이 `bash -c '...'` 래퍼를 사용하기 때문 (라우팅 비결정성 우회).
- **Bun** — Telegram 채널 플러그인 실행용. post-merge hook이 자동 설치하므로 수동 설치 불필요.

## 기능

- **bypass 모드 자동 진입** — `defaultMode: bypassPermissions` (settings.json)
- **Windows toast 알림 + Telegram 발송** — Claude 답변 완료, 질문 대기, 입력 대기 시점에 PC와 폰 양쪽 알림
- **Telegram 채널 (비상용 원격)** — `ctg` 명령으로 활성 (lock 파일로 한 번에 한 세션만). `claude`는 로컬 전용.
- **statusline** — 모델명 / 컨텍스트 사용률 / 5시간·7일 레이트리밋을 터미널 상태바에 표시
- **플러그인 마켓플레이스** — `claude-plugins-official`, `anthropic-agent-skills` 등록
- **document-skills, telegram 플러그인** 활성화
- **draft 스킬** — `/draft` 명령으로 KBS 기안문 작성
- **post-merge hook** — `git pull` 후 환경 자동 점검·복구 (Bun 설치, $PROFILE 갱신, 플러그인 다운로드)

---

## 새 PC 온보딩

### 경우 1: Claude Code를 처음 쓰는 PC (기존 `~/.claude` 폴더 없음)

```powershell
git clone https://github.com/mw3love/claude-global-config_260502.git $env:USERPROFILE\.claude

# core.hooksPath 설정 (한 번만 — 커밋·풀 훅 자동 실행)
git -C $env:USERPROFILE\.claude config core.hooksPath setup/hooks

# post-merge hook 첫 실행 (Bun 설치 + $PROFILE 갱신 + 플러그인 다운로드 자동)
bash $env:USERPROFILE\.claude\setup\hooks\post-merge

# 봇 토큰만 직접 입력 (PC당 1회, 시크릿이라 자동 불가)
Set-Content "$env:USERPROFILE\.claude\channels\telegram\.env" "TELEGRAM_BOT_TOKEN=<봇 토큰>"

# 끝. 새 PowerShell에서 `claude` (로컬) 또는 `ctg` (텔레그램 채널) 입력
```

> BotFather에서 새 봇 만들거나 기존 봇 토큰 재사용. **두 PC가 같은 봇을 동시에 폴링하면 충돌**하니 PC 사용은 순차적으로.

---

### 경우 2: 이미 Claude Code를 사용 중인 PC (기존 `~/.claude` 폴더 있음)

> ⚠️ 기존 `settings.json`, `toast.ps1`, `statusline.ps1` 등은 이 레포 버전으로 **덮어씌워집니다.**
> 세션 기록, 대화 내용, `plugins/cache/`, `cache/` 등 런타임 데이터는 건드리지 않습니다.

```powershell
# 기존 .git 제거 후 이 레포로 재연결
Remove-Item "$env:USERPROFILE\.claude\.git" -Recurse -Force

git -C $env:USERPROFILE\.claude init
git -C $env:USERPROFILE\.claude remote add origin https://github.com/mw3love/claude-global-config_260502.git
git -C $env:USERPROFILE\.claude fetch origin
git -C $env:USERPROFILE\.claude reset --hard origin/main
git -C $env:USERPROFILE\.claude branch -m master main
git -C $env:USERPROFILE\.claude branch --set-upstream-to=origin/main main

# core.hooksPath 설정 (한 번만)
git -C $env:USERPROFILE\.claude config core.hooksPath setup/hooks

# post-merge hook 첫 실행
bash $env:USERPROFILE\.claude\setup\hooks\post-merge

# 봇 토큰 (PC당 1회)
Set-Content "$env:USERPROFILE\.claude\channels\telegram\.env" "TELEGRAM_BOT_TOKEN=<봇 토큰>"
```

---

## 설정 변경 후 동기화

```powershell
# 변경사항 저장 및 GitHub에 올리기
git -C $env:USERPROFILE\.claude add -A
git -C $env:USERPROFILE\.claude commit -m "변경 내용 설명"
git -C $env:USERPROFILE\.claude push

# 다른 PC에서 최신 설정 받아오기 — post-merge hook이 환경 자동 점검
git -C $env:USERPROFILE\.claude pull
```

> 기존 PC에서 pull 시: Bun·플러그인·`$PROFILE` 등이 이미 갖춰져 있으면 hook이 무동작으로 끝나고 `✅ 모두 정상` 메시지만 출력.

---


## 파일 구조

```
~/.claude/
├── setup/
│   ├── hooks/
│   │   ├── post-commit       # 커밋 시 변경 이력 자동 기록
│   │   └── post-merge        # pull 후 환경 자동 점검 (Bun, $PROFILE, 플러그인)
│   └── profile.ps1           # PowerShell 프로필 — Bun PATH 보정 + claude (로컬) / ctg (텔레그램) 함수
├── skills/
│   └── draft/                # KBS 기안문 작성 스킬
├── channels/
│   └── telegram/
│       ├── .env              # 봇 토큰 (gitignore, PC별 수동)
│       ├── access.json       # 페어링·allowlist (git 동기화)
│       └── approved/         # 승인된 sender (gitignore, 런타임)
├── settings.json             # 전역 설정 (bypass, hooks, statusLine, 마켓플레이스, 채널 활성)
│                              #   ⚠ statusLine 명령은 `bash -c '...'` 래퍼 형태 유지 (Git Bash 필요).
│                              #     단순화하면 cmd 라우팅 PC에서 silent fail.
├── statusline.ps1            # 터미널 상태바 스크립트
├── toast.ps1                 # Windows toast + Telegram 발송 스크립트
├── telegram.json             # 알림용 봇 토큰 (gitignore, PC별 수동)
└── CLAUDE.md                 # 전역 응답 원칙
```

---

## 변경 이력

| 날짜 | PC | 커밋 메시지 |
|------|----|------------|
| 2026-05-23 | Home-Desktop | feat: deep-interview 전역 스킬 추가 |
| 2026-05-23 | Home-Desktop | feat: git push 후 자동 문서 동기화 (doc-sync hook + 스킬) |
| 2026-05-22 | moak-minwoo | merge: origin/main 병합 — statusLine bash 래퍼 채택, README 본문 ctg 분리 반영 |
| 2026-05-22 | MW-Lenovo | docs: draft 스킬 참조자료 추가 - 모악산(송) 삭도 비상제동장치 개선공사 |
| 2026-05-21 | Home-Desktop | feat: ExitPlanMode 알림 훅 추가 - 플랜 승인 대기 토스트 |
| 2026-05-21 | MW-Lenovo | fix: Notification 훅 제거 - "Input needed" 중복 토스트 차단 |
| 2026-05-21 | MW-Lenovo | refactor: claude는 로컬 전용, ctg로 텔레그램 분리 |
| 2026-05-20 | Home-Desktop | chore: claude 함수 안내 문구 자연화 — "다리" → "텔레그램 채널 활성" |
| 2026-05-20 | Home-Desktop | docs: README 보강 — 사전 요건 + statusLine 래퍼 주의 (Home-Desktop) |
| 2026-05-20 | Home-Desktop | fix: statusLine 명령을 bash -c 래퍼로 변경 (Home-Desktop) |
| 2026-05-20 | Home-Desktop | feat: pull 자동화 — post-merge hook + claude lock 함수 (Home-Desktop) |
| 2026-05-20 | Home-Desktop | feat: Telegram 채널 플러그인 활성화 (Home-Desktop) |
| 2026-05-20 | Home-N100 | chore: post-merge 훅 제거 — statusLine portable화로 불필요해진 죽은 코드 정리 |
| 2026-05-20 | Home-Desktop | feat: 질문/입력 알림 hook + Telegram 발송 + statusLine portable화 (Home-Desktop) |
| 2026-05-08 | moak-minwoo | chore: statusLine 경로 로컬 적용 (moak-minwoo) |
| 2026-05-08 | moak-minwoo | merge: origin/main 병합 — gitignore 충돌 해결, 변경 이력 통합 |
| 2026-05-08 | moak-minwoo | chore: chrome/, .last-cleanup를 .gitignore에 추가 |
| 2026-05-06 | Home-N100 | docs: 온보딩 훅 설치를 core.hooksPath 방식으로 전환, statusLine 경로 교체 |
| 2026-05-06 | Home-Desktop | fix: post-merge hook이 USERNAME 대신 USERPROFILE 경로 사용 |
| 2026-05-06 | Home-Desktop | feat: 전역 CLAUDE.md 작성 및 settings 업데이트 (Home-Desktop) |
| 2026-05-06 | MW-Lenovo | docs: 훅 설치 확인 및 수동 복구 절차 추가, statusLine 경로 절대경로로 수정 |
| 2026-05-05 | Home-Desktop | docs: 파일 구조에 post-merge hook 항목 추가 |
| 2026-05-05 | Home-Desktop | feat: post-merge hook 추가 (statusLine 경로 자동 교체) |
| 2026-05-05 | Home-Desktop | fix: statusLine 환경변수를 %USERPROFILE%로 변경 (cmd.exe 확장) |
| 2026-05-05 | Home-Desktop | fix: statusLine 단일따옴표 버그 수정 (Join-Path로 변수 확장 보장) |
| 2026-05-05 | Home-Desktop | fix: statusLine -File -> -Command으로 변경 (환경변수 자동 확장, PC 무관) |
| 2026-05-05 | Home-N100 | fix: statusLine 경로 이스케이핑 수정 (하드코딩 절대경로) |
| 2026-05-05 | Home-N100 | feat: statusline 추가 및 settings 병합 (마켓플레이스, document-skills) |
| 2026-05-05 | Home-N100 | git 연동 대상 변경: mw_ClaudeCode_Tempaltes_260422 → claude-global-config_260502 |
| 2026-05-03 | Home-Desktop | feat: draft 스킬 완전 전역화 |
| 2026-05-03 | Home-Desktop | feat: draft 규칙 파일 전역 관리로 이동 |
| 2026-05-02 | Home-Desktop | docs: README 온보딩 안내 보강 (기존 PC 케이스 추가) |
