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
- [x] 5차: ① deep-interview 비교 ② self-improve 내부 ③ 에이전트 프롬프트 정독 ④ skillify 비교 — 분석 완료. ①③ 적용·② 스킵·④ 보류(§8).
- [x] **연구 종결 (2026-06-29).** 핵심 수확 완료: A(커밋 트레일러 9-c)·C(skillify)·①(deep-interview 프레임 챌린지)·③(skillify 나쁜-예 패턴). 남은 건 B급(수확 체감)이라 닫음.
  - **미검증으로 남김:** ①③ 두 스킬 변경은 문구 추가라 다음 실사용 때 발화 확인 필요(일부러 작업 안 만듦).
  - **서랍 보관(필요 시 재개):** ④ Directive 트레일러(실제 "의도된 코드 오수정" 사건 시), D(메모리 린트 — 모순·stale 메모 탐지), self-improve(벤치 있는 최적화 작업 시 prior art).

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

---

## 8. 5차 결론 (4개 과제 분석 + 적용 후보)

### ① deep-interview 비교 — 우리 것(58줄) vs OMC(800줄)
- **OMC 구성:** 수학적 모호성 점수(가중 차원 → 임계값 게이트), Round 0 **토폴로지 락**(드릴다운 전에 최상위 컴포넌트 목록 확정 → 한 컴포넌트에 과적합 방지), **온톨로지 수렴 추적**(엔티티가 라운드마다 안정화되는지 비율로), **챌린지 모드**(라운드 임계값마다 Contrarian/Simplifier/Ontologist 인격 주입), state 영속·resume, brownfield/greenfield 가중치, 스펙 파일 결정화, 실행 브리지(plan/autopilot/ralph/team).
- **판단:** 우리 린 버전이 1인용엔 맞다(수학 점수·온톨로지·state머신은 §1 명제대로 따라하면 부채). **단 1개는 진짜 가치 — 챌린지 패스.** 우리 건 "가장 약한 축"을 *targeting*하지만 **프레임 자체를 의심하는** 질문(반대로면? 가장 단순한 버전은?)이 없다. 습관적 가정을 깨는 데 효과적. → **후보 ①: deep-interview에 막판 챌린지 질문 1~2줄 추가**(라운드 머신 없이, "정리 끝나기 전 한 번은 반론/단순화 질문을 던진다").

### ② self-improve(토너먼트) 내부 — 진화형 코드개선 엔진
- **구조:** N개 executor를 git worktree에서 병렬 → 각자 가설 1개 구현 → **벤치마크 채점** → 토너먼트 선발(랭크 → 무회귀 게이트 → 승자 머지 → **재벤치마크로 개선 확정** → 회귀 시 revert) → plateau/circuit-breaker 정지. **sealed files**로 평가 코드 자기수정 차단.
- **본질:** AlphaEvolve류 진화 탐색. **객관적 벤치마크(적합도 함수)가 있을 때만** 작동. 우리 전역설정 작업엔 그런 측정 지표가 거의 없음.
- **판단: 포팅 안 함.** 무거운 엔진 + 벤치마크 하네스 필요. 전이 가능한 핵심(무회귀 게이트·수락 전 재검증·N회 실패 시 circuit-breaker)은 **이미 우리 규칙 11-b(스턱루프)·11-c(정직표기)에 있음**. → **서랍 보관:** 측정 가능한 최적화 작업(벤치 있는)이 생기면 그때 `reference-repos`→OMC self-improve를 prior art로.

