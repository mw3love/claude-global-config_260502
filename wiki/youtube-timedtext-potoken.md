---
repo: youtube_dual_subtitle
remote: https://github.com/mw3love/youtube_dual_subtitle.git
stack: [Chrome MV3, TypeScript]
tags: [YouTube, timedtext, PoToken, pot, 자막캡처, 콘솔probe, fetch훅, performance-buffer]
used: []
---

# YouTube timedtext PoToken은 영상 바인딩 — 크로스-비디오 이식 불가 (+ 콘솔 probe 함정 3종)

## 함정 1 — pot 이식으로 페이지 의존을 끊으려던 시도 (기각)

`/api/timedtext`는 raw `baseUrl`(playerResponse에 든 것)로 그냥 fetch하면 **200 + empty body**다. 통과하려면 페이지가 붙이는 `pot`(PoToken)이 필요하다. 그래서 확장은 "페이지가 그 영상 자막을 한 번 fetch하게 만들고(CC 강제 클릭) 그 URL의 pot을 빌려 쓰는" 구조인데, 이 의존 때문에 **유튜브 자막이 '사용 안 함'이면 데이터 경로가 통째로 없다**(+ 우리가 CC를 강제로 켜는 부작용).

"세션 안의 **다른 영상** timedtext URL에서 `pot`만 떼어 이 영상 baseUrl(서명은 유효)에 이식하면 되지 않나" → **안 된다.**

결정 실험(단일 변수): 이 영상의 **정상 페이지 URL** 그대로 두고 `pot` 하나만 다른 영상 것으로 교체.

```
mine 110545   (정상 URL 그대로)
swap 0        (pot만 남의 영상 것으로 교체)
```

나머지 파라미터(`expire`/`signature`/`sparams`/`c`/`cver`…)가 전부 유효한 상태였으므로 **`pot`은 콘텐츠(영상) 바인딩**으로 확정. 세션 공용이 아니다. `pot` 자체 생성은 BotGuard 챌린지가 필요해 확장에서 비현실적.

→ **결론: "페이지가 그 영상의 timedtext를 fetch하게 만든다"가 유일한 데이터 경로.** 자막 UI를 강제로 켜는 부작용은 제거 불가능한 구조적 대가.

## 함정 2 — 콘솔 probe가 자기 요청에 오염됨 (가짜 실패를 만든다)

probe가 `window.fetch`를 훅해 timedtext URL을 모으는데, **probe 자신이 쏘는 실험용 fetch도 그 훅에 잡혀** 목록에 섞인다. 그 결과 "이 영상의 정상 URL"을 고를 때 **pot 없는 우리 실험 URL**이 뽑혀 `mine 0`이 나왔다 — 실제로는 정상 URL이 110545를 반환하는데도.

**해법:** 수집 목록에서 `pot` 파라미터가 실제로 붙은 URL만 필터(`.filter(x => x.searchParams.get('pot'))`). probe의 raw 요청은 pot이 없어 자동 배제된다.

## 함정 3 — `performance.getEntriesByType('resource')`로 URL을 못 찾는다

첫 probe는 resource timing 기록에서 timedtext URL을 뒤졌는데 항상 "없음"이었다. 원인은 **resource timing 버퍼가 기본 250개**인데 YouTube가 그걸 순식간에 넘겨 timedtext 엔트리가 밀려나기 때문. (`setResourceTimingBufferSize`를 미리 키우거나) **fetch/XHR을 직접 훅해 모으는 방식**으로 바꿔야 한다. SPA 이동은 document가 유지되므로 `window.__X`에 모아 둔 값이 다음 영상까지 살아남는다 — 크로스-비디오 실험이 가능한 이유.

## 함정 4 — 사용자에게 복붙시킬 콘솔 스크립트는 "줄바꿈에 면역"이어야

한 줄로 압축한 probe가 사용자 터미널/채팅을 거치며 **자동 줄바꿈**되어 반복 실패했다:
- `const L = async\n u => …` → **`async`와 화살표 사이의 줄바꿈은 SyntaxError**(ASI 함정).
- `console.log('내 정상 URL len\n =', …)` → 긴 **한글 문자열이 줄 중간에서 잘려** `Invalid or unexpected token`.

**해법:** 압축 one-liner를 고집하지 말고 **처음부터 짧은 여러 줄**(각 줄 80자 미만)로 쓴다. 문자열 리터럴은 짧은 ASCII(`'mine'`, `'swap'`)로. `async function f(){}` 선언형을 쓰면 async-arrow ASI 함정을 피한다.

## 대가

없음(진단 전용). 단 probe를 돌린 탭은 `window.fetch`가 훅된 상태로 남으므로 실험 후 새로고침 권장.
