# Claude Code 전역 설정

여러 PC에서 동일한 Claude Code 환경을 유지하기 위한 전역 설정 저장소.

## 기능

- **bypass 모드 자동 진입** — PowerShell / CMD / Git Bash에서 `claude` 입력 시 `--dangerously-skip-permissions` 자동 적용
- **Windows toast 알림** — Claude 답변 완료 시 알림 표시
- **draft 스킬** — `/draft` 명령으로 KBS 기안문 작성

## 새 PC 온보딩

새 PC / 기존 Claude Code 사용 PC 구분 없이 아래 한 줄로 완료:

```powershell
irm https://raw.githubusercontent.com/mw3love/claude-global-config_260502/main/setup.ps1 | iex
```

> `~/.claude`가 없으면 clone, 있으면 pull로 자동 처리됩니다.

## 동기화

```powershell
# 이 PC에서 변경 후
git -C ~/.claude add -A
git -C ~/.claude commit -m "변경 내용"
git -C ~/.claude push

# 다른 PC에서 최신화
git -C ~/.claude pull
```

## 파일 구조

```
~/.claude/
├── setup.ps1              # 새 PC 온보딩 진입점
├── setup/
│   ├── install.ps1        # bypass 별명 + 훅 설치
│   ├── profile.ps1        # PowerShell 프로필
│   ├── claude.cmd         # CMD 래퍼
│   ├── bashrc_snippet.sh  # Git Bash 설정
│   └── hooks/
│       └── post-commit    # README 변경 이력 자동 기록
├── settings.json          # Stop 훅(toast) + playwright
├── toast.ps1              # Windows toast 알림 스크립트
├── CLAUDE.md              # 전역 응답 원칙
└── skills/
    └── draft/             # KBS 기안문 작성 스킬
```

## 변경 이력

| 날짜 | PC | 커밋 메시지 |
|------|----|------------|
| 2026-05-02 | Home-Desktop | refactor: setup.ps1 단일 진입점으로 개선 (irm / iex 지원) |
| 2026-05-02 | Home-Desktop | fix: Stop 훅에 shell:powershell 명시 ($env:USERPROFILE 확장 오류 수정) |
| 2026-05-02 | Home-Desktop | fix: toast 알림 소리 추가 (audio 태그) |
| 2026-05-02 | Home-Desktop | docs: README 추가 및 post-commit 훅 설정 |
