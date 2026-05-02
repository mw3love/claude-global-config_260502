# Claude Code 전역 설정

여러 PC에서 동일한 Claude Code 환경을 유지하기 위한 전역 설정 저장소.

## 기능

- **bypass 모드 자동 진입** — `claude` 실행 시 `--dangerously-skip-permissions` 자동 적용 (settings.json)
- **Windows toast 알림** — Claude 답변 완료 시 알림 및 소리
- **draft 스킬** — `/draft` 명령으로 KBS 기안문 작성

## 새 PC 온보딩

```powershell
# 1. 전역 설정 clone
git clone https://github.com/mw3love/claude-global-config_260502.git $env:USERPROFILE\.claude

# 2. 변경 이력 자동 기록 훅 설치 (선택)
Copy-Item "$env:USERPROFILE\.claude\setup\hooks\post-commit" "$env:USERPROFILE\.claude\.git\hooks\post-commit"
```

## 동기화

```powershell
# 이 PC에서 변경 후
git -C $env:USERPROFILE\.claude add -A
git -C $env:USERPROFILE\.claude commit -m "변경 내용"
git -C $env:USERPROFILE\.claude push

# 다른 PC에서 최신화
git -C $env:USERPROFILE\.claude pull
```

## 파일 구조

```
~/.claude/
├── setup/
│   └── hooks/
│       └── post-commit    # README 변경 이력 자동 기록
├── settings.json          # bypass 모드 + Stop 훅(toast) + playwright
├── toast.ps1              # Windows toast 알림 스크립트
├── CLAUDE.md              # 전역 응답 원칙
└── skills/
    └── draft/             # KBS 기안문 작성 스킬
```

## 변경 이력

| 날짜 | PC | 커밋 메시지 |
|------|----|------------|
