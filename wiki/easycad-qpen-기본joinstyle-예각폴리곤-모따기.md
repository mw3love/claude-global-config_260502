---
repo: Easy_CAD_260718
remote: https://github.com/mw3love/Easy_CAD_260718
stack: [PyQt6, QPainter, QGraphicsItem]
tags: [QPen, joinStyle, BevelJoin, MiterJoin, RoundJoin, drawPolygon, 화살촉, arrowhead, 모따기, chamfer, 어깨깎임, 예각, 고배율재현, 줌배율, 안티에일리어싱, 렌더버그재현]
used: []
---

# QPen의 기본 joinStyle이 BevelJoin이라 예각 폴리곤(화살촉) 꼭짓점이 잘려나간다

## 함정

직각 커넥터(`_PolyArrowItem`)의 화살촉 삼각형만 어깨 두 곳이 45°로 깎여 보인다는 실사용
보고를 받았다. 곡선·직선 화살표(`_ArrowItem`)는 멀쩡했다.

**3라운드 동안 재현에 실패했다.** 시도한 재현 조건:
- 실제 그리기 도구로 마우스 드래그해 직각 화살표 생성(굵은 펜, 기본 둥근 모서리) → 깨끗
- 직선/곡선 화살표 tip을 도형 테두리에 바인딩 → 깨끗
- 사용자가 보낸 `.ecad` 파일을 그대로 로드해서 렌더 → 깨끗

그때마다 "재현 안 됨"으로 보고했고, 사용자는 매번 같은 증상을 다시 스크린샷으로 보냈다.

**재현 실패의 진짜 원인은 「줌 배율」이었다.** 화살촉을 그리는 펜은 폭이 `1`로 **고정**이라
(도형 펜 두께와 무관), bevel로 깎여 나가는 크기도 항상 ~0.5 씬단위로 고정된다. 즉:
- 100% 줌 → 0.5 px → 안티에일리어싱에 완전히 묻혀 **안 보인다**
- 사용자가 본 배율(실측 **2863%**) → ~14 px → **확 보인다**

내 재현은 전부 100%~600% 배율이었다. 버그는 처음부터 계속 거기 있었는데, 관찰 배율이
부족해 "없다"고 결론 낸 것이다. 사용자가 배율 표시(미니맵 `2863%`)가 찍힌 스크린샷을
보내준 뒤에야 같은 배율로 렌더해 즉시 재현했다.

## 해법

`QPen`을 생성할 때 **`joinStyle`을 반드시 명시**한다. Qt의 `QPen` 기본 joinStyle은
`BevelJoin`이고, bevel은 예각 꼭짓점의 바깥 확장부를 직선으로 잘라낸다(= 모따기). 화살촉
삼각형의 어깨는 30° 예각이라 크게 잘린다.

```python
# 버그 — joinStyle 미지정 → 기본 BevelJoin → 어깨 깎임
painter.setPen(QPen(self._color, 1))
painter.setBrush(QBrush(self._color))
painter.drawPolygon(QPolygonF(self._head_points()))

# 수정 — RoundJoin 명시
painter.setPen(QPen(self._color, 1, Qt.PenStyle.SolidLine,
                    Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin))
```

같은 앱의 `_ArrowItem`(곡선·직선)은 처음부터 `RoundJoin`을 명시해 두었기에 멀쩡했다 —
**"A만 이상하고 B는 멀쩡"할 때 두 렌더 경로의 펜 생성 코드를 나란히 diff하는 것이 가장
빠른 진단**이었는데, 그걸 3라운드 뒤에야 했다.

**회귀 테스트는 픽셀로 못 박았다.** 이런 종류(눈으로 3라운드 못 잡은 시각 버그)는 로직
어서션으로 못 잡으므로, `QGraphicsScene.render()`로 실제 paint() 경로를 QImage에 그린 뒤
어깨 꼭짓점 **바깥 0.4 단위** 지점의 픽셀이 칠해졌는지 확인한다(RoundJoin이면 반지름 0.5
원으로 덮이고, BevelJoin이면 잘려 배경색). 판정 거리는 두 join을 각각 렌더해 실측으로
정했다 — 0.30~0.50 구간에서 갈리고, 0.60부터는 둘 다 배경색이라 0.4가 안전 중앙값.
테스트를 넣은 뒤 **수정을 일시적으로 되돌려 실제로 실패하는지 확인**했다(통과하는 테스트가
진짜 그 버그를 잡는지 검증하지 않으면 무의미하므로).

## 대가

`RoundJoin`은 tip(화살촉 끝점)도 반지름 0.5만큼 둥글려서, 이론상 극단적 고배율에서는
바늘처럼 뾰족하지 않다. `MiterJoin`이 가장 뾰족하지만 miter limit을 넘으면 자동으로
bevel로 폴백해 같은 증상이 재발할 수 있어 택하지 않았다 — 기존 `_ArrowItem`과 렌더를
일치시키는 편(사용자가 "곡선·직선은 괜찮다"고 한 그 렌더)이 더 중요했다.

## 교훈 (다른 렌더 버그에도 적용)

**"재현 안 됨"으로 결론 내기 전에 사용자가 본 것과 같은 관찰 조건(줌 배율·창 크기·테마)을
맞췄는지 확인할 것.** 크기가 펜 폭·화면 px에 고정된 결함은 배율이 낮으면 원리적으로
안티에일리어싱에 묻힌다. 사용자 스크린샷에 배율 표시가 있으면 그 숫자를 먼저 읽는다.
