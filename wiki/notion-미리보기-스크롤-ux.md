---
repo: Notion_PDF_Preview_260706
remote: https://github.com/mw3love/Notion_PDF_Preview_260706.git
stack: [JS, CSS, DOM]
tags: [미니맵, cloneNode, scale, IntersectionObserver, 스크롤스파이, spyLock, scrollend, 스크롤바, scrollbar-color, 드래그리사이즈, 커스텀커서, SVG커서]
used: []
---

# 미리보기 좌측 레일 · 스크롤 스파이 UX

여러 페이지 미리보기의 좌측 썸네일 레일과 스크롤 동기화. 겉보기보다 함정이 많다.

## 썸네일 미니맵 — 캡처 라이브러리 없이

각 페이지를 **`cloneNode` + `transform:scale`** 로 축소해 미니맵을 만든다(html2canvas 등 불요).

- **전제:** 이미지가 이미 `data:` URL로 인라인돼 있어야 오프라인 렌더가 됨(→ [[notion-스냅샷-이미지인라인]]).
- `transform-origin: top-left` + 프레임 `overflow:hidden` 으로 클립.

## 함정 — 스크롤 스파이가 중간 항목을 훑는다

`IntersectionObserver`로 현재 페이지를 강조하면, **smooth 스크롤 도중 중간 항목(2→3→4)을 모두 지나며** 강조가 깜빡인다.

**해법:** **`spyLock` + `scrollend`** 로 스크롤 중엔 스파이를 잠근다.

- 클릭 시 **즉시 목표를 강조**하고 `spyLock=true`.
- 스크롤이 끝나면(`scrollend`) 잠금 해제.
- **`scrollend` 미발화 대비**(no-scroll 케이스 등) **`setTimeout 1500ms` 폴백**으로 반드시 잠금 해제.

## 썸네일 클릭 이동 — 하이브리드

가까우면 `smooth`, 멀면 `instant` 점프(먼 거리를 smooth로 하면 중간 페이지를 오래 훑어 어지럽다).

## 함정 — Chrome에서 `::-webkit-scrollbar` 커스텀이 무시된다

Notion CSS가 표준 `scrollbar-width`를 걸면 **Blink가 `::-webkit-scrollbar`를 통째로 무시**하는 것으로 추정.

**해법:** 표준 **`scrollbar-color` / `scrollbar-width`** 로 강제한다. `html`에 `scrollbar-color`를 지정하면 Blink가 **오버레이(hover 전용) 대신 클래식 상시 스크롤바**를 그린다. 주입 스타일이 뒤에 와서 Notion CSS를 이긴다(`scrollbar-width` 생략=기본 폭, `thin`이면 좁아짐).

## 레일 자동 `scrollIntoView` 제거

active 항목을 자동으로 `scrollIntoView`하면 클릭·스크롤 때 좌측이 **덜컹거린다** → 제거. 강조 테두리만 두고, **레일은 사용자 휠에만** 이동.

## 레일 너비 드래그 리사이즈 (핸들 하나로 겸용)

접기 핸들 하나로 **드래그(>4px)=리사이즈 / 클릭(<4px)=접기** 를 겸한다. **CSS var `--railw`** 하나로 rail width + pages padding + handle 위치를 일괄 구동.

## 커스텀 커서 — 어느 배경에서도 보이게

**SVG `data:` URL** 커서. **흰 stroke halo 4px + 본색 2px 이중 path**로 밝은/어두운 배경 모두에서 보이게 하고, hotspot 좌표를 지정.
