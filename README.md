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
- **전역 스킬** — `/draft`(KBS 기안문), `/deep-interview`(요구사항 명확화 인터뷰), `/doc-sync`(푸쉬 전후 문서 동기화), `/self-review`(답변을 근거 기반으로 적대적 재검토), `/harness`(에이전트 팀·스킬 구성 — 적합성 사전심사 게이트), `/pick-skill`(계획 적었을 때 어떤 스킬/모드로 진행할지 추천하는 진입점 라우터), `/sync-repos`(여러 PC git 프로젝트를 명단 기반으로 일괄 pull+빌드), `/reference-repos`(비자명한 설계 전 비슷한 문제를 푼 기존 git repo를 찾아 참고 — 사용자 지목 우선 + `repos.json` 인덱스, 모자라면 GitHub 공개 API 라이브 스캔(gh 불요), remote로 PC 독립 접근), `/skillify`(세션에서 잘 통한 반복 절차를 재사용 스킬로 굳히기 — 품질 게이트 + memory(사실)와 경계), `jbnu-gateway`(전북대 API Gateway로 이미지·비디오·TTS 생성 — "이미지/영상 만들어줘" 등에 자동 발동)
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
│   │   ├── post-commit       # 커밋 시 변경 이력 자동 기록
│   │   └── post-merge        # pull 후 환경 자동 점검 (Bun, $PROFILE, 플러그인)
│   └── profile.ps1           # PowerShell 프로필 — Bun PATH 보정 + claude (로컬) / tel (텔레그램) 함수
├── skills/
│   ├── deep-interview/       # 요구사항 명확화 인터뷰 스킬
│   ├── doc-sync/             # 푸쉬 전후 문서 동기화 스킬
│   ├── draft/                # KBS 기안문 작성 스킬
│   ├── harness/              # 에이전트 팀·스킬 구성 메타 스킬 (적합성 사전심사 게이트)
│   ├── jbnu-gateway/         # 전북대 API Gateway로 이미지·비디오·TTS 생성 (preflight 비용고지)
│   ├── pick-skill/           # 계획 진입점 라우터 — 어떤 스킬/모드로 갈지 추천
│   ├── reference-repos/      # 기존 git repo에서 prior art 참고 (인덱스=repos.json reference 필드)
│   ├── self-review/          # 답변 근거 기반 적대적 재검토 스킬
│   ├── skillify/             # 세션의 반복 절차를 재사용 스킬로 굳히기 (품질 게이트)
│   └── sync-repos/           # 여러 PC git 프로젝트 일괄 pull+빌드 동기화 스킬
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

---

## 변경 이력

