---
repo: Notion_PDF_Preview_260706
remote: https://github.com/mw3love/Notion_PDF_Preview_260706.git
stack: [MV3, JS, CSS, DOM]
tags: [Notion에디터, offsetHeight, getBoundingClientRect, 블록핸들, 컬렉션뷰, 난독화클래스, padding-inline, float붕괴, 편집크롬]
used: []
---

# Notion 에디터 크롬(편집 UI) 제거

라이브 Notion 페이지를 스냅샷할 때 블록 핸들·툴바 같은 **편집용 오버레이**가 같이 찍힌다. Notion export처럼 순수 콘텐츠만 남겨야 한다.

## 함정 1 — 빈 오버레이 판정에 `getBoundingClientRect`를 쓰면 안 잡힌다

블록 핸들 오버레이나 "표 높이만큼 큰데 내용 없는 배경/선택 오버레이 레이어"를 걸러내야 하는데, **`getBoundingClientRect`는 absolute 자식이 잡혀 높이가 0으로 안 나온다**(자식 때문에 rect가 부풀어).

**해법:** **`offsetHeight === 0` + 내용 유무**로 판정한다. offsetHeight는 absolute 자식을 레이아웃에 포함하지 않아 오버레이 본체의 실제 높이를 준다.

## 함정 2 — DB(컬렉션 뷰) 편집 크롬을 클래스로 지우기

DB 뷰의 툴바 / "새로 만들기" / 열 헤더의 `+` / `...` / "새 페이지" 행을 제거해야 한다. **라이브 DOM을 실제로 조사**해 각각의 클래스를 특정해 제거.

- 헤더 끝의 `+` / `...` 버튼은 **안정적 클래스 없는 난독화 `div`**다.
- **함정:** `:last-child`로 지우면 **읽기 전용 모드에서 진짜 헤더 셀을 지울 위험**(그 모드엔 +/... 버튼이 없어 마지막이 헤더가 됨).
- **해법:** 헤더 로우의 **직접 자식 중 `.notion-table-view-header-cell` 클래스가 없는 것만** 제거.

## 함정 3 — `padding-inline:0` 하면 표 전체가 사라진다

Notion DB 컬렉션 뷰는 `<table>`이 아니라 **`div` 그리드 + 가로 스크롤 캔버스**다. `.notion-table-view`의 좌우 데드스페이스를 없애려고 **`padding-inline:0`을 주면 `float:inline-start` 레이아웃이 붕괴**해 표 전체가 소멸한다.

**교훈:** div-그리드 기반 Notion 뷰의 padding은 레이아웃 구조에 물려 있다 — 순진하게 0으로 만들지 말 것.
