# Claude Code 전역 설정

여러 PC에서 동일한 Claude Code 환경을 유지하기 위한 전역 설정 저장소.

## 사전 요건

런타임(훅·statusLine·sync-repos)은 **Windows / macOS / Linux 크로스플랫폼**이다. 디스패처로 `bash`, 구현으로 `python3`(없으면 `.ps1` PowerShell 폴백)를 쓴다.

- **공통** — `bash` + `python3`. statusLine·훅 명령이 `bash -c '...'` 래퍼로 OS를 감지해 분기한다(라우팅 비결정성 우회).
- **Windows** — PowerShell 5.1/7 + Git for Windows(Git Bash 포함). python 있으면 사용, 없으면 `.ps1` 폴백.
- **macOS / Linux** — 기본 제공 `bash`·`python3`. 데스크톱 알림은 macOS `osascript`(+ `afplay` 소리) / Linux `notify-send`.
- **Bun** — Telegram 채널 플러그인 실행용. post-merge hook이 자동 설치(현재 온보딩 자동화는 Windows 기준 — macOS 온보딩 절차는 아직 미자동화).

## 기능

- **bypass 모드 자동 진입** — `defaultMode: bypassPermissions` (settings.json)
- **데스크톱 알림 + Telegram 발송** — Claude 답변 완료, 질문 대기, 입력 대기 시점에 PC와 폰 양쪽 알림 (Windows 활성 모니터 중앙 팝업 기본, 사람이 안 지켜보는 저빈도 자동화는 알림센터에 남는 우하단 토스트도 추가 / macOS osascript / Linux notify-send)
- **Telegram 채널 (비상용 원격)** — `tel` 명령으로 활성 (lock 파일로 한 번에 한 세션만). `claude`는 로컬 전용. (옛 이름 `ctg`도 별칭으로 동작)
- **statusline** — 폴더 / git 브랜치(미커밋 개수·GitHub 동기화 상태, fetch 없이 `@{upstream}` 캐시 비교 + 마지막 fetch 시각 절대표기(오늘이면 `HH:MM`, 아니면 `MM/DD HH:MM`)) / 모델명(`opusplan` 설정 시 `[opusplan]` 태그 병기) / 컨텍스트 사용률 / 5시간·7일 레이트리밋을 터미널 상태바에 표시
- **플러그인 마켓플레이스** — `claude-plugins-official`, `anthropic-agent-skills` 등록
- **document-skills, telegram 플러그인** 활성화
- **전역 스킬** — `/draft`(KBS 기안문), `/deep-interview`(요구사항 명확화 인터뷰), `/doc-sync`(푸쉬 전후 문서 동기화), `/self-review`(답변을 근거 기반으로 적대적 재검토), `/sync-repos`(여러 PC git 프로젝트를 명단 기반으로 일괄 pull+빌드), `/reference-repos`(비자명한 설계 전 비슷한 문제를 푼 기존 git repo를 찾아 참고(읽기) + 어렵게 뚫은 해법·재사용 기법을 묻지 말고 인덱스에 자동 기록(쓰기, CLAUDE.md 4-c) — 사용자 지목 우선 + `repos.json` 인덱스, 모자라면 GitHub 공개 API 라이브 스캔(gh 불요), remote로 PC 독립 접근), `/skillify`(세션에서 잘 통한 반복 절차를 재사용 스킬로 굳히기 — 품질 게이트 + memory(사실)와 경계), `design-bakeoff`(여러 AI 모델에게 같은 UI 디자인 과제를 시켜 한 Artifact에서 나란히 비교, 사용자 피드백으로 한 축씩 좁혀 최종 스펙으로 수렴 — 취향은 `design-system/`에 축적), `jbnu-gateway`(전북대 API Gateway로 이미지·비디오·TTS 생성 — "이미지/영상 만들어줘" 등에 자동 발동)
- **post-merge hook** — `git pull` 후 환경 자동 점검·복구 (Bun 설치, $PROFILE 갱신, 플러그인 다운로드, memory 연결)
- **pre-push doc-sync 게이트** — `git push` 전 doc-sync 사전 검토를 기계로 강제(PreToolUse 훅). 센티널(`.doc-sync-ready`, 1회용·30분 유효)이 없으면 push 자체가 거부됨
- **settings.json의 `model` 필드 git churn 차단** — `/model` 전환마다 `settings.json`(여러 PC 동기화 대상)이 dirty해지는 문제를 git clean 필터로 해결. 로컬 파일은 그대로 두고 git이 볼 때만 `model` 키를 제거(`.gitattributes` + PC별 로컬 `git config` 등록 필요 — 아래 온보딩 참조)
- **memory PC 간 공유** — 자동 memory를 `memory/`에 두고 git으로 동기화. `.claude` 자신은 정크션(post-merge hook), `repos.json`에 등록된 다른 프로젝트는 `autoMemoryDirectory`(SessionStart hook) (아래 "memory 동기화")

