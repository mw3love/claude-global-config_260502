---
repo: AI_Dictionary_260622
remote: https://github.com/mw3love/AI_Dictionary_260622.git
stack: [Chrome Extension MV3, JS]
tags: [브라우저액션, iframe오버레이, executeScript, 부트스트랩, 전체화면, fullscreenchange, ResizeObserver, postMessage, translateZ, 영상위페인트]
used: []
---

# 크롬 확장 오버레이 주입 & 유지

브라우저 액션 팝업 대신, 현재 탭에 iframe 오버레이를 띄워 콘텐츠 위에 패널을 유지하는 방식. 함정이 여럿이다.

## 팝업 → 콘텐츠 iframe 오버레이 전환

`activeTab` + `scripting.executeScript` 로 현재 탭에 주입한다. 주입되는 `func` 는 **직렬화되어 건너가므로 자기완결(self-contained) 부트스트랩**이어야 한다 — 외부 스코프 참조 불가, 필요한 것은 함수 안에 다 넣는다.

## 함정 — HTML5 전체화면에 들어가면 패널이 사라진다

동영상 등이 전체화면(`requestFullscreen`)에 들어가면 오버레이가 전체화면 요소 밖이라 안 보인다.

**해법:** `fullscreenchange` 이벤트에서 `fullscreenElement` 를 읽어 **패널을 그 요소에 재부착**한다.

## iframe 자동 높이

내용 높이에 맞춰 iframe이 커져야 한다.

- iframe **내부** `ResizeObserver` → `postMessage` → **부모**가 iframe `height` 조정.
- 리사이즈 폭주를 막으려 `rAF` 로 합친다(coalesce).

## 오버레이 UX 디테일

- 위치 **드래그 저장** + 📖 아이콘으로 최소화. **클릭 vs 드래그는 4px 임계**로 구분(움직임 4px 미만이면 클릭).

## 함정 — 영상 위에서 페인트가 버벅인다

오버레이가 재생 중인 영상 위에 있으면 페인트가 끊긴다.

**해법:** `translateZ` 로 **합성 레이어를 격리**하면 완화된다(별도 GPU 레이어로 올려 영상 리페인트와 분리).
