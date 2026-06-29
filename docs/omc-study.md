# OMC 연구 노트 (oh-my-claudecode 분석 → 우리 전역설정 개선)

> 목적: 평점 높은 Claude Code 플러그인 **oh-my-claudecode(OMC)**를 뜯어보고, 우리 개인 전역설정(`~/.claude`)에 **가져올 아이디어**를 추린다.
> 이 노트는 세션이 끊겨도 이어가기 위한 **회의록**이다. 새 세션에서 "omc-study.md 이어서" 라고 하면 복구.
> 대상 repo(클론): GitHub `Yeachan-Heo/oh-my-claudecode` (shallow clone, scratchpad에 위치 — 세션 끝나면 사라지니 필요시 재클론).

---

## 0. 진행 상태 (매번 갱신)

- [x] 1차: 전체 구조 + CLAUDE.md + 스킬/에이전트 목록 + 룰 템플릿 파악
- [x] 2차: 에이전트 19종 프롬프트 구조, 실행엔진(ultrawork/ralph/autopilot) 구조
- [x] 3차: B(.claude/rules) 메커니즘 소스 확인 → 보류 확정. A(git trailers)·C(skillify) 설계안 작성 (§7)
- [x] 4차: **A 구현 완료** (CLAUDE.md 규칙 9-c). **C 구현 완료** (`skills/skillify/SKILL.md` 생성).
- [ ] 5차(다음): ① deep-interview 그쪽 vs 우리 것 비교, ② self-improve(토너먼트) 내부, ③ 에이전트 프롬프트 전문 정독, ④ skillify 실사용 후 다듬기

---

## 1. 핵심 결론 (한 줄)

OMC는 **배포용 제품**(수천 사용자, npm+플러그인, TS 빌드, 5,795파일), 우리는 **개인 config**.
→ 덩치 대부분은 따라하면 안 되는 유지보수 부채. **추출할 아이디어 몇 개**가 진짜 수확.

---

## 2. 우리가 이미 더 나은 점 (지킬 것)

- **인식론/행동규약 레이어가 압도적.** 우리 CLAUDE.md 규칙 1~12(불확실성 표기, push-back, 스턱-루프 트립와이어, 미검증/프록시검증/실조건검증 3단 정직표기, 비유 병행)는 OMC엔 사실상 없음. OMC `<operating_principles>`는 4줄.
- **린한 스킬 9개** (전부 실사용) vs OMC 50개(모드 중복 심함: ultrawork/ralph/autopilot/ultrapilot/swarm).
- **실환경 맞춤 훅**(Windows+PowerShell, py→ps1 폴백), **memory + reference-repos(prior art)**, **doc-sync 푸쉬 규율** — 우리 고유 자산.

---

## 3. 배울 만한 것 (추천 순위)

### A. ⭐ Git trailers 커밋 프로토콜 — 1순위 추천
커밋 메시지에 구조화 꼬리표:
`Constraint:`(제약) `Rejected:`(버린 대안|이유) `Directive:`(미래 수정자 경고) `Confidence:`(high/med/low) `Scope-risk:`(narrow/mod/broad) `Not-tested:`(못 덮은 엣지).
- 왜: 결정의 *이유*를 git 히스토리(영구·검색가능)에 남김. 우리 memory는 "사실"은 잡지만 커밋 *이유*는 못 잡음.
- 우리 규칙 11(자기검증)·11-c(정직표기)와 철학 일치. trivial 커밋엔 생략 단서도 우리 "비자명한 것에만"과 같음.

### C. ⭐ skillify — "이 세션 워크플로를 스킬로 추출"
우리 harness는 하네스 전체를 짓지만, "방금 잘 됐으니 가볍게 스킬로 캡처" 경로가 없음.
- 좋은 **품질 게이트**: ①5분 구글링으로 나오나?→No ②이 코드베이스 특정인가?→Yes ③진짜 노력 들었나?→Yes
- memory(사실)의 *절차(procedure)* 버전. 보완관계.

### B. ⭐ `.claude/rules/` 자동 발견 + 룰 템플릿
프로젝트 루트 `.claude/rules/*.md`를 자동 컨텍스트 주입. 전역=인식론 / 프로젝트=그 코드 컨벤션 으로 레이어 분리.
- 확인필요: OMC 고유인지 Claude Code 기본 기능인지 별도 확인.

### (B급, 선택)
- **D. wiki의 lint** — 고아·stale·**모순 페이지 탐지**. 우리 memory/MEMORY.md에 "오래됐거나 서로 모순된 메모 잡기" 추가 가치.
- **E. authoring/review 패스 분리 명문화** — "같은 컨텍스트에서 self-approve 금지". 우리 self-review 강화 재료. OMC는 advisory 에이전트를 아예 `disallowedTools: Write,Edit`(읽기전용)로 *툴 레벨*에서 강제.
- **F. ralplan의 steelman + pre-mortem** — 계획에 "최강 반론 + 3개 실패 시나리오 사전부검" 한 줄 추가 가치. (전체 합의루프는 개인용엔 과함)

---

## 4. 가져오지 말 것
TS/npm/dist 빌드, HUD, 벤치마크, i18n 13개, 50스킬 난립, 멀티 CLI(codex/gemini/antigravity) tmux 패널. 멀티모델은 우리 jbnu-gateway로 이미 해결.

---

## 5. 2차에서 새로 발견한 설계 패턴 (프롬프트 엔지니어링 교훈)

