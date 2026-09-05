---
name: reference-git-identity
description: "이 PC(7make)의 git 커밋 신원 — 전역은 mw3love/jjrftech@gmail.com, ~/.claude repo만 7maker@gmail.com로 덮어씀"
metadata: 
  node_type: memory
  type: reference
  originSessionId: b0095da3-18a2-434a-8a81-87cab7ff96c9
  modified: 2026-09-05T09:22:51.497Z
---

**이 PC(사용자 폴더 `C:\Users\7make`) 실측, 2026-09-05.**

| 범위 | user.name | user.email |
|---|---|---|
| 전역(`--global`) | `mw3love` | `jjrftech@gmail.com` |
| `~/.claude` repo | `mw3love` | `7maker@gmail.com` (repo 로컬 override) |
| 그 외 repo(youtube_dual_subtitle 등) | 전역 상속 | 전역 상속 |

**정정 이력** — 이 메모의 옛 서술은 「youtube_dual_subtitle repo가 `7maker@gmail.com`을 쓰고 `jjrftech@`는 낡은 값」이라고 되어 있었으나 **실측과 반대였다**(2026-09-05 `git config` 직접 확인으로 정정). `7maker@`를 쓰는 건 `~/.claude` repo 하나뿐이고, 나머지는 전부 전역값 `jjrftech@`를 상속한다.

**How to apply:** 커밋 신원을 묻거나 새 repo를 세팅할 땐 이 표를 근거로 하되, PC가 바뀌면 값이 다를 수 있으니 `git config --global user.email`로 한 번 확인한다. 원래 `projects/youtube_dual_subtitle/` 서랍에 갇혀 있었음(2026-09-05 전역 루트로 이동 — 특정 repo 사실이 아니라 이 PC의 환경 사실이라).
