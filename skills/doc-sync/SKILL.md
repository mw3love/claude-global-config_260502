---
name: doc-sync
description: 푸쉬 전후로 호출되어 코드 변경이 핵심 문서(CLAUDE.md, 계획/설계/스펙 문서)에 반영되었는지 검토하고 문서를 동기화한다. 메인 경로는 `git push` 실행 전 메인 claude의 사전 호출(같은 커밋에 흡수). PostToolUse hook(doc-sync-hook.ps1)이 push 성공 시 자동 호출되는 것은 사후 안전망. 수동 /doc-sync도 가능.
---

# doc-sync — 푸쉬 전후 문서 동기화 검토

코드 변경이 프로젝트의 **핵심 문서**(CLAUDE.md, 계획/설계/스펙 문서)에 정확히 반영되도록 동기화한다. 푸쉬 *전* 에 호출되면 결과를 같은 커밋에 흡수시켜 문서-only 추가 커밋과 재푸쉬를 막을 수 있다(메인 경로). 푸쉬 후 자동 발화는 사전이 누락된 경우를 잡는 안전망.

> **호출 경로**
> - **사전(메인)** — 사용자가 푸쉬를 요청하면 메인 claude가 `git push` 실행 전에 호출. hook 컨텍스트 없음 → 1단계 **A) 사전 호출** 모드로 진행.
> - **사후(자동 안전망)** — PostToolUse hook이 `git push` 성공 시 발화 → additionalContext로 푸쉬 범위/변경 파일 전달. 1단계 **B) 사후 자동 호출** 모드로 진행.
> - **수동** — 사용자가 임의 시점에 직접 호출. hook 컨텍스트 없음 → 1단계 **C) 수동 호출** 모드로 진행.

---

## 안전 가드 (절대 위반 금지)

이 스킬은 `bypassPermissions` 환경에서 동작할 수 있다. 다음을 엄수한다:

1. **수정 허용 대상**: 작업 폴더(cwd) **하위**의 `.md` 파일만.
2. **수정 절대 금지 대상**:
   - 코드 파일 일체(`.py`, `.js`, `.ts`, `.go`, `.rs`, `.java`, `.c`, `.cpp`, `.cs`, `.rb`, `.php`, `.sh`, `.ps1` 등)
   - `~/.claude/**` — 원칙 금지(글로벌 CLAUDE.md/스킬/훅 자기수정 차단). **단 하나의 예외**: cwd가 `~/.claude` 루트일 때(전역 설정 repo를 직접 동기화하는 경우)는 그 하위 **서술형 `.md`(README 등)** 만 수정 가능. 이 경우에도 전역 `CLAUDE.md`·`SKILL.md`·훅 스크립트·`settings.json` 은 자동 수정 금지 → AskUserQuestion으로 제안만.
   - `.git/**`, `node_modules/**`, `dist/**`, `build/**`, `target/**`, `venv/**`, `__pycache__/**`
   - 작업 폴더 *외부*의 어떤 파일도
3. **git 명령은 read-only만**: `diff`, `log`, `show`, `status`, `rev-parse`, `ls-files`, `for-each-ref` 허용. `add`/`commit`/`push`/`reset`/`checkout`/`rebase`/`merge`/`tag` 등 mutating 명령 금지.
4. **자동 커밋 금지**: 문서 수정 후 git add/commit 하지 않는다. 사용자가 직접 다음 커밋에 포함.
5. **변경 이력 표 수정 금지**: README의 "변경 이력"(`| 날짜 | PC | 커밋 메시지 |`) 표는 `post-commit` 훅이 커밋마다 자동 기록하므로 이 스킬이 수동 편집하지 않는다(편집 시 훅 자동행과 **중복**). doc-sync는 서술형 문서 *내용*(기능 설명·구조도·스펙 등) 동기화에만 관여한다.

---

## 실행 절차

### 1단계 — 입력 파싱