### (1) 에이전트 프롬프트 공통 골격 — 매우 전수가능
19개 에이전트가 전부 같은 틀:
- `<Role>`: **"~을 책임진다 / ~은 책임지지 않는다"** (responsible / NOT responsible) — 역할 경계를 날카롭게.
- `<Why_This_Matters>`: 이 규칙이 왜 있는지(동기).
- `<Success_Criteria>`: 통과/실패가 명확한 검증 기준.
- frontmatter: `model`(haiku/sonnet/opus 티어), `level`, `disallowedTools`.
→ 우리 스킬 작성 시 "NOT responsible" 경계와 "Why this matters"를 더 의식적으로 쓸 가치. 우리 규칙 8(외과적 수정)·9(목표→검증)와 정합.

### (2) code-reviewer의 통찰 — 우리 self-review에 직접 적용 가능
"발견(discovery) 단계에서 low-severity를 **필터링하지 마라**. 최신 Claude는 필터 지시를 충실히 따라서, 걸러내라 하면 *잡을 수 있는 버그도 안 꺼낸다*. 발견=커버리지 우선, 순위·필터링은 *다음 단계*에서." → self-review 1패스는 넓게 긁고, 추리기는 나중.

### (3) critic의 통찰 — 우리 규칙 11과 정합
"거짓 승인은 거짓 거절보다 10~100배 비싸다. 있는 것(IS)만 보지 말고 **없는 것(ISN'T = 빠진 것)**을 본다(gap analysis)." 다관점(보안/신입/운영 시선) 강제.

### (4) 실행엔진 = 합성(composition) 구조
ultrawork(병렬) ⊂ ralph(지속+검증루프) ⊂ autopilot(아이디어→코드 전체). 각 스킬에 `Use_When`/`Do_Not_Use_When`을 명시해 **라우팅 규율**. 
- autopilot: "QA 5회 반복, 같은 에러 3회면 멈추고 근본문제 보고" = **우리 규칙 11-b 스턱루프 트립와이어와 동일 사상** (서로 독립 도달 → 좋은 신호).

---

## 6. 다음 액션 후보 (사용자 선택 대기)
1. A(git trailers)·C(skillify) **설계안 승인 시 실제 구현** (CLAUDE.md 규칙 추가 / skillify 스킬 생성)
2. 더 뜯어보기 — deep-interview 비교 / self-improve 내부 / 에이전트 프롬프트 전문 정독

---

## 7. 3차 결론 (B 보류 확정 + A/C 설계안)

### B (.claude/rules) — 보류 확정
- **소스 확인:** OMC 자체 훅 `src/hooks/rules-injector/`. Claude Code 기본 기능 아님(OMC 깔아야 작동).
- native Claude Code = 전역/프로젝트 `CLAUDE.md` + 하위폴더 CLAUDE.md + `@import`. **사용자는 이미 이 표준 방식을 잘 씀.**
- rules의 **유일한 진짜 차이 = 글롭(glob) 조건부 "그때그때" 주입.** 규칙 frontmatter에 `globs: "**/*.test.py"` 달면 그 파일 건드릴 때만 컨텍스트에 뜸 (matcher.ts `shouldApplyRule`: `alwaysApply` 또는 `globs` 매칭). `.cursor/rules`·`.github/instructions` 패턴 호환. oh-my-opencode에서 포팅.
- CLAUDE.md=항상 켜진 사규집 / rules=장비별 경고 스티커(만질 때만).
- **판단:** 1인·중소규모·프로젝트 CLAUDE.md 잘 쓰는 사용자에겐 실익 작음(직접 훅 제작 비용 > 이득). 보류. *단 "글롭 조건부 주입" 아이디어는 서랍에 보관* — 한 프로젝트 CLAUDE.md가 조건부 규칙으로 비대해지면 그때 도입.

### A. Git trailers — ✅ 구현 완료 (CLAUDE.md 규칙 9-c)
6개 원본 → 1인용 4개: `Rejected:`(버린 방법+이유→규칙11-b) / `Not-tested:`(못덮은 엣지→규칙11-c) / `Confidence:`(high·med·low→규칙3) / `Constraint:`(비자명 제약→규칙9).
- 비자명 커밋에만(trivial 생략). 위치: 본문 아래·`Co-Authored-By:` 위. 예시 1개 포함.
- 가치: memory(사실)가 못 잡는 *커밋 단위의 왜*를 git 히스토리(영구)에 박음.

### C. skillify — ✅ 설계 확정 (구현 대기)
빈틈: harness(무거움)·memory(사실) 사이의 "잘 통한 절차를 가볍게 재사용 스킬로 굳히기"가 없음.
- 슬러그 `skillify`(영어, 기존 스킬들과 일관). 트리거 수동: "스킬로 만들어줘"/"이거 스킬화"/"skillify". Claude는 제안만 가능, 자동생성 금지.
- 품질게이트(OMC 차용): ①5분 구글링? No ②프로젝트 특정? Yes ③진짜 노력? Yes — 셋 다 Yes만.
- 흐름: SKILL.md 초안 제시→승인→저장. 위치 `AskUserQuestion` 선택(전역 `~/.claude/skills/` vs 프로젝트 `.claude/skills/`, **기본 추천=프로젝트**).
- 경계: memory=사실 / skillify=절차(SKILL.md에 명시). 린함 보호: 게이트 빡세게+프로젝트 우선.
- SKILL.md 뼈대: frontmatter → ①반복작업 식별 ②게이트 ③추출(입력·단계·성공기준·함정·검증증거) ④위치선택 ⑤초안·승인·저장.
