---
name: user-git-identity
description: "User's preferred git commit identity for this repo (mw3love / 7maker@gmail.com)"
metadata: 
  node_type: memory
  type: user
  originSessionId: 2f243dde-6059-4705-9eb6-6f8f9b943bf7
---

이 저장소에서 사용자가 쓰는 git commit identity:

- name: `mw3love`
- email: `7maker@gmail.com`

이전 커밋들은 `jjrftech@gmail.com`으로 찍혀 있으나, 사용자가 명시적으로 `7maker@gmail.com`을 선호한다고 알려줌 (2026-05-19).

저장소에 user.name/user.email이 아직 설정되어 있지 않을 수 있다. 커밋이 identity 부재로 실패하면 `git -c user.name=... -c user.email=...` inline override로 진행하고, 영구 설정은 사용자에게 직접 실행을 권한다 (Claude는 git config를 임의 변경하지 않는다).
