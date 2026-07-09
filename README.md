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
- **데스크톱 알림 + Telegram 발송** — Claude 답변 완료, 질문 대기, 입력 대기 시점에 PC와 폰 양쪽 알림 (Windows toast + 활성 모니터 중앙 팝업 / macOS osascript / Linux notify-send)
- **Telegram 채널 (비상용 원격)** — `tel` 명령으로 활성 (lock 파일로 한 번에 한 세션만). `claude`는 로컬 전용. (옛 이름 `ctg`도 별칭으로 동작)
- **statusline** — 모델명 / 컨텍스트 사용률 / 5시간·7일 레이트리밋을 터미널 상태바에 표시
- **플러그인 마켓플레이스** — `claude-plugins-official`, `anthropic-agent-skills` 등록
- **document-skills, telegram 플러그인** 활성화
- **전역 스킬** — `/draft`(KBS 기안문), `/deep-interview`(요구사항 명확화 인터뷰), `/doc-sync`(푸쉬 전후 문서 동기화), `/self-review`(답변을 근거 기반으로 적대적 재검토), `/harness`(에이전트 팀·스킬 구성 — 적합성 사전심사 게이트), `/pick-skill`(계획 적었을 때 어떤 스킬/모드로 진행할지 추천하는 진입점 라우터), `/sync-repos`(여러 PC git 프로젝트를 명단 기반으로 일괄 pull+빌드), `/reference-repos`(비자명한 설계 전 비슷한 문제를 푼 기존 git repo를 찾아 참고(읽기) + 어렵게 뚫은 해법·재사용 기법을 묻지 말고 인덱스에 자동 기록(쓰기, CLAUDE.md 4-c) — 사용자 지목 우선 + `repos.json` 인덱스, 모자라면 GitHub 공개 API 라이브 스캔(gh 불요), remote로 PC 독립 접근), `/skillify`(세션에서 잘 통한 반복 절차를 재사용 스킬로 굳히기 — 품질 게이트 + memory(사실)와 경계), `jbnu-gateway`(전북대 API Gateway로 이미지·비디오·TTS 생성 — "이미지/영상 만들어줘" 등에 자동 발동)
- **post-merge hook** — `git pull` 후 환경 자동 점검·복구 (Bun 설치, $PROFILE 갱신, 플러그인 다운로드)

---

## 새 PC 온보딩

### 경우 1: Claude Code를 처음 쓰는 PC (기존 `~/.claude` 폴더 없음)

```powershell
git clone https://github.com/mw3love/claude-global-config_260502.git $env:USERPROFILE\.claude

# core.hooksPath 설정 (한 번만 — 풀 훅 자동 실행)
git -C $env:USERPROFILE\.claude config core.hooksPath setup/hooks

# post-merge hook 첫 실행 (Bun 설치 + $PROFILE 갱신 + 플러그인 다운로드 자동)
bash $env:USERPROFILE\.claude\setup\hooks\post-merge

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
│   │   └── post-merge        # pull 후 환경 자동 점검 (Bun, $PROFILE, 플러그인)
│   └── profile.ps1           # PowerShell 프로필 — Bun PATH 보정 + claude (로컬) / tel (텔레그램) 함수
├── skills/
│   ├── deep-interview/       # 요구사항 명확화 인터뷰 스킬
│   ├── doc-sync/             # 푸쉬 전후 문서 동기화 스킬
│   ├── draft/                # KBS 기안문 작성 스킬
│   ├── harness/              # 에이전트 팀·스킬 구성 메타 스킬 (적합성 사전심사 게이트)
│   ├── jbnu-gateway/         # 전북대 API Gateway로 이미지·비디오·TTS 생성 (preflight 비용고지)
│   ├── pick-skill/           # 계획 진입점 라우터 — 어떤 스킬/모드로 갈지 추천
│   ├── reference-repos/      # 기존 git repo prior art 참고(읽기)+참고 가치 자동 기록(쓰기, CLAUDE.md 4-c) (인덱스=repos.json reference 필드)
│   ├── self-review/          # 답변 근거 기반 적대적 재검토 스킬
│   ├── skillify/             # 세션의 반복 절차를 재사용 스킬로 굳히기 (품질 게이트)
│   └── sync-repos/           # 여러 PC git 프로젝트 일괄 pull+빌드 동기화 스킬
├── wiki/                     # reference-repos 함정 위키 — repo별 스턱루프→해법 (<repo>-<기법>.md, 여러 repo 공유는 shared-*)
├── docs/                     # 연구·분석 노트 (예: omc-study.md — OMC 비교 분석)
├── channels/
│   └── telegram/
│       ├── .env              # 봇 토큰 (gitignore, PC별 수동)
│       ├── access.json       # 페어링·allowlist (git 동기화)
│       └── approved/         # 승인된 sender (gitignore, 런타임)
├── settings.json             # 전역 설정 (bypass, hooks, statusLine, 마켓플레이스, 채널 활성)
│                              #   ⚠ statusLine·훅 명령은 `bash -c '...'` 래퍼로 OS 감지·분기 (Git Bash 필요).
│                              #     단순화하면 cmd 라우팅 PC에서 silent fail. python 우선 + .ps1 윈도우 폴백.
├── statusline.py             # 터미널 상태바 (크로스플랫폼, 기본)
├── statusline.ps1            # 〃 PowerShell 폴백 (python 없는 Windows)
├── toast.sh                  # 데스크톱 알림 디스패처 (Win→toast.ps1 / mac→osascript+afplay / linux→notify-send)
├── toast.ps1                 # Windows toast + Telegram 발송 + 중앙 팝업 호출 (toast.sh 가 호출)
├── center-toast.ps1          # Windows: 활성 모니터(포커스 창) 정중앙 팝업 (toast.ps1 이 호출 · UTF-8 BOM 필수)
├── doc-sync-hook.py          # git push 후 doc-sync 트리거 훅 (크로스플랫폼, 기본)
├── doc-sync-hook.ps1         # 〃 PowerShell 폴백 (python 없는 Windows)
├── sync-repos.py             # 여러 repo 일괄 pull+빌드 엔진 (크로스플랫폼, 기본)
├── sync-repos.ps1            # 〃 PowerShell 폴백 (python 없는 Windows)
├── repos.json                # sync-repos 동기화 명단(홈 기준 상대경로+빌드) + reference-repos 인덱스(remote+reference 필드)
├── telegram.json             # 알림용 봇 토큰 (gitignore, PC별 수동)
└── CLAUDE.md                 # 전역 응답 원칙
```
