---
repo: Easy_CAD_260718
remote: https://github.com/mw3love/Easy_CAD_260718.git
stack: [PyQt6, QGraphicsScene, Windows]
tags: [QGraphicsItem, QGraphicsScene.render, QGraphicsView.grab, setParentItem, 자식 아이템, paint 오버라이드 무시, QPainterPath moveTo lineTo gap, 테두리 trim, offscreen 렌더]
used: []
---

# QGraphicsItem: 자식이 있는 아이템은 paint()에서 그린 QPainterPath의 gap이 씬 렌더에 반영 안 됨

## 함정
장비(호스트) 아이템이 자식(포트)이 걸친 구간만큼 테두리를 끊어 그리려고, `paint()`를
오버라이드해 `QPainterPath`를 여러 개의 분리된 subpath(moveTo/lineTo, 중간에 gap)로
구성해 `painter.drawPath()`로 그렸다.

- `item.paint(painter, option, None)`을 **직접 호출**하면(QImage에 수동으로) gap이
  정확히 보임 — 경로 자체(`elementCount()`)도 매번 정확히 gap 포함 구조였음.
- 그런데 `QGraphicsScene.render()`나 `QGraphicsView.grab()`(정상적인 Qt 씬 렌더
  파이프라인)로 그리면, **그 아이템에 Qt 자식(`setParentItem`으로 붙인 것)이 하나라도
  있을 때만** gap이 사라지고 완전히 닫힌 도형으로 렌더링됨.
- 자식을 실제 `setParentItem`으로 붙이지 않고 (좌표만 별도 dict에 저장하는 식으로)
  "가짜 자식"만 흉내내면 정상적으로 gap이 보임 — 즉 **진짜 Qt parent-child 관계 자체가
  트리거**.
- `paint()` 내부에 `print`를 심어 매번 올바른 분기(gap 있는 경로)를 타는 것도 확인함.
  즉 **내 코드는 매번 정확한 데이터를 painter에 넘기는데, 최종 픽셀에만 반영이 안 됨.**
- 시도했으나 전부 무효: `prepareGeometryChange()` 호출, `item.update()` 호출,
  antialiasing 끄기, `_base_shape()`(shape()의 클릭영역 경로)도 gap 반영하도록 동기화.
- 정확한 Qt/PyQt6 내부 원인은 특정 못함(Not-tested) — 자식이 있을 때 씬 렌더가 아이템을
  다루는 방식(오파크 영역 계산/배치 컴포지팅 등)이 단순 `paint()` 가상 디스패치와 다르게
  동작하는 것으로 추정.

## 해법
문제가 있는 쪽(자식을 가진 부모가 자기 paint()에서 자기 형태를 분절해 그리는 것)을
포기하고, **자식(포트) 쪽이 자기 paint()에서 자기 자신을 그리기 직전에 자기 영역
(`self.rect()`)을 캔버스 배경색으로 먼저 덮어 칠하고, 그 위에 자기 몸체를 그리는** 방식으로
뒤집었다. 포트 자신은 자식이 없는 말단(leaf) 아이템이라 이 버그를 안 타서 정상 렌더링된다.
결과적으로 "부모 테두리가 포트 자리만큼 끊겨 보인다"는 시각효과는 동일하게 달성된다.

부수 이점: 포트를 드래그로 옮기거나 부모가 리사이즈돼도, 커버 패치는 포트 자신의 `paint()`가
새 위치에서 다시 호출될 때 자동으로 같이 따라간다 — 부모 쪽에 별도 무효화/재계산 트리거를
따로 안 심어도 됨(이동은 Qt 부모-자식 변환이 공짜, 커버는 포트 paint()에 종속).

## 대가
- 화면 렌더링은 "진짜 분절"이 아니라 "덮어그리기"라, 캔버스 배경이 **단색**이어야 자연스럽다
  (그리드 점이 배경 위에 그려진다면 포트 밑 그리드 점 몇 개가 사라지는 정도는 허용 범위로 판단).
- DXF 내보내기처럼 QPainter를 안 거치는 별도 경로(파일 직접 작성)는 이 버그와 무관하므로,
  그쪽은 원래 계획대로 진짜 분절된 세그먼트 데이터(`QPainterPath`를 segment별로 분해)를
  그대로 써도 된다 — 화면 렌더링 우회와 DXF 내보내기 정확성은 서로 독립적인 문제.
