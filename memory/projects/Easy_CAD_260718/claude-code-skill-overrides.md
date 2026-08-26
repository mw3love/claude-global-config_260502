---
name: claude-code-skill-overrides
description: 빌트인/번들 스킬(code-review 등) 하나만 끄는 공식 방법 — settings.json의 skillOverrides
metadata: 
  node_type: memory
  type: reference
  originSessionId: babad006-341e-4aa6-a5bb-183c606bc443
  modified: 2026-08-25T23:57:45.192Z
---

Claude Code 공식 문서(`code.claude.com/docs/en/skills.md`, `settings-reference.md`)로 확인한 사실
(2026-08-26, [[feedback_no_superpowers]]에서 이어지는 조사).

**`code-review`는 마켓플레이스 플러그인이 아니라 "번들 스킬"**(`/doctor`·`/debug`·`/loop`·
`/claude-api` 등과 같은 카테고리, Claude Code 자체에 내장). 그래서 `enabledPlugins`/
`plugin uninstall`로는 못 건드리고, 스킬 전용 설정으로 다뤄야 한다.

**개별 스킬 하나만 끄기 — `skillOverrides`** (아무 scope의 settings.json에나 가능:
`~/.claude/settings.json`=전역, `.claude/settings.json`=프로젝트 공유,
`.claude/settings.local.json`=프로젝트 개인):

```json
{
  "skillOverrides": {
    "code-review": "off"
  }
}
```

값은 4단계: `"on"`(기본)·`"name-only"`(이름만 노출)·`"user-invocable-only"`(자동트리거만 막음,
`/code-review`로 수동 호출은 됨)·`"off"`(완전히 숨김 — `/` 메뉴에도 안 뜨고, 전체이름으로
직접 호출해도 에러). **완전히 끄려면 `"off"`.**

`/skills` 메뉴에서 스킬 하이라이트 후 Space로 상태 순환→Enter로도 설정 가능(이 경우
`.claude/settings.local.json`에 저장됨).

**주의**: `disableBundledSkills: true`는 `code-review` 하나가 아니라 **번들 스킬 전체**
(`/doctor` 제외)를 끈다 — `/debug`·`/loop`·`/run`·`/verify` 등도 같이 죽으므로 이 사용자
목적(code-review만 절감)엔 과함, `skillOverrides`가 맞는 도구.

**적용 완료(2026-08-26)**: `~/.claude/settings.json`에 `skillOverrides: {"code-review":
"user-invocable-only"}`를 실제로 반영했다(완전 `"off"`가 아니라 이 값을 고른 이유 —
자동발동만 막고 필요하면 `/code-review`로 직접 부르는 옵션은 남겨둠). Easy CAD 프로젝트의
`docs/final_review_plan.md`도 Phase 4부터 code-review 스킬 대신 자체 진행 방식으로 쓰도록
동기화함(§1 표·Phase 4 체크리스트·진행기록).