| 날짜 | PC | 커밋 메시지 |
|------|----|------------|
| 2026-07-04 | Home-Desktop | feat: 완료 알림에 활성 모니터 중앙 팝업 추가 (Windows) |
| 2026-07-04 | Home-Desktop | Docs: PasteFlow reference 갱신 — 입력-소유 자석 캡처·창-스코프 accHitTest·핀 제자리·깜빡임 repaint |
| 2026-06-30 | Home-Desktop | repos.json: AI 사전 reference에 오버레이 전환 기법 추가 |
| 2026-06-29 | Home-Desktop | docs: OMC 연구 종결 표기 (핵심 수확 완료, 잔여는 서랍 보관) |
| 2026-06-29 | Home-Desktop | feat: OMC 5차 연구 반영 — deep-interview 프레임 챌린지 + skillify 나쁜-예 패턴 |
| 2026-06-29 | Home-Desktop | feat: OMC 연구 반영 — git-trailers 커밋 규칙(9-c) + skillify 스킬 |
| 2026-06-28 | Home-Desktop | Reference: PasteFlow에 QGraphicsItem 회전·크기조절 핸들 기법 키워드 추가 |
| 2026-06-27 | Home-Desktop | docs(CLAUDE.md): 죽은 참조 /goal 제거, repos.json 필드명 reference/remote로 보정 |
| 2026-06-27 | Home-Desktop | Add PasteFlow to reference-repos index |
| 2026-06-24 | Home-Desktop | docs(doc-sync): 변경이력 표 수동편집 금지 가드 추가 (post-commit 훅과 중복 방지) |
| 2026-06-24 | Home-Desktop | fix(README): 변경이력 중복 행 제거 (post-commit 훅과 doc-sync 수동기록 충돌) |
| 2026-06-24 | Home-Desktop | chore: sync-repos 명단 AI 사전 경로 날짜-우선 통일 (AI_Dictionary_260622 → 260622_AI_Dictionary) |
| 2026-06-24 | MW-Lenovo | repos.json: Chrome Annotation repo rename 반영 (→ Reading_Highlighter_260614) |
| 2026-06-24 | MW-Lenovo | chore: TUI를 classic 렌더러로 복귀 (fullscreen·DISABLE_MOUSE 제거) |
| 2026-06-24 | MW-Lenovo | chore: fullscreen TUI에서 마우스 캡처 비활성화 (CLAUDE_CODE_DISABLE_MOUSE=1) |
| 2026-06-24 | MW-Lenovo | docs(CLAUDE): 규칙 11 self-review 자동 추천 → 자동 실행으로 전환 |
| 2026-06-24 | MW-Lenovo | draft 스킬: 핵심 미확정값 [작성] 전 AskUserQuestion 확인 규칙(8) 추가 |
| 2026-06-24 | MW-Lenovo | chore: sync-repos 명단 AI 사전 경로 복원 (ai-dictionary → AI_Dictionary_260622) + tui fullscreen |
| 2026-06-24 | Home-Desktop | feat(reference-repos): 라이브 GitHub 스캔 단계 추가 + 지목 우선 |
| 2026-06-24 | Home-Desktop | feat: reference-repos 스킬 — 기존 git repo prior art 참고 시스템 |
| 2026-06-23 | Home-Desktop | chore: sync-repos 명단 AI 사전 경로 수정 (AI_Dictionary_260622 → ai-dictionary) |
| 2026-06-23 | MW-Lenovo | sync-repos: AI_Dictionary_260622 명단 추가 |
| 2026-06-21 | Home-Desktop | feat: 훅·statusline·sync-repos 크로스플랫폼화 (macOS 지원) |
| 2026-06-19 | MW-Lenovo | docs(CLAUDE): 규칙 9-b 추가 — 실행 산출물은 건네기 전 직접 실행 |
| 2026-06-16 | MW-Lenovo | feat: sync-repos 스킬 추가 — 여러 PC git 프로젝트 일괄 pull+빌드 자동화 |
| 2026-06-14 | Home-Desktop | statusline: PowerShell→python 전환(콜드스타트 단축) + powershell 폴백 |
| 2026-06-12 | MW-Lenovo | chore: settings.json — defaultMode auto + harness-marketplace 등록 |
| 2026-06-12 | MW-Lenovo | chore: jbnu-gateway __pycache__ 추적 제거 + .gitignore에 Python 캐시 추가 |
| 2026-06-12 | MW-Lenovo | feat: jbnu-gateway 스킬 추가 — 전북대 API Gateway로 이미지·비디오·TTS 생성 |
| 2026-06-12 | MW-Lenovo | feat(draft): 관련근거 사전확인·접수번호 예외, 전부-인라인 표, 출처 검증표 단계 추가 |
| 2026-06-11 | Home-Desktop | feat: pick-skill 진입점 라우터 스킬 추가 + 전역 설정 정리 |
| 2026-06-11 | Home-Desktop | 규칙 추가/정리: 스턱-루프 트립와이어·검증 충실도·추천 명시 + 자동화 섹션 순서 정렬 |
| 2026-06-11 | moak-minwoo | refactor: 텔레그램 단축어 ctg → tel (ctg는 별칭 유지) |
| 2026-06-10 | Home-Desktop | refactor(doc-sync): ~/.claude 쓰기금지에 좁은 예외 추가 (전역 repo 서술형 .md 동기화 허용) |
| 2026-06-10 | Home-Desktop | docs(README): 기능 목록·파일 구조에 harness 스킬 반영 |
| 2026-06-10 | Home-Desktop | feat: harness 스킬을 전역 personal skill로 포크 + 적합성 사전심사 게이트 추가 |
| 2026-06-09 | moak-minwoo | feat(self-review): 출력 끝에 [다음] 행동 추천 줄 추가 |
| 2026-06-08 | moak-minwoo | docs(CLAUDE): 규칙 11 '덜 상관된 독립 에이전트' 표현 정정 |
| 2026-06-08 | moak-minwoo | feat(self-review): 출력 형식에 [제안] 라벨 추가 |
| 2026-06-08 | moak-minwoo | refactor(self-review): 검토 대상 일반화 + 독립 에이전트 한계 정직화 |
| 2026-06-07 | Home-Desktop | feat: self-review 스킬 + 답변 검증 규칙(11 자기검증, 12 계획·검토 시 실행금지) 추가 |
| 2026-05-31 | Home-Desktop | chore: effortLevel 기본값(high) 복구 및 설정 정리 |
| 2026-05-26 | Home-Desktop | docs(doc-sync): SKILL.md를 사전+사후 2단계 흐름과 정합화 |
| 2026-05-26 | moak-minwoo | docs(CLAUDE.md): 푸쉬 시 문서 동기화 규칙을 사전+사후 2단계로 보강 |
| 2026-05-26 | MW-Lenovo | feat: statusline 맨 앞에 현재 폴더명 시안색으로 표시 |
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
