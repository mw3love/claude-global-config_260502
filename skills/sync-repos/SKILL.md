---
name: sync-repos
description: 여러 PC에서 쓰는 git 프로젝트들을 한 번에 git pull(+필요 시 빌드)로 최신화한다. "git 동기화", "전부 pull", "프로젝트 최신화", "sync-repos", "/sync-repos" 요청 시 사용. 새 PC로 옮겼거나 한동안 다른 곳에서 작업했을 때 반복적인 repo별 pull을 한 번에 끝낸다.
---

# sync-repos — 여러 repo 한 번에 pull + 빌드

`~/.claude/repos.json` 명단에 적힌 프로젝트들을 한 번에 `git pull` 하고, pull로 실제 변경이 생긴 프로젝트는 빌드까지 실행한다. 경로는 홈(`~`) 기준 상대경로라 PC마다 사용자명이 달라도 그대로 동작한다.

## 동작

1. **엔진 스크립트 실행** — 크로스플랫폼 Python 엔진을 bash 로 실행한다(Windows/macOS 공통). 인터프리터를 먼저 **감지**해 한 번만 실행하고, python 이 없는 PC는 PowerShell 엔진으로 폴백:
   ```
   bash -c 'for p in python3 python; do command -v "$p" >/dev/null 2>&1 && exec "$p" ~/.claude/sync-repos.py "$@"; done; exec pwsh -File ~/.claude/sync-repos.ps1 "$@"' _
   ```
   (변경 없어도 빌드 강제: `--build-all` / 빌드 건너뛰기: `--no-build`. 인수는 위 명령 끝 `_` 뒤에 붙인다 — 예: `... ' _ --no-build`. PowerShell 폴백은 `-BuildAll`/`-NoBuild` 형식도 받음.)
   주의: `python3 ... || python ...` 식의 `||` 체인은 쓰지 말 것 — 엔진이 문제(pull 실패=exit 2, 명단없음=exit 1)로 끝나면 "인터프리터 없음"으로 오해해 다음 인터프리터로 **전체를 재실행**(중복 pull/build)한다.

2. **출력 요약 전달** — 스크립트가 각 repo를 `[v]업데이트 / [=]변경없음 / [-]미클론 / [!]문제`로 찍고 마지막에 요약을 낸다. 그 결과를 사용자에게 그대로 간결히 전한다.

3. **문제 발생 시 개입(이게 스킬의 핵심 가치)** — 스크립트가 `확인 필요:`로 보고한 repo가 있으면:
   - **pull 실패(ff-only 거부, 분기/디버전)** → 해당 repo 상태(`git -C <path> status`, `git -C <path> log --oneline -5 HEAD..@{u}`)를 확인하고, 로컬 미커밋·충돌 원인을 진단해 사용자에게 어떻게 풀지(rebase/stash/merge) **선택지를 제시**한다. 임의로 머지·리셋하지 말 것 — 되돌리기 어려운 작업은 승인 후 실행.
   - **빌드 실패** → 해당 프로젝트로 들어가 빌드 로그를 읽고 원인을 진단·수정 제안한다.

## 명단 관리 (repos.json)

새 프로젝트를 추가하려면 `~/.claude/repos.json`에 한 항목만 더한다:
```json
{ "path": "Dev/새프로젝트", "desc": "설명", "build": "npm install && npm run build" }
```
- `path` — **홈 폴더 기준 상대경로** (절대경로 금지: PC마다 사용자명이 달라짐).
- `desc` — (선택) 요약에 표시할 이름.
- `build` — (선택) pull로 변경이 생겼을 때 repo 폴더에서 실행할 명령. 없으면 pull만.

`.claude` 폴더 자체가 명단 첫 항목이라, `repos.json`을 고쳐 push 해두면 **다른 모든 PC에도 명단이 자동 동기화**된다.

## 안전 가드

- `git pull`은 **`--ff-only`**(fast-forward 전용)로만 한다. 분기된 경우 자동 머지하지 않고 문제로 보고 → 사용자와 처리 방향 결정.
- `git reset`, `git checkout -- `, force push 등 되돌리기 어려운 명령은 **자동 실행 금지**, 진단·제안만.
- 스크립트가 `.claude`를 pull 하면 이번 실행에는 옛 스크립트가 돌고 있으므로, 명단/스크립트 자체가 갱신됐다면 다음 실행부터 반영된다고 안내한다.

## 터미널에서 직접 (Claude 없이)

정상 루틴이면 Claude 세션 없이 터미널에서 바로 더 빠르게 돌릴 수 있다:
```bash
python3 ~/.claude/sync-repos.py        # macOS / Linux / python 있는 Windows
pwsh -File ~/.claude/sync-repos.ps1    # python 없는 Windows 폴백
```
스킬은 **문제가 생겨 진단·수정이 필요할 때** 값을 한다.
