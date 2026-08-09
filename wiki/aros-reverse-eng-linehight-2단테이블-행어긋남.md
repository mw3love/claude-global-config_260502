---
repo: AROS_Reverse_Eng_260803
remote: https://github.com/mw3love/AROS_Reverse_Eng_260803.git
stack: [stdlib-only 웹 대시보드, http.server, sqlite3, 순정 JS+SVG]
tags: [line-height, 테이블 행높이, 2단 컬럼 뷰, 서브픽셀, Windows ClearType, 폰트 폴백, 픽셀 스크린샷 대조]
used: []
---

# 좌우 나란한 두 <table>의 행 구분선이 아래로 갈수록 어긋남

## 함정

`tools/dashboard.html`의 "2단" 뷰는 같은 페이지의 포인트 목록을 두 개의 독립된
`<table>` 엘리먼트로 좌우 배치한다(`renderXTablePaged` → `xTableHTML`을 컬럼마다
따로 호출). 사용자가 "아래쪽 행일수록 좌우 줄이 안 맞는다"고 보고.

1차 시도: `.anom-badge`(이상탐지 뱃지)가 비동기로 늦게 로드되며 행 높이를 바꾸는
줄 알고 `display:none` 대신 `visibility:hidden`으로 항상 공간을 예약하도록 고침
(2026-08-08). 다음날 사용자가 "지금도" 동일 증상 재보고 — 강제 새로고침 후에도
재현됨. **1차 시도는 무관한 다른 버그를 고친 것뿐이었다.**

라이브 DOM에서 `getBoundingClientRect()`로 두 컬럼 12행을 비교하면 완벽히
일치(diff=0) — 헤드리스 Linux Chromium(개발 환경)에서는 애초에 이 증상이
재현되지 않았다. "내 환경에서 안 보이니 이미 고쳐진 것"이라고 결론 내리기
직전, 사용자가 보낸 실제 스크린샷을 못 믿고 픽셀 단위로 대조해본 것이
결정적이었다.

## 해법

사용자 스크린샷 파일(PasteFlow가 저장한 실제 경로)을 PIL로 열어, 좌/우 컬럼의
"거의 빈 여백" 칼럼(사이트 컬럼 부근 x좌표)을 세로로 스캔해 배경↔보더 색
전이가 일어나는 y좌표를 각 컬럼별로 뽑아 나열:

```python
from PIL import Image
im = Image.open(path).convert("RGB")
px = im.load()
def border_rows(x, y0, y1, thresh=10):
    rows = []
    for y in range(y0+1, y1-1):
        d1 = diff(px[x,y], px[x,y-1]); d2 = diff(px[x,y], px[x,y+1])
        if d1 > thresh and d2 > thresh*0.3: rows.append(y)
    return rows
```

좌: `419,466,513,560,607,654,701,748,795,842,889,936` (47px 등간격, 12행 전부)
우: `419,466,513,560,607,654,701,747,793,839,885,931` (7행까지는 완전 일치,
8행부터 46px 간격으로 바뀌어 12행에서 -5px까지 누적)

어긋남이 시작되는 8행이 마침 그 페이지에서 그룹이 바뀌는 지점(`_AI4`→`_AI5`)과
일치 — 텍스트 glyph 조합이 바뀌는 지점에서 발생한다는 단서.

**진짜 원인**: `.x-name-line`/`.x-sub`에 `line-height`를 지정하지 않아
브라우저 기본값(`normal`)에 맡겨져 있었다. `normal`은 그 줄에 실제로 쓰인
glyph들의 폰트 ascent/descent/line-gap을 조회해 자연 line-height를 계산하는데,
같은 font-size·font-family라도 한글/영문/괄호 등 glyph 폴백 조합에 따라 그
값이 미세하게(서브픽셀) 달라질 수 있다. 이게 디바이스 픽셀로 반올림되며
어느 행부터 실제 렌더 높이가 1px 줄어들고, 그 아래 모든 행이 그만큼씩
밀려 누적된다. Windows의 폰트 힌팅/ClearType 특성으로 추정(리눅스 헤드리스
Chromium에서는 폰트 스택이 달라 애초에 재현되지 않았음 — 그래서 라이브 DOM
비교만으로는 이 버그를 못 잡는다).

고정:

```css
.x-name-line { line-height: 15px; }
.x-sub { line-height: 13px; }
```

`line-height`를 고정 px로 박으면 폰트 메트릭 조회 자체를 우회하므로, 어떤
glyph 조합이 오든 그 줄의 계산된 높이는 항상 동일한 산술값이 된다.

## 대가

없음 — 순수 CSS 한 줄 추가라 레이아웃 부작용 없음(재확인: 텍스트 잘림 없음,
행 높이 47px→44.5px로 살짝 줄었지만 좌우 컬럼 모두 균일).

## 일반화

"좌우 두 개의 독립된 DOM 서브트리가 시각적으로 나란히 정렬돼야 하는데
자꾸 어긋난다" 증상을 만나면, `line-height: normal`을 의심할 것 — 특히
CJK/Latin 혼용 텍스트가 행마다 다른 glyph 조합으로 나타나는 다국어 UI에서
잘 걸린다. 그리고 **헤드리스 Linux Chromium에서 재현 안 된다고 "버그 없음"
결론 내리지 말 것** — Windows 실기기의 폰트 힌팅 차이로만 나타나는 서브픽셀
버그가 실제로 있다. 이럴 땐 사용자가 보낸 스크린샷을 PIL로 픽셀 단위 대조하는
게 라이브 DOM 측정보다 훨씬 신뢰도 높은 진단 도구였다.
