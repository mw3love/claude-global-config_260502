# Claude Code 전역 설정

여러 PC에서 동일한 Claude Code 환경을 유지하기 위한 전역 설정 저장소.

## 기능

- **bypass 모드 자동 진입** — `defaultMode: bypassPermissions` (settings.json)
- **Windows toast 알림** — Claude 답변 완료 시 알림 및 소리
- **statusline** — 모델명 / 컨텍스트 사용률 / 5시간·7일 레이트리밋을 터미널 상태바에 표시
- **플러그인 마켓플레이스** — `claude-plugins-official`, `anthropic-agent-skills` 등록
- **document-skills 플러그인** — `anthropic-agent-skills` 마켓플레이스에서 활성화
- **draft 스킬** — `/draft` 명령으로 KBS 기안문 작성

---

## 새 PC 온보딩

### 경우 1: Claude Code를 처음 쓰는 PC (기존 `~/.claude` 폴더 없음)

```powershell
git clone https://github.com/mw3love/claude-global-config_260502.git $env:USERPROFILE\.claude

# 훅 설치 (post-commit: 변경 이력 자동 기록 / post-merge: statusLine 경로 자동 교체)
Copy-Item "$env:USERPROFILE\.claude\setup\hooks\post-commit" "$env:USERPROFILE\.claude\.git\hooks\post-commit"
Copy-Item "$env:USERPROFILE\.claude\setup\hooks\post-merge"  "$env:USERPROFILE\.claude\.git\hooks\post-merge"

# 훅 설치 확인 (post-commit, post-merge 두 파일이 보여야 함)
Get-ChildItem "$env:USERPROFILE\.claude\.git\hooks\" | Where-Object { $_.Name -notlike "*.sample" }
```

---

### 경우 2: 이미 Claude Code를 사용 중인 PC (기존 `~/.claude` 폴더 있음)

> ⚠️ 기존 `settings.json`, `toast.ps1`, `statusline.ps1` 등은 이 레포 버전으로 **덮어씌워집니다.**
> 세션 기록, 대화 내용, `plugins/`, `cache/` 등 런타임 데이터는 건드리지 않습니다.

```powershell
# 기존 .git 제거 후 이 레포로 재연결
Remove-Item "$env:USERPROFILE\.claude\.git" -Recurse -Force

git -C $env:USERPROFILE\.claude init
git -C $env:USERPROFILE\.claude remote add origin https://github.com/mw3love/claude-global-config_260502.git
git -C $env:USERPROFILE\.claude fetch origin
git -C $env:USERPROFILE\.claude reset --hard origin/main
git -C $env:USERPROFILE\.claude branch -m master main
git -C $env:USERPROFILE\.claude branch --set-upstream-to=origin/main main

# 훅 설치 (post-commit: 변경 이력 자동 기록 / post-merge: statusLine 경로 자동 교체)
Copy-Item "$env:USERPROFILE\.claude\setup\hooks\post-commit" "$env:USERPROFILE\.claude\.git\hooks\post-commit"
Copy-Item "$env:USERPROFILE\.claude\setup\hooks\post-merge"  "$env:USERPROFILE\.claude\.git\hooks\post-merge"

# 훅 설치 확인 (post-commit, post-merge 두 파일이 보여야 함)
Get-ChildItem "$env:USERPROFILE\.claude\.git\hooks\" | Where-Object { $_.Name -notlike "*.sample" }
```

---

## 훅 없이 pull한 경우 수동 복구

`git pull` 전에 훅을 설치하지 않았다면 statusLine 경로가 다른 PC의 사용자명으로 남아 있을 수 있습니다.

```powershell
# 1. 훅 재설치
Copy-Item "$env:USERPROFILE\.claude\setup\hooks\post-commit" "$env:USERPROFILE\.claude\.git\hooks\post-commit" -Force
Copy-Item "$env:USERPROFILE\.claude\setup\hooks\post-merge"  "$env:USERPROFILE\.claude\.git\hooks\post-merge"  -Force

# 2. post-merge 훅 수동 실행 (경로 자동 교체)
bash "$env:USERPROFILE\.claude\.git\hooks\post-merge"

# 3. Claude Code 재시작
```

> ⚠️ `post-merge` 훅은 settings.json의 `statusLine.command` 경로가 `C:\Users\<이름>\` 형식일 때만 자동 교체합니다.
> `%USERPROFILE%` 형식으로 되어 있으면 훅이 인식하지 못하므로, 반드시 절대경로 형식을 유지해야 합니다.

---

## 설정 변경 후 동기화

```powershell
# 변경사항 저장 및 GitHub에 올리기
git -C $env:USERPROFILE\.claude add -A
git -C $env:USERPROFILE\.claude commit -m "변경 내용 설명"
git -C $env:USERPROFILE\.claude push

# 다른 PC에서 최신 설정 받아오기
git -C $env:USERPROFILE\.claude pull
```

---


## 파일 구조

```
~/.claude/
├── setup/
│   └── hooks/
│       ├── post-commit       # 커밋 시 변경 이력 자동 기록
│       └── post-merge        # pull 후 statusLine 경로 자동 교체
├── skills/
│   └── draft/                # KBS 기안문 작성 스킬
├── settings.json             # 전역 설정 (bypass, hooks, statusLine, 마켓플레이스)
├── statusline.ps1            # 터미널 상태바 스크립트
├── toast.ps1                 # Windows toast 알림 스크립트
└── CLAUDE.md                 # 전역 응답 원칙
```

---

## 변경 이력

| 날짜 | PC | 커밋 메시지 |
|------|----|------------|
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
