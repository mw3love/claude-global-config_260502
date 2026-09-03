---
name: reference-notion-connector-workspace
description: Claude의 Notion 커넥터는 "rf jj의 Notion"(업무용) 워크스페이스에만 연결돼 있어 개인 mw2love 워크스페이스 페이지는 404
metadata:
  type: reference
---

claude.ai Notion 커넥터(integration `1f8d872b-594c-80a4-b2f4-00370af2b13f`)가 인증된 워크스페이스는
**`rf jj의 Notion`**(ID `326666ac-1a35-4c36-af82-73636ca51d85`, jjrftech@gmail.com) 하나뿐.
2026-09-03 실측: `notion-fetch("self")` + `list-private-pages` + `get-teams` 모두 확인 — teamspace 0개,
private 페이지는 전부 KBS/모악산 송신소 업무 콘텐츠.

**증상** — `app.notion.com/p/mw2love/...` 형태(개인 워크스페이스) 페이지를 fetch하면
`object_not_found` 404. 이건 "integration에 페이지를 공유 안 해서"가 아니라
**워크스페이스 자체가 다르기 때문** — 페이지를 공유해도 안 뚫린다.

**조치** — 개인 워크스페이스 콘텐츠가 필요하면 커넥터를 `mw2love` 워크스페이스로 재연결하거나
그 워크스페이스를 추가로 연결해야 한다. 대안: 크롬 확장([[reference-ydt-notion-schema]] 참조)이
쓰는 internal integration 토큰으로 `curl` 직접 호출(토큰은 채팅에 붙이지 말고 gitignore된
로컬 파일 경유).

⚠ 이 커넥터의 plan 제약도 함께 확인됨 — `query_data_sources`는 available_with_limit,
`query_multiple_data_sources`는 full version 필요.
