---
repo: Shorts_Eng_260903
remote: https://github.com/mw3love/Shorts_Eng_260903.git
stack: [모바일웹, iOS Safari, WebKit, CSS]
tags: [overflow-hidden, clip-path, will-change, 합성레이어, compositing, 화면밖대기패널, peek, 미리보기, 실기기전용버그, 프레임픽셀실측, ffmpeg, 오진, 스턱루프]
used: []
---

# 화면 밖에 숨겨둔 패널이 iOS에서만 보임 — `overflow:hidden`은 합성 레이어를 안 자른다 (+ 화면 증상은 화면을 재서 판정할 것)

## 함정

카드 좌우 스와이프 미리보기 패널(`.peek`)을 `transform: translateX(∓100%)`로 앱 박스
바깥에 대기시켜 두고, 조상 `#app`의 `overflow:hidden`이 잘라 줄 것으로 믿었다.
데스크톱 크롬에서는 완벽히 잘렸다. **아이패드/아이폰 Safari에서만** 그 패널들이 앱
박스 양옆 여백에 **상시** 드러나 다른 카드 조각이 계속 보였다.

**1차 오진(실패)** — "스와이프가 중간에 끊겨 드래그 transform이 안 지워진 잔상"으로
보고, 다음 `pointerdown`에서 강제 정리하는 코드를 넣음. → 증상 그대로.

**2차 오진(실패)** — "세로 스크롤 중 가로/세로 판정이 'h'로 잘못 고착돼 안 풀린다"로
보고, 세로가 우세해지면 가로 판정을 취소하는 로직을 넣음. → 증상 그대로.
(게다가 이건 스와이프 손맛을 바꾸는 부작용까지 있어 나중에 되돌려야 했다.)

두 오진의 공통점: **화면에서 벌어진 일을 코드만 읽고 추론했다.** 둘 다 그럴듯했고
로컬 검증도 통과했다 — 애초에 크롬에서는 이 버그가 **원리적으로 재현되지 않으므로**
"로컬 통과"가 아무런 정보도 주지 못하는 종류의 버그였다.

## 해법

### 진단이 먼저 — 프레임을 픽셀로 재니 한 번에 끝났다

신고받은 화면녹화를 `ffmpeg`로 프레임 분해한 뒤, 한 프레임의 **열(column)별 밝기
프로파일**을 재서 콘텐츠가 있는 구간을 뽑았다:

```
[0–207] 왼쪽 슬리버 | 여백 | [286–1247] 본문 | 여백 | [1328–1535] 오른쪽 슬리버
                 ↑ 좌우 슬리버 폭이 각각 208px로 정확히 대칭
```

**대칭이라는 사실 하나로 상태 가설이 즉사한다.** 드래그로 밀린 것이라면 두 패널이
같은 방향으로 옮겨져 한쪽만 넓어지고 반대쪽은 사라진다. 좌우가 같다 = 오프셋 0 =
**패널이 「쉬는 위치」에 얌전히 서 있는데 그냥 보이는 것.** 본문 텍스트 폭에서 역산한
앱 박스 경계와 슬리버 경계가 1px 오차로 일치해 확인 사살.

```bash
ffmpeg -i frame.png -vf "crop=W:H:0:Y,format=gray" -f rawvideo prof.raw
# 열마다 최대 밝기 → 임계값으로 CONTENT/gap 구간화
```

### 진범

`.peek`에 걸린 `will-change: transform` 때문에 별도 **합성 레이어**로 승격되는데,
**iOS Safari(WebKit)는 이 경우 조상의 `overflow:hidden` 클립을 무시한다.**

같은 페이지의 본문(`.content`)도 `will-change:transform`인데 멀쩡했던 이유가 결정적
힌트였다 — 그 부모 `.scroller`는 (다른 목적으로) **`clip-path`**를 쓰고 있었다.
**`clip-path`는 합성 레이어까지 확실히 자른다.** `.peek`만 그 컨테이너 바깥 형제라
보호를 못 받고 있었던 것.

### 수정 (2겹)

```css
.stage { position:absolute; inset:...; clip-path: inset(0); }  /* 근본 */
.peek  { ...; visibility: hidden; }                            /* 안전판 */
```
```js
function setDragX(px){ /* ... */ peekPrev.style.visibility = peekNext.style.visibility = 'visible'; }
function resetDragX(){ /* ... */ peekPrev.style.visibility = peekNext.style.visibility = ''; }
```

안전판을 같이 두는 이유: 클리핑이 어느 브라우저에서 또 안 먹더라도, **드래그 중이
아니면 아예 안 그려지므로** 새어나올 수가 없다.

## 대가

- **`clip-path`는 그 요소를 `position:fixed` 자손의 컨테이닝 블록으로 만든다**
  (`transform`과 같은 효과). 걸기 전에 그 안에 fixed 요소가 없는지 반드시 확인할 것 —
  이 프로젝트에선 토스트·팝업이 한 단계 위(`#app` 직속)라 무사했다.
- 더 상위 컨테이너에 `contain:paint`를 거는 안이 범위는 넓지만, 그 안의 fixed 요소들이
  전부 영향을 받아 위험하다. **범위가 가장 좁은 컨테이너에 `clip-path`**를 거는 쪽이 안전.
- `visibility` 토글은 `setDragX`/`resetDragX` **두 곳에만** 두어야 짝이 어긋나지 않는다
  (transform을 만지는 자리와 정확히 같은 자리).

## 교훈 (같은 repo에서 두 번째다)

**실기기에서만 나는 화면 버그는, 화면을 재서 판정한다.** 코드 읽기로 세운 가설은
그럴듯하지만 반증이 안 되고, 로컬(크롬) 통과는 증거가 아니다. 스크린샷/녹화가 이미
손에 있다면 **눈으로 보지 말고 픽셀을 숫자로 뽑아라** — 대칭·경계 좌표 같은 값 하나가
가설 절반을 즉사시킨다.

같은 프로젝트의 [모바일 제스처 히트박스 함정](shorts-deck-모바일제스처-히트박스-touchaction.md)도
"1차 패치가 그럴듯했지만 실기기에서 그대로"라는 **완전히 같은 실패 모양**이었다.
이 repo의 실기기 버그는 기본적으로 이 함정에 빠진다고 보고 시작할 것.
