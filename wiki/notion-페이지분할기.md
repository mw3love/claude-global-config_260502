---
repo: Notion_PDF_Preview_260706
remote: https://github.com/mw3love/Notion_PDF_Preview_260706.git
stack: [MV3, JS, CSS, print]
tags: [페이지분할, HTML→PDF, paged.js, 그리디분할, 표분할, thead반복, "@page", mm, A2, A1, decode, WYSIWYG, print-color-adjust, 형광펜인쇄]
used: []
---

# 브라우저 클라이언트사이드 HTML → PDF 페이지 분할기

Notion 본문을 내보내기 전에 A4/A3 페이지 경계로 잘라 미리보기하는 확장. 조판 라이브러리에 기대려다 막혀서 자체 분할기를 짰다.

## 막다른 길 — paged.js를 못 쓴다

`paged.js 0.4.3`이 **Chrome 149에서 조판 도중 멈춘다**(폴리필이 특정 시점에 hang). 버전을 올릴 수도 내릴 수도 없어 **직접 재귀 그리디 분할기**를 구현.

## 재귀 그리디 블록 분할

페이지(shell)에 블록을 위에서부터 채우다 남은 높이를 넘으면 다음 페이지로.

- **표(table)**: 통째로 넘기지 않고 **`tbody tr` 행 단위**로 쪼개 여러 페이지에 걸침. **조각마다 `thead` 반복** 삽입(각 페이지에서 열 머리 유지).
- **표 외 컨테이너**: **요소 자식(element child) 단위**로 재귀 분할. **원자 블록(더 못 쪼개는 것)만** 잘리도록.
- **페이지 초과 블록**: 다음 페이지로 통째 미루지 말고 **현재 페이지 남은 공간부터 채우고** 넘치는 만큼만 이월(빈 공간 낭비 방지).
- **shell·페이지는 lazy 생성** — 블록이 실제로 들어갈 때만 새 페이지를 만든다(선(先)생성하면 **빈 페이지**가 남음).

## 고정폭 표를 페이지폭에 맞춤

Notion 표는 픽셀 고정폭이라 페이지를 넘긴다. `width:100%` + `table-layout:auto` + 셀 `min-width:0` + `overflow-wrap:anywhere` 로 페이지폭에 욱여넣는다.

## 페이지 박스 & 높이 정확 측정

- **mm 단위 A4/A3 페이지박스**를 실제 용지와 **1:1 매칭**.
- **조판 전에 이미지 `decode()` 강제** — 안 하면 이미지 높이가 0/미확정으로 잡혀 분할 지점이 어긋난다.
- 미리보기 = 출력 **WYSIWYG 인쇄**.

## 함정 — A2/A1은 `size:A2` 가 무시된다

CSS `@page { size: ... }` 의 **명명 크기 목록은 A5~ledger 까지만**이다. `size:A2`/`size:A1`은 브라우저가 무시.

**해법:** 명시적 mm로 지정 — `@page { size: 420mm 594mm }` (A2). 용지 전체를 mm로 통일해 두면 안전.

## 인쇄 시 주석·형광펜 레이어 동반 출력

형광펜 `span`(배경) + 네모박스(`border`) 주석을 인쇄물에 함께 내보내려면:

- 주석 레이어를 **`.pp-page`(`position:relative`) 안에 앵커링**한다. `document` 최상위에 그리면 인쇄에서 어긋난다 → **시작 페이지 요소에 귀속**.
- **`border`는 항상 인쇄**되지만 **배경색은 `print-color-adjust:exact`** 가 있어야 인쇄된다.
- 박스 좌표는 **`clientX - page.getBoundingClientRect().left`** — `.pp-page`에 border가 없어 **absolute 컨테이닝 블록 원점 = 페이지 코너**이므로 이 식이 그대로 맞는다.
- 형광펜 자체 직렬화·`surroundContents` 함정은 → [[shared-형광펜-dom-range-직렬화]].
