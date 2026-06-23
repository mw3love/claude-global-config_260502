---
name: reference-repos
description: 비자명한 설계·접근 결정 전에, 비슷한 문제를 이미 해결해 둔 기존 git 프로젝트(prior art)가 있는지 찾아 그 해법을 참고한다. "예전에 비슷한 거 어디서 해봤지", "기존 프로젝트 참고해줘", "prior art 찾아줘", 또는 새 기능을 어떻게 구현할지 접근을 정할 때 사용. 인덱스는 ~/.claude/repos.json의 reference/remote 필드. 경로는 PC마다 달라도 git remote로 PC 독립 접근(로컬 클론 우선, 없으면 shallow clone 캐시).
---

# reference-repos — 완성된 프로젝트에서 prior art 참고

새 작업에서 비자명한 설계·접근을 정하기 전에, **이미 비슷한 문제를 풀어 둔 내 git 프로젝트**가 있는지 찾아 그 해법을 근거로 삼는다. git에 올라간 repo는 어느 정도 완성된 것이 많아 참고 가치가 높다. 경로는 PC마다 다르거나 없을 수 있지만 **git remote는 항상 정확**하므로 remote를 키로 접근한다.

## 인덱스 = `~/.claude/repos.json`

각 항목의 두 필드를 본다(sync-repos와 공용 파일이지만 sync는 `path`/`build`만 읽으므로 무관):

- `remote` — git URL. **PC 불문 안정 키.**
- `reference` — "이 repo가 잘 풀어 둔 문제" 한 줄. **이게 있는 항목만 참고 대상.** (없으면 단순 동기화용 repo.)
- `path`(선택) — 홈(`~`) 기준 상대경로. 이 PC에 로컬 클론이 있을 때의 위치 힌트.

`reference`가 있고 `path`가 없는 항목 = **참고 전용 repo**(sync-repos는 자동 제외함).

## 절차

1. **인덱스 로드** — `~/.claude/repos.json`을 읽어 `reference` 있는 항목만 추린다.

2. **매칭** — 지금 풀려는 문제를 각 `reference` 노트와 대조해 관련 repo를 고른다(0개면 "참고할 prior art 없음"으로 끝내고 일반 진행). 애매하면 사용자에게 어떤 걸 볼지 확인.

3. **코드 확보(PC 독립)** — 고른 repo의 실제 코드를 연다:
   - **로컬 클론 우선**: `path`가 있으면 `~/<path>` 확인. 없거나 `path`가 비었으면, repo 이름으로 흔한 개발 폴더(`~/Dev`, `~/Documents` 등)에서 `.git` remote가 일치하는 클론을 가볍게 탐색.
   - **없으면 shallow clone 캐시**: `git clone --depth 1 <remote> ~/.claude/ref-cache/<repo-name>` 로 받아 읽는다. 이미 캐시에 있으면 재사용(필요 시 `git -C <cache> pull --ff-only`로 갱신). 캐시 디렉터리는 읽기 전용 참고용이며 수정하지 않는다.
   - clone 실패(네트워크·인증)면 그 사실을 보고하고 나머지 후보로 진행.

4. **해법 추출** — 관련 파일을 읽어(README/PLAN/HANDOFF 같은 설계문서가 있으면 먼저, 그다음 핵심 소스) **현재 문제에 옮길 수 있는 접근**을 요약한다. 그대로 베끼지 말고, 왜 그렇게 풀었는지·우리 상황과 다른 점·옮길 때 바꿔야 할 부분을 함께 제시한다.

5. **판단 보조** — 추출한 접근을 현재 작업의 선택지·추천에 **근거로** 연결한다. prior art가 정답이라는 보장은 없으므로(사용자도 확신하지 않을 수 있음), 맹신하지 말고 트레이드오프를 함께 평가한다.

## 새 항목 추가

참고 가치가 있는 repo를 만났을 때 `~/.claude/repos.json`에 한 항목을 더한다:
```json
{ "desc": "프로젝트 설명 [참고 전용]", "remote": "https://github.com/.../repo.git",
  "reference": "이 repo가 잘 풀어 둔 문제들 — 키워드 위주로" }
```
- 이 PC에서 동기화도 하고 싶으면 `path`(+`build`)를 같이 넣는다(sync-repos 명단과 통합).
- `reference`는 **검색 매칭용**이니 키워드(기능·기법 이름)를 충분히 담는다.
- `.claude` repo가 첫 항목이라 push 해두면 다른 모든 PC에 인덱스가 자동 동기화된다.

## 안전 가드

- 캐시 클론(`~/.claude/ref-cache/**`)과 기존 로컬 클론은 **읽기 전용 참고용** — 수정·커밋·push 하지 않는다.
- `repos.json`에 항목을 추가/수정하는 건 가능하나(인덱스 관리), 사용자가 요청했거나 명백히 참고 가치가 확인된 경우에 한한다.
