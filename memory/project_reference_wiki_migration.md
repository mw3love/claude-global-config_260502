---
name: project-reference-wiki-migration
description: reference 지식을 repos.json 블롭에서 wiki/*.md로 이관 — 2026-07-09 전 repo 완료. 남은 일 없음
metadata: 
  node_type: memory
  type: project
  originSessionId: ee19d96b-127b-468e-be1f-eaeef87add59
  modified: 2026-09-05T09:17:40.123Z
---

**2026-07-09 완료. 남은 일 없음** (2026-09-05 재확인 — 계획했던 wiki 파일이 전부 실재).

`~/.claude`의 reference 지식 저장을 **repos.json 한 줄 JSON 블롭 → `wiki/<repo>-<기법>.md` 파일 하나당 기법 하나**로 재설계한 작업. 전 repo 이관 끝(PasteFlow·AI사전·Notion 순, 블롭은 각각 2476→148자·1184→237자·3493→375자로 축소). 함정 없는 짧은 3개 repo(youtube_dual_subtitle·전역Claude·Reading_Highlighter)는 손대지 않기로 확정. 커밋 `a4fbaba`.

**같이 바뀐 정책** — CLAUDE.md 4-c, `reference-repos`·`doc-sync` 스킬 개정. 트리거를 스턱루프 하나로 축소(구 Type B 폐지), `used:` frontmatter로 인용 횟수 측정, `ref-cache/` gitignore.

**공유 위키 패턴** — 여러 repo가 같은 함정을 겪으면 `shared-*.md` 하나로 묶는다(`shared-svg-png-래스터화-우회`·`shared-형광펜-dom-range-직렬화`·`shared-headless-pdf-인쇄검증`).

**재사용되는 두 가지 (이 메모가 남아 있는 이유):**

- **감사 기준(사용자 승인)** — 스턱루프(코드로 복원 불가능한 막다른 길)만 위키에 넣는다. "검색 5분짜리 일반지식"·"코드 읽으면 나오는 구현"은 탈락. 관련 함정끼리 묶어 과분할 방지, 중복은 `shared-*`로.
- **wiki 새 파일 커밋 방식(실측)** — `git -C ~/.claude add -N <경로> && git commit <경로> -m …`. `add -N` 없으면 untracked라 pathspec이 실패하고, `git add … && git commit`(경로 없이)은 사용자가 스테이징해 둔 것을 삼킨다.