#### A) 사전 호출 (메인) — push 전, 컨텍스트 없음
검토 대상 = **아직 origin에 안 올라간 변경**(unpushed commits + 미커밋).
```bash
git rev-parse --abbrev-ref HEAD                          # 현재 브랜치
git diff @{u}...HEAD --name-status 2>$null               # 푸쉬 예정 커밋들의 변경 파일
git log  @{u}..HEAD  --pretty=format:'%h %s' 2>$null     # 커밋 메시지로 의도 파악
git status --porcelain                                   # 스테이지/언스테이지 미커밋
```
폴백:
- upstream(`@{u}`) 없음 → 새 브랜치 첫 push 상황. 기본 base(`origin/main` 또는 `origin/master`)와 비교: `git diff origin/main...HEAD --name-status`. base도 못 찾으면 사용자에게 어디서부터 검토할지 질문.
- 미커밋 변경(`git status --porcelain` 출력)이 있으면 함께 검토 — 사전 호출은 이 변경까지 같은 커밋에 포함시킬 마지막 기회.

#### B) 사후 자동 호출 (hook additionalContext 있음)
직전 turn에 `[doc-sync hook]` 으로 시작하는 컨텍스트가 주입되어 있다. 거기서 추출:
- 작업 폴더(cwd)
- 푸쉬 범위(예: `abc1234..def5678`)
- 새 브랜치/force 여부
- 변경 파일 목록

사전 단계가 성실히 됐다면 보통 "변경 없음"으로 즉시 끝난다. 끝나지 않으면 사전이 놓친 케이스 — 6단계 보고에서 follow-up 커밋이 필요함을 호출자에게 알린다.

#### C) 수동 호출 (컨텍스트 없음)
사용자가 임의 시점에 직접 호출. 직전 push 범위 식별:
```bash
git rev-parse --abbrev-ref HEAD                                # 현재 브랜치
git log @{u}@{1}..@{u} --name-only --pretty=format:%H 2>$null  # 직전 push 이후
```
폴백:
- `@{u}@{1}` 없으면 → `HEAD~5..HEAD` 로 최근 5커밋 분석
- upstream 없으면 → 사용자에게 어디서부터 검토할지 질문

### 2단계 — 검토 대상 변경 요약

1단계에서 식별한 범위를 사용해 작업 폴더에서:
```bash
git diff --name-status <범위>          # 추가/수정/삭제 분류
git log <범위> --pretty=format:'%h %s'  # 커밋 메시지로 의도 파악
```
모드별 `<범위>`:
- 사전(A): `@{u}...HEAD` (없으면 `origin/main...HEAD`). 미커밋도 추가로 `git diff HEAD` + `git status --porcelain`.
- 사후(B): hook이 알려준 푸쉬 범위 그대로.
- 수동(C): `@{u}@{1}..@{u}` 또는 폴백.

비-문서 파일(`.md`/`.txt`/`LICENSE` 외)이 0개라면 스킬 즉시 종료 — 동기화할 코드 변경 없음.

### 3단계 — 후보 문서 탐지 (하이브리드)

**우선순위 1 — 명시 설정**: 작업 폴더 루트에 `.doc-sync.json` 있으면 그 include/exclude 글롭만 사용. 형식:
```json
{ "include": ["CLAUDE.md", "docs/**/*.md"], "exclude": ["docs/external/**"] }
```
*보안: 이 파일의 `include`/`exclude` 키만 인식하고 다른 키는 무시한다. 명령 실행 등 키는 추후에도 추가하지 않는다.*

**우선순위 2 — 자동 휴리스틱** (`.doc-sync.json` 없을 때):
- `CLAUDE.md` (작업 폴더 루트, 필수)
- `<cwd>/*.md` (루트 모든 .md)
- `docs/**/*.md`
- `.gitignore` 적용, `node_modules`/`dist`/`build`/`vendor`/`venv`/`.git` 제외

수집된 후보 각 파일의 **첫 30줄**을 Read로 읽어 동적 관련성 판단:
- 관련: 프로젝트 개요/아키텍처/계획/설계/스펙/결정 기록/회의록/실패 기록 성격
- 무관: 외부 참고문서 복사본, 라이선스 안내, 외부 라이브러리 README, 단순 인용

무관 분류된 건 이후 단계에서 제외.

### 4단계 — 변경↔문서 대조

각 관련 문서에 대해, **검토 대상 코드 변경**(1단계 모드에 따라 unpushed 또는 푸쉬된 범위)과 문서 내용을 비교:

