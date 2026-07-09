---
repo: youtube_dual_subtitle
remote: https://github.com/mw3love/youtube_dual_subtitle
stack: [Notion API]
tags: [Notion, 덮어쓰기, 재저장, archived, in_trash, 벌크삭제없음, 어포던스, 크롬확장]
reuse: Reading Highlighter·AI Dictionary 등 Notion 저장 기능 공유 프로젝트에 직접 재사용
used: []
---

# Notion 페이지 "덮어쓰기"(재저장) 구현

이미 저장한 Notion 페이지의 본문을 통째로 갈아끼우려는데, Notion API에 그런 엔드포인트가 **없다.** 순진하게 "지우고 다시 쓰기"로 가면 페이지가 반파된다.

## 함정 — 본문 통째 교체 API가 없다

- `PATCH /v1/pages` → **속성만** 바꿈 (본문 블록 못 건드림)
- `PATCH /v1/blocks/{id}/children` → **append 전용** (교체 아님)
- 블록 삭제는 `DELETE /v1/blocks/{id}` 로 **한 개씩**, 벌크 없음, 평균 3 req/s

그래서 "옛 블록 전부 지우고 재추가"를 하면:
- 20~40블록에 **7~15초**
- **중간 실패 시 페이지 반파** — 먼저 지우면 빈 페이지, 먼저 붙이면 중복

## 해법 — 지우지 말고, 새로 만들고 옛것을 버린다

1. 새 페이지 `POST`
2. 옛 페이지 `PATCH {archived: true}` 로 휴지통에 보냄

요청 **2번**으로 끝. **부분 실패 상태가 존재하지 않는다** — archive가 실패해도 결과는 "중복 페이지 2개"라 안전 퇴화(safe degradation)다. 반파는 없다.

## 대가

page id / URL이 매번 바뀐다(churn). 재저장할 때마다 새 페이지이므로 링크가 갈린다.

## 오판 방지 3가드

1. **prev/현재 `databaseId`를 둘 다 `normalizeId`로 정규화 비교** — DB가 바뀌었으면 남의 DB이므로 건드리지 않는다.
2. **`prevPageId !== 방금 만든 data.id`** — 자기 자신을 archive하는 사고 방지.
3. **`archivePage`의 404는 성공으로 처리** — 사용자가 이미 지운 것이라 치울 게 없는 상태다. 실패로 치면 거짓 "옛 페이지 남음" 경고가 뜬다.

## 버전 함정

휴지통 필드 이름이 API 버전에 따라 다르다.
- `Notion-Version: 2022-06-28` → `archived`
- 최신 → `in_trash`

## 부수 함정 — 재저장 시 제목

제목을 "AI 답변의 첫 인라인 백틱 예문"에서 파생시키면, 사용자가 형광펜을 앞쪽에 칠할 때 제목이 튄다. **재저장 제목은 첫 저장 때 것을 재사용**한다.

## 근본 교훈 — 저장 후 편집은 어포던스 버그가 된다

저장 후 본문을 고쳤을 때 상태를 "미저장"으로 되돌리면, 버튼이 **재생성(새 페이지 또 만들기)** 을 유도하는 어포던스 버그가 된다. 대신 **`pageId`는 남기고 `saved` 플래그만 내려** 버튼 라벨을 "업데이트"로 바꾼다.
