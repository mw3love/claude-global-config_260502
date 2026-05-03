# Claude Code 전역 설정

여러 PC에서 동일한 Claude Code 환경을 유지하기 위한 전역 설정 저장소.

## 기능

- **bypass 모드 자동 진입** — `claude` 실행 시 `--dangerously-skip-permissions` 자동 적용 (settings.json)
- **Windows toast 알림** — Claude 답변 완료 시 알림 및 소리
- **draft 스킬** — `/draft` 명령으로 KBS 기안문 작성

---

## 새 PC 온보딩

### 경우 1: Claude Code를 처음 쓰는 PC (기존 `~/.claude` 폴더 없음)

```powershell
# 설정 파일 전체를 ~/.claude 폴더로 받아옴
git clone https://github.com/mw3love/claude-global-config_260502.git $env:USERPROFILE\.claude

# (선택) 변경 이력 자동 기록 훅 설치
Copy-Item "$env:USERPROFILE\.claude\setup\hooks\post-commit" "$env:USERPROFILE\.claude\.git\hooks\post-commit"
```

끝. 이후 `claude` 명령 실행 시 자동으로 설정이 적용됩니다.

---

### 경우 2: 이미 Claude Code를 사용 중인 PC (기존 `~/.claude` 폴더 있음)

> ⚠️ 기존 `settings.json`, `toast.ps1` 등은 이 레포 버전으로 **덮어씌워집니다.**
> 세션 기록, 대화 내용 등은 건드리지 않습니다.

```powershell
# 기존 ~/.claude 폴더를 git 저장소로 초기화
git -C $env:USERPROFILE\.claude init

# 이 레포를 원격 저장소로 연결
git -C $env:USERPROFILE\.claude remote add origin https://github.com/mw3love/claude-global-config_260502.git

# 레포 내용 가져오기
git -C $env:USERPROFILE\.claude fetch origin main

# 레포 버전으로 덮어쓰기 (기존 설정 파일 교체됨)
git -C $env:USERPROFILE\.claude checkout -f main

# (선택) 변경 이력 자동 기록 훅 설치
Copy-Item "$env:USERPROFILE\.claude\setup\hooks\post-commit" "$env:USERPROFILE\.claude\.git\hooks\post-commit"
```

---

## 설정 변경 후 동기화

이 PC에서 설정을 바꿨다면 다른 PC에도 반영하는 방법입니다.

```powershell
# 변경사항 저장 및 GitHub에 올리기
git -C $env:USERPROFILE\.claude add -A
git -C $env:USERPROFILE\.claude commit -m "변경 내용 설명"
git -C $env:USERPROFILE\.claude push
```

```powershell
# 다른 PC에서 최신 설정 받아오기
git -C $env:USERPROFILE\.claude pull
```

---

## 파일 구조

```
~/.claude/
├── setup/
│   └── hooks/
│       └── post-commit    # 커밋 시 변경 이력 자동 기록
├── settings.json          # bypass 모드 + Stop 훅(toast) + playwright
├── toast.ps1              # Windows toast 알림 스크립트
├── CLAUDE.md              # 전역 응답 원칙
└── skills/
    └── draft/             # KBS 기안문 작성 스킬
```

---

## 변경 이력

| 날짜 | PC | 커밋 메시지 |
|------|----|------------|
| 2026-05-03 | Home-Desktop | feat: draft 규칙 파일 전역 관리로 이동 |
| 2026-05-02 | Home-Desktop | docs: README 온보딩 안내 보강 (기존 PC 케이스 추가) |
