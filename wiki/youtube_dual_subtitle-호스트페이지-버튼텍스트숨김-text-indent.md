---
repo: youtube_dual_subtitle
remote: https://github.com/mw3love/youtube_dual_subtitle.git
stack: [Chrome Extension, TypeScript, CSS]
tags: [content-script, 호스트CSS충돌, text-indent, overflow, 아이콘버튼, 이모지, Playwright디버깅, 한국포털]
used: []
---

# 임의 호스트 페이지에 주입한 버튼 아이콘이 안 보임 — 진범은 text-indent, 첫 가설(그라디언트 텍스트/font-size:0)이 아니었다

## 함정 — 가상 시뮬레이션으로 "검증 완료" 선언

Chrome 확장이 content script로 임의의 제3자 페이지(유튜브가 아닌 사이트)에 UI를 주입하는 기능(ask-anywhere)에서, 버튼의 이모지 아이콘(🖍️📋📝➕)이 특정 사이트(nate.com)에서만 빈 사각형으로 보이는 버그가 났다. 박스(배경·테두리·패딩)는 정상, 글리프만 사라짐.

**1차 시도:** "그라디언트 텍스트 버튼"(`-webkit-text-fill-color:transparent`+`background-clip:text`)과 "아이콘폰트식 `button{font-size:0}`" 두 흔한 CSS 충돌 패턴을 **가정**하고, `color`/`font-family`/`background-clip` 등을 `!important`로 재선언 + 셀렉터 이중화(`.foo.foo`)로 specificity까지 올려 방어했다. **실제 충돌 사이트를 모르니** 그 두 패턴을 흉내낸 가상 HTML을 만들어 헤드리스로 스크린샷 비교 — "방어 전 재현, 방어 후 정상" 확인하고 배포.

사용자가 실제 사이트(nate.com)에서 재확인하니 **똑같이 안 됨.** 가상 시뮬레이션은 "내가 세운 가설"만 검증했지, 그 사이트의 진짜 CSS는 한 번도 안 봤다는 게 드러났다.

## 해법 — 실제 호스트 페이지에 Playwright로 직접 진입해 조사

Playwright MCP로 `browser_navigate`해 **실제 nate.com**을 열고, `browser_evaluate`로 그 페이지 컨텍스트 안에서 우리가 실제 쓰는 CSS 클래스(`ydt-explain-action` 등)를 가진 `<button>`을 직접 만들어 붙인 뒤:

```js
const cs = getComputedStyle(btn);
const range = document.createRange();
range.selectNodeContents(btn);
const textRect = range.getBoundingClientRect(); // 텍스트 노드의 실제 화면 위치
```

`cs.textIndent === '-14000px'`, `cs.overflow === 'hidden'`, `textRect.x === -7020...` — 텍스트(=이모지)가 화면 밖으로 밀려나 클립됐다. `color`/`font-family`는 이미 우리 1차 수정이 올바르게 이기고 있었다(그건 진범이 아니었음). **네이버·네이트 등 한국 포털은 버튼 텍스트를 `text-indent`로 화면 밖에 밀고 `overflow:hidden`으로 클립해 스크린리더용으로만 남기고, 시각적으로는 `background-image` 아이콘을 보여주는 접근성 패턴을 흔히 쓴다.** 우리 버튼은 "텍스트"가 곧 아이콘(이모지)이라 이 리셋에 그대로 당한다.

수정: `text-indent: 0 !important; overflow: visible !important;`를 같은 버튼 클래스들에 추가. 같은 방법(실제 페이지에 주입 + 스크린샷)으로 재검증해 아이콘이 실제로 보이는 것까지 확인.

## 대가 / 한계

- `#id` 셀렉터나 3중 클래스 조합처럼 이론상 더 강한 host 리셋은 여전히 이길 수 있음 — 완전한 격리는 아니다.
- 완전 격리(Shadow DOM)는 검토했으나 `window.getSelection()`이 open shadow root 경계를 넘는 동작이 브라우저별로 불확실해 본문 드래그 재해설/형광펜 기능이 깨질 위험이 있어 채택 안 함.

## 일반화 — 다음에 이런 상황이면

호스트 페이지 CSS 충돌을 "가정"으로 방어할 때, **가상 시뮬레이션 통과 = 실제 사이트 통과가 아니다.** 실제 재현 사이트가 알려져 있으면 Playwright로 그 페이지에 직접 들어가 `getComputedStyle` + `Range.getBoundingClientRect()`(텍스트 노드의 실제 화면 좌표)로 진짜 범인 속성을 찾는 게, 그럴듯한 패턴을 계속 추가로 가정하는 것보다 훨씬 빠르다. 텍스트/아이콘이 "박스는 있는데 안 보임" 증상이면 `color`/`font-*` 계열 외에 `text-indent`/`overflow`/`letter-spacing`도 반드시 같이 검사할 것.
