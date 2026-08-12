---
name: google-drive-accounts
description: mw-lenovo PC의 G:\/H:\ 드라이브가 서로 다른 구글 계정(개인 vs 회사공유)임 — 업무 파일 전달엔 H:만 사용
metadata: 
  node_type: memory
  type: reference
  originSessionId: 79e45623-5039-476d-afa1-764287c20be6
  modified: 2026-08-10T00:18:38.233Z
---

mw-lenovo PC에서 구글드라이브가 드라이브 문자 두 개로 마운트돼 있고, 용도가 다르다:

- `G:\내 드라이브` — 개인 계정(`7maker@gmail.com`). 업무·회사 공유 파일을 넣으면 안 됨.
- `H:\내 드라이브` — 회사와 공유하는 계정(`jjrftech@gmail.com`). 감시운용PC 등 다른 PC로 파일을 전달할 때(예: `rollup_export.zip` 같은 CIMON 리버싱 산출물)는 항상 이쪽.

**Why:** 2026-08-10 세션에서 감시운용PC용 `rollup_export.zip`을 실수로 `G:\`에 복사했다가 사용자가 정정 — `H:\`에는 이미 같은 파일(md5 일치)이 2026-08-06 세션 때부터 올라가 있었음. `G:\`에 올린 사본은 삭제 완료.

**How to apply:** 이 프로젝트([[AROS_Reverse_Eng_260803]] 관련 작업, 특히 감시운용PC·다른 개발PC로의 파일 전달)에서 구글드라이브 경유가 필요하면 무조건 `H:\내 드라이브`를 쓴다. `G:\`는 후보에서 제외.