---

## 새 PC 온보딩

### 경우 1: Claude Code를 처음 쓰는 PC (기존 `~/.claude` 폴더 없음)

```powershell
git clone https://github.com/mw3love/claude-global-config_260502.git $env:USERPROFILE\.claude

# core.hooksPath 설정 (한 번만 — 풀 훅 자동 실행)
git -C $env:USERPROFILE\.claude config core.hooksPath setup/hooks

# post-merge hook 첫 실행 (Bun 설치 + $PROFILE 갱신 + 플러그인 다운로드 자동)
bash $env:USERPROFILE\.claude\setup\hooks\post-merge

# settings.json의 model 필드 git churn 차단 필터 등록 (PC당 1회, git config라 커밋 안 됨)
git -C $env:USERPROFILE\.claude config filter.modelstrip.clean 'python3 -S "$HOME/.claude/git-settings-model-filter.py" 2>/dev/null || python -S "$HOME/.claude/git-settings-model-filter.py"'
git -C $env:USERPROFILE\.claude config filter.modelstrip.smudge cat

# 봇 토큰만 직접 입력 (PC당 1회, 시크릿이라 자동 불가)
Set-Content "$env:USERPROFILE\.claude\channels\telegram\.env" "TELEGRAM_BOT_TOKEN=<봇 토큰>"

# 끝. 새 PowerShell에서 `claude` (로컬) 또는 `tel` (텔레그램 채널) 입력
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

# settings.json의 model 필드 git churn 차단 필터 등록 (PC당 1회, git config라 커밋 안 됨)
git -C $env:USERPROFILE\.claude config filter.modelstrip.clean 'python3 -S "$HOME/.claude/git-settings-model-filter.py" 2>/dev/null || python -S "$HOME/.claude/git-settings-model-filter.py"'
git -C $env:USERPROFILE\.claude config filter.modelstrip.smudge cat

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

## memory 동기화 (PC 간)

Claude Code의 자동 memory는 원래 **PC에 갇힌다.** 하네스가 memory를 `projects/<작업경로 인코딩>/memory/`에서 읽는데, 그 폴더명이 **절대경로를 인코딩**하기 때문이다(영숫자가 아닌 문자 → `-`). 사용자 폴더명이 PC마다 다르면 키가 달라져, 파일을 git으로 옮겨도 **다른 PC에서는 읽히지 않는다.**

```
C:\Users\7make\.claude  →  projects/C--Users-7make--claude/memory/   ← PC A
C:\Users\길동\.claude    →  projects/C--Users----claude/memory/       ← PC B (키가 다름!)
```

**해결(현재, 2026-08-05):** 실제 파일은 repo 루트 `memory/`에 두고(git 추적), `.claude` 자신을 포함한 **모든 등록 프로젝트**에 Claude Code 공식 설정 **`autoMemoryDirectory`**로 저장 위치를 그리로 돌린다.

- **`session-memory-hook.py`**(`SessionStart` 훅, 매 세션 시작마다 발화) — cwd의 git root를 `repos.json`의 `path`와 대조해, 등록된 레포면 그 레포의 `.claude/settings.local.json`에 `autoMemoryDirectory`를 써넣는다(멱등 — 이미 맞으면 안 건드림). `.claude` 자신은 `memory/` 루트, 다른 프로젝트는 `memory/projects/<이름>`을 **완전한 절대경로**로 써넣는다 — `~/`로 시작하는 값은 Claude Code의 물결표 확장이 구분자를 빠뜨리는 버그가 있어(예: `~/.claude/memory` → `C:\Users\minwoo.claude\memory`, `minwoo`와 `.claude` 사이 `\` 소실 — 2026-08-05 새 세션에서 `/memory`로 실측 발견) 절대경로로 우회한다. 로컬 폴더명이 `repos.json`과 달라졌어도(리네임 등) 매칭 실패로 조용히 스킵되어 오탐이 없다(실측 검증: 이미설정됨/새로씀/git아님/미등록레포/`.claude` 자신 — 5가지 케이스).
- 실제 파일은 repo 안이라 이미 있는 커밋/push 흐름을 그대로 타고 다른 PC로 넘어간다 — 정크션과 달리 별도 pull 훅이 필요 없다.
- 각 프로젝트의 `.claude/settings.local.json`은 그 프로젝트 자신의 `.gitignore`에 추가해 그 프로젝트의 공유 레포로 새지 않게 한다.
- ⚠ 확인 필요: 리다이렉트가 설정 직후 같은 세션에서 바로 적용되는지 다음 세션부터인지는 공식 문서에도 명시가 없어 미검증.
- PC마다 이미 따로 쌓여있던 로컬 memory는 이 훅이 건드리지 않는다 — 새 PC에서 처음 pull 받은 뒤 기존 로컬 memory와 repo의 `memory/`를 직접 비교해 병합할 것(단순 덮어쓰기 금지, PC마다 다른 내용이 쌓였을 수 있음).

**과거 방식(레거시, `.claude` 전용) — 아직 남아있지만 이제 불필요:** `post-merge` hook이 pull 때마다 `projects/<이 PC의 키>/memory`에 **정크션**(디렉터리 링크)을 걸어 하네스 경로를 repo `memory/`로 직접 연결하던 방식. 정크션 대상 계산이 **비공식 해시 알고리즘**(문서화 안 됨)에 의존해 Claude Code 버전업 시 조용히 깨질 위험이 있어, 공식 지원 설정인 `autoMemoryDirectory`로 대체했다. 정크션 로직 자체는 위험하지 않고 같은 목적지(`~/.claude/memory/`)를 가리키므로 **안전망으로 그대로 남겨둠** — 굳이 지금 제거하지 않는다.

---


## 파일 구조

```
~/.claude/
├── memory/                   # 자동 memory 실체 (PC 간 공유) — 아래 "memory 동기화" 참조
│   └── projects/<이름>/      # repos.json 등록 프로젝트별 memory (autoMemoryDirectory 리다이렉트 대상)
├── design-system/            # design-bakeoff가 읽고 쓰는 디자인 취향 축적 문서 (preferences.md + projects/<slug>.md)
├── setup/
│   ├── hooks/
│   │   └── post-merge        # pull 후 환경 자동 점검 (Bun, $PROFILE, 플러그인, memory 정크션)
│   └── profile.ps1           # PowerShell 프로필 — Bun PATH 보정 + claude (로컬) / tel (텔레그램) 함수 + core.hooksPath 점검(경고)
├── skills/
│   ├── deep-interview/       # 요구사항 명확화 인터뷰 스킬
│   ├── design-bakeoff/       # 여러 AI 모델 UI 시안을 한 Artifact에서 비교·수렴시키는 스킬
│   ├── doc-sync/             # 푸쉬 전후 문서 동기화 스킬
│   ├── draft/                # KBS 기안문 작성 스킬
│   ├── hwp-from-data/        # 데이터로 한글(.hwp) 양식 표 칸 채우기 (COM+HWPML2X, Windows+한글 전용)
│   ├── jbnu-gateway/         # 전북대 API Gateway로 이미지·비디오·TTS 생성 (preflight 비용고지)
│   ├── reference-repos/      # 기존 git repo prior art 참고(읽기)+참고 가치 자동 기록(쓰기, CLAUDE.md 4-c) (인덱스=repos.json reference 필드)
│   ├── self-review/          # 답변 근거 기반 적대적 재검토 스킬
│   ├── skillify/             # 세션의 반복 절차를 재사용 스킬로 굳히기 (품질 게이트)
│   └── sync-repos/           # 여러 PC git 프로젝트 일괄 pull+빌드 동기화 스킬
├── agents/                   # 커스텀 서브에이전트 override (예: Explore.md → model: haiku, 비용 절감용)
├── wiki/                     # reference-repos 함정 위키 — repo별 스턱루프→해법 (<repo>-<기법>.md, 여러 repo 공유는 shared-*)
├── tools/                    # 유지보수 유틸 (audit_rules.py — 규칙 발화율 감사, 지문 기반)
├── docs/                     # 연구·분석 노트 (예: omc-study.md — OMC 비교 분석)
├── channels/
│   └── telegram/
│       ├── .env              # 봇 토큰 (gitignore, PC별 수동)
│       ├── access.json       # 페어링·allowlist (git 동기화)
│       └── approved/         # 승인된 sender (gitignore, 런타임)
├── settings.json             # 전역 설정 (bypass, hooks, statusLine, 마켓플레이스, 채널 활성)
│                              #   ⚠ statusLine·훅 명령은 `bash -c '...'` 래퍼로 OS 감지·분기 (Git Bash 필요).
│                              #     단순화하면 cmd 라우팅 PC에서 silent fail. python 우선 + .ps1 윈도우 폴백.
│                              #   model 필드는 .gitattributes+git-settings-model-filter.py로 git엔 항상 안 보임
├── .gitattributes            # settings.json → filter=modelstrip 지정 (실제 필터 명령은 PC별 로컬 git config)
├── git-settings-model-filter.py  # git clean 필터 — settings.json의 model 키를 git 인덱스에서만 제거
├── statusline.py             # 터미널 상태바 (크로스플랫폼, 기본)
├── statusline.ps1            # 〃 PowerShell 폴백 (python 없는 Windows)
├── toast.sh                  # 데스크톱 알림 디스패처 (Win→toast.ps1 / mac→osascript+afplay / linux→notify-send)
├── toast.ps1                 # Windows 중앙 팝업 호출(기본) + Telegram 발송 + -Persist 시 우하단 토스트 추가 (toast.sh 가 호출)
├── center-toast.ps1          # Windows: 활성 모니터(포커스 창) 정중앙 팝업 (toast.ps1 이 호출 · UTF-8 BOM 필수)
├── doc-sync-hook.py          # git push 후 doc-sync 트리거 훅 (크로스플랫폼, 기본)
├── doc-sync-hook.ps1         # 〃 PowerShell 폴백 (python 없는 Windows)
├── pre-push-doc-sync-hook.py # PreToolUse 훅 — 센티널(.doc-sync-ready) 없는 git push 거부 (doc-sync 사전 검토 기계 강제)
├── session-memory-hook.py    # SessionStart 훅 — repos.json 등록 프로젝트의 auto-memory를 memory/projects/<이름>으로 리다이렉트(autoMemoryDirectory)
├── stuck-loop-hook.py        # UserPromptSubmit 훅 — 좌절 어휘 2회째 감지해 규칙 11-b 트립와이어 주입 (안전망)
├── sync-repos.py             # 여러 repo 일괄 pull+빌드 엔진 (크로스플랫폼, 기본)
├── sync-repos.ps1            # 〃 PowerShell 폴백 (python 없는 Windows)
├── repos.json                # sync-repos 동기화 명단(홈 기준 상대경로+빌드) + reference-repos 인덱스(remote+reference 필드)
├── telegram.json             # 알림용 봇 토큰 (gitignore, PC별 수동)
└── CLAUDE.md                 # 전역 응답 원칙
```