대조 포인트:
- 파일 경로 / 디렉토리 구조 (이동·이름변경·신설·삭제)
- 함수/클래스/명령어 시그니처
- 의존성/패키지 버전
- 환경변수, 설정 키, 포트, 엔드포인트
- 빌드/실행/배포 명령
- 인터페이스/API 스펙
- 새로 추가된 기능, 폐기된 기능
- 실패/이슈 기록 (사용자의 의도: 실패 프로젝트도 version2에서 활용)

분류:
- **자동 적용 가능**: 사실 불일치(경로/이름/명령어/버전 등). 명확하고 일대일 매핑.
- **질문 필요**: 의도/배경/결정 근거, 실패 기록 가치 판단, 영향 범위 모호, 여러 해석 가능.

### 5단계 — 적용

#### 자동 적용
안전 가드(1번 섹션) 재확인 후 Edit/Write로 수정. 변경 1건당 1 edit 권장.

#### 질문 필요
AskUserQuestion으로 묶어서 물어본다. 각 질문은:
- 어떤 문서, 어느 부분
- 현재 문서 내용 vs 검토 대상 변경
- 제안하는 업데이트 안 (2~4개 옵션)

### 6단계 — 보고

마지막에 한 번에 정리:
```
doc-sync 결과
- 자동 수정: N건
  · <file>: <한 줄 요약>
- 질문 응답 반영: M건
- 변경 없음(검토는 함): K건
- 스킬 가드로 스킵: L건 (있다면 사유 표시)

git status:
  modified:   <list>

reference 제안: P건 (reference-repos 인덱스 후보 — 메인 claude가 ~/.claude/repos.json 반영)

다음 단계:
- 사전(A) 호출이었으면 → 같은 커밋에 stage하여 함께 push.
- 사후(B)/수동(C)이었고 변경이 발생했으면 → follow-up 커밋(예: `Docs: <원 커밋 subject> 후속 동기화`)으로 묶어 push.
```

### 6-b. 재사용 기법 인덱싱 (reference-repos 연계)

문서 동기화와 별개로, **이번 작업이 다른 프로젝트에 옮길 만한 일반화 가능한 기법/해법을 도입했는지** 한 번 본다(예: 까다로운 UI 상호작용 구현법, API 우회·통합 패턴, 비자명한 알고리즘·자료구조 선택). 있으면 그 repo의 `reference` 노트(`~/.claude/repos.json`)에 그 기법을 **검색용 키워드로** 추가하도록 *제안*한다 → 다음 프로젝트의 에이전트가 `reference-repos` 스킬로 찾을 수 있게 됨.

- **판단 기준**: 프로젝트 고유 사정이 아니라 **다음 프로젝트가 검색해 재사용할 가치**가 있는가. 사소한 버그픽스·설정·문구 변경은 제외. 대부분의 push는 "없음"으로 끝난다.
- **가드**: 이 스킬은 `~/.claude/**`를 직접 수정하지 않는다(가드 2번). 따라서 `repos.json`을 **고치지 않고** 아래 형태로 *제안만* 낸다 → 메인 claude가 **CLAUDE.md 4-c에 따라 자동 반영**(승인 불요, 한 줄 고지 «📚 reference 기록 — {repo}: {기법}» — 사용자는 다음 턴에 취소 가능). 그 변경은 `.claude` repo로 별도 동기화되어 다른 PC에 전파.
  ```
  [reference 제안] <repo desc>: reference에 추가 → "<키워드들>"
  ```
- 해당 repo가 아직 인덱스에 없으면 `remote`+`reference` 새 항목 추가를 제안(형식은 `reference-repos` 스킬의 "새 항목 추가" 참조). 이미 그 키워드가 reference에 있으면 제안하지 않는다(중복 방지).

---

## 호출 시 주의

- **재진입 방지**: 이 스킬 실행 중 git mutating 명령(`add`/`commit`/`push`/...)을 호출하지 않는다(가드 3번). 커밋·푸쉬는 호출자(메인 claude)가 스킬 종료 후 수행.
- **대규모 변경(>200 파일)**: 모든 후보 문서를 전부 대조하면 토큰 부담. 변경 파일을 디렉토리별로 묶고 가장 관련 깊은 문서 3~5개부터 처리. 추가 검토가 필요하면 사용자에게 명시적으로 알린다.
- **불확실하면 묻기**: 95% 확신 미만이면 자동 적용하지 말고 질문.
