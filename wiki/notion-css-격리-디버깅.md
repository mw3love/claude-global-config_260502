---
repo: Notion_PDF_Preview_260706
remote: https://github.com/mw3love/Notion_PDF_Preview_260706.git
stack: [JS, CSS, iframe]
tags: [CSS격리, iframe, srcdoc, 위양성, 라이브클론, 디버깅기법]
used: []
---

# 어느 CSS 규칙이 렌더를 깨뜨리는지 격리하는 법

no-JS export/미리보기의 렌더가 **라이브 페이지와 다르게** 나올 때, 수많은 CSS 규칙 중 **무엇이 범인인지** 좁혀야 한다.

## 막다른 길 — 라이브 페이지에 클론을 붙여 실험하면 위양성

디버깅하려고 라이브 페이지에 노드 클론을 직접 얹으면, **페이지의 JS가 그 클론에 간섭**(옵저버·이벤트·재레이아웃)해서 **위양성**이 난다 — 실제로는 CSS 문제가 아닌데 깨진 것처럼 보이거나 그 반대.

## 해법 — iframe `srcdoc` 격리 하네스

1. **iframe `srcdoc`** 안에 스냅샷 HTML + 대상 CSS + 오버라이드를 통째로 넣는다(페이지 JS와 완전 차단된 무균 환경).
2. **CSS 규칙을 하나씩 켜 보며** 어느 규칙에서 렌더가 깨지는지 이분 탐색.
3. 범인 규칙을 찾으면 그 규칙만 오버라이드.

iframe 격리라 페이지 스크립트 간섭이 없어 **CSS만의 인과**를 순수하게 본다.