### ③ 에이전트 프롬프트 정독 — 2차 골격 확인 + 신규 너겟
- **planner:** "3~6단계 — 30개 마이크로도, 2개 모호도 아닌" 보정 휴리스틱. pre-mortem(3시나리오)+ADR은 `--deliberate`(고위험) 모드에서만. → 우리 §3.F(ralplan steelman/pre-mortem)의 출처 확인됨.
- **git-master:** 커밋 전 `git log -30`으로 **스타일 자동탐지**(언어 EN/KO·semantic vs plain) 후 매칭 + concern별 분리(파일수→커밋수 휴리스틱) + `--force-with-lease`(never `--force`). **trailers 프로토콜은 git-master에 없음** → OMC trailers는 자기네 `CLAUDE.md`에 있음(우리 9-c 도출이 충실했음을 재확인: 6개 중 4개 채택, Directive·Scope-risk 제외).
- **공통 너겟:** 모든 에이전트가 `<Failure_Modes_To_Avoid>`에 **구체적 나쁜 예시**를 단다(가르치기 좋음). → **후보 ③: skillify가 생성하는 SKILL.md 골격에 "흔한 실패(나쁜 예 1개)" 항목 추가** 권장.
- **재고 후보(선택): `Directive:` 트레일러.** 우리 4개는 *못 채운 한 칸*이 있음 — `Rejected:`="시도했다 버린 길, 재시도 마라", `Directive:`="**틀려 보이지만 의도된** 코드, '고치지' 마라"(미래의 내가 지뢰 밟기 방지). 역할이 다름. → **후보 ④: 9-c에 `Directive:` 5번째로 추가**(선택, 트레일러 비대화 트레이드오프 있음).

### ④ skillify 비교 — 우리 것 vs OMC skillify
- OMC skillify는 우리가 4차에 충실히 포팅한 것과 거의 동일(품질게이트 3문항·추출 항목·frontmatter 강제). **우리가 더 나음:** memory 경계 명시, 위치 `AskUserQuestion`(프로젝트 기본), 비유 병행, 승인 게이트(규칙 12).
- OMC에만 있는 1줄 가치: "스킬은 **휴리스틱·제약·함정·검증**을 인코딩해야 함 — 일반 스니펫·보일러플레이트는 스킬 아님(문서로)". 우리 게이트가 *통과 여부*는 거르지만 *어떤 내용*이 좋은 스킬인지는 덜 명시. → **후보 ②: skillify에 "휴리스틱>스니펫" 한 줄 추가**(후보 ③과 같은 파일이라 묶어 처리 가능).
- **실사용 다듬기:** skillify는 4차에 만들어졌고 아직 실세션 사용 0회 → "실사용 후 다듬기"는 실제로 쓸 때 수행(6차로 이월).

### 적용 결과 (사용자 승인 후 — 규칙 12)
| # | 대상 파일 | 변경 | 상태 |
|---|---|---|---|
| ① | `skills/deep-interview/SKILL.md` | "프레임 챌린지(정리 막판 1회)" 섹션 — 반론/단순화 질문 | ✅ **적용** |
| ② | `skills/skillify/SKILL.md` | "휴리스틱>스니펫" 1줄 | ❌ **스킵** — 게이트 Q1(구글5분)+Q3(진짜노력)과 중복. 린함 보호 |
| ③ | `skills/skillify/SKILL.md` | 함정 가이드에 "구체적 나쁜 예 1개"(OMC `<Failure_Modes>` 패턴) | ✅ **적용** — 뿌리가 다름(에이전트 프롬프트發, skillify 포팅에 없던 발상) |
| ④ | `CLAUDE.md` 9-c | `Directive:` 5번째 트레일러 | ⏸ **보류** — 9-c 실전 검증 전. 실제 지뢰 밟을 때 추가(투기적 추가 금지) |
- self-improve는 **무액션**(서랍 보관: 벤치 있는 최적화 작업 생기면 prior art). deep-interview 수학머신·온톨로지는 **가져오지 않음**(§1 명제 유지).
- **②의 판단 맥락:** 우리 skillify 자체가 OMC skillify 포팅이라 ②는 "뺐던 줄 복원"으로 같은 뿌리. 게이트와 중복 판정 → 스킵. ③은 *다른* 뿌리(에이전트)라 채택.
