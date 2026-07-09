---
repo: claude-global-config
remote: https://github.com/mw3love/claude-global-config_260502.git
stack: [git, hooks, Windows, Git-Bash]
tags: [git훅, githook, post-commit, post-merge, core.hooksPath, .git/hooks, 훅제거, 훅비활성화, 이력커밋, 추적본, 로컬복사본, hooksPath미설정]
used: []
---

# git 훅: 추적본을 지워도 안 죽는다 — .git/hooks 그림자 복사본

## 함정
`post-commit` 훅이 매 커밋마다 별도 이력커밋(`docs: 변경 이력 업데이트`)을 만들어 히스토리를 오염시켰다. 없애려고 **추적 파일 `setup/hooks/post-commit`을 `git rm` 했는데, 커밋할 때 훅이 계속 발화**했다. 추적본은 분명히 사라졌는데도.

왜: 이 PC는 `core.hooksPath`가 **어느 스코프에도 미설정**(빈 값)이었다. 온보딩 문서 의도는 `core.hooksPath = setup/hooks`였지만 실제로는 안 걸려 있었다. 그래서 git이 발화시키는 건 추적본이 아니라 **기본 위치의 로컬 복사본 `.git/hooks/post-commit`** 이었다. 옛 온보딩 방식(훅을 `.git/hooks`로 *복사*하던 시절)의 잔재.

추가 증거 — 같은 이유로 `.git/hooks/post-merge`도 **낡은 버전(statusLine 패치 + settings.json 자동커밋)** 이 돌고 있었고, 추적본(환경점검 신버전)과 내용이 달랐다. **로컬 복사본은 추적본이 업데이트돼도 자동으로 못 따라온다** → 조용한 버전 드리프트.

판별 한 방: `git config core.hooksPath`
- `setup/hooks` 나오면 → git이 `.git/hooks`를 통째로 무시, 추적본만 실행(안전).
- **빈 값이면 → `.git/hooks/`의 로컬 복사본이 살아있다.** 추적본을 지워도 안 죽는다.

## 해법
1. 즉시: 로컬 복사본 직접 제거 — `rm .git/hooks/post-commit` (`.git/**`는 push 안 되는 클론-로컬이라 각 PC에서 따로 지워야 함).
2. 근본: 각 PC에서 `git config core.hooksPath setup/hooks` 설정. 이러면 git이 `.git/hooks`를 **전부 무시**하고 추적본만 실행 → 로컬 복사본이 모두 inert가 되고, **추적 파일의 존재/삭제가 권위를 가진다**(pull로 전파). 드리프트도 사라짐(추적본 = 실행본).

## 대가
- `core.hooksPath`를 켜면 그동안 돌던 로컬 `.git/hooks/post-merge`(낡은 동작)가 갑자기 추적본(신버전) 동작으로 바뀐다 — 내용 diff를 먼저 확인하고 켤 것.
- `.git/hooks`는 클론-로컬이라 "전역 설정" 습관으로 커버 안 된다. PC마다 물리적으로 존재하며, 각 PC에서 판별·조치해야 한다.
- 되돌리기: `git config --unset core.hooksPath`.
