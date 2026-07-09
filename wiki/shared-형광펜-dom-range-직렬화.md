---
shared: true
repos:
  - AI_Dictionary_260622 (https://github.com/mw3love/AI_Dictionary_260622.git)
  - Reading_Highlighter_260614 (https://github.com/mw3love/Reading_Highlighter_260614.git)
  - Notion_PDF_Preview_260706 (https://github.com/mw3love/Notion_PDF_Preview_260706.git)
stack: [DOM, Range, JS]
tags: [형광펜, highlight, surroundContents, DOMException, TreeWalker, 텍스트노드, markdown직렬화, 마크클래스]
reuse: 웹 텍스트에 형광펜을 긋는 모든 프로젝트 — 세 repo가 이미 공유 중
used: []
---

# 웹페이지 형광펜 — DOM Range 하이라이트 & 직렬화

세 프로젝트(AI 사전 · Reading Highlighter · Notion 페이지나눔)가 각자 구현했다가 같은 함정에 수렴한 기법. 사용자가 텍스트를 드래그하면 그 범위에 형광펜 `span`을 씌우고, 나중에 재현·저장할 수 있게 직렬화한다.

## 핵심 함정 — `Range.surroundContents`는 부분 경계에서 터진다

선택 Range가 여러 텍스트 노드에 걸쳐 있으면, 그 Range를 통째로 `surroundContents`하면 **`DOMException`**(부분적으로 선택된 비-Text 노드를 감쌀 수 없음).

**해법:** Range 전체를 한 번에 감싸지 말고, **교차하는 텍스트 노드마다 노드별 subrange**를 만들어 각각 `surroundContents`한다.

- **Reading Highlighter**: `DOM Range surroundContents` · 텍스트노드 단위
- **Notion 페이지나눔**: `TreeWalker`로 선택 Range와 교차하는 텍스트 노드만 골라, 노드별 **단일-텍스트노드 subrange**를 `surroundContents`
- 두 구현의 공통 결론이 위 해법이다.

## 마크 클래스로 출처 구분

형광펜 `span`에 **모델 마크 / 사용자 마크**를 클래스로 구분해 둔다. (AI 답변에 자동으로 친 하이라이트와 사용자가 직접 친 것을 나중에 분리 처리하기 위함.)

## 직렬화 — DOM ↔ markdown

친 하이라이트를 저장·복원하려면 markdown으로 왕복시킨다.

- **AI 사전**: 렌더 텍스트의 **offset 범위를 저장** + `domToMarkdown` 직렬화 + 모델/사용자 코드 클래스 구분
- **Reading Highlighter**: `serializeInline` 로 markdown 직렬화

## 인쇄까지 가는 경우 (Notion 페이지나눔)

형광펜을 인쇄물에 동반 출력하려면 별도 함정이 있다 → [[notion-페이지분할기]] 참조. 요점만:
- **배경색**은 `print-color-adjust: exact` 가 있어야 인쇄됨. **border(네모박스)** 는 항상 인쇄됨.
- 하이라이트 레이어를 `document` 최상위에 그리면 인쇄에서 어긋난다 → **시작 페이지 요소에 귀속**시킨다.
