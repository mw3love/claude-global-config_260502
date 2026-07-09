---
repo: PasteFlow
remote: https://github.com/mw3love/Paste_flow.git
stack: [PyQt6, QGraphicsScene]
tags: [주석편집, 회전핸들, 크기조절핸들, QGraphicsItem, 잔상, 피벗, 스냅]
reuse: AI CAD 프로젝트 주석/도형 편집에 직접 재사용 후보
used: []
---

# QGraphicsItem 회전·크기조절 핸들

캔버스 위 아이템을 선택하면 크기조절 핸들과 회전 핸들이 붙는 편집 UI.

## 회전

- **중심 피벗**으로 `setRotation` 을 건다.
- `Shift` 누르면 **15° 스냅**.
- 회전 핸들 **원의 지름 = 사각형 한 변**의 길이로 잡으면 크기에 관계없이 비율이 맞는다.
- 회전 핸들을 잇는 **줄기(stem)의 gap은 고정값**으로 둔다 (스케일에 따라 늘어나면 어색해짐).

## 크기조절

- `scale` 을 클램프하고, 핸들 자체 크기는 스케일에 따라 **가변**으로 둔다.

## 함정 — 선택 해제 시 핸들 잔상

`content_rect` 와 `boundingRect` 를 **분리**하지 않으면, 선택을 해제할 때 핸들이 있던 자리에 잔상이 남는다.

**해법:** `boundingRect` 를 `content_rect ∪ 핸들 영역` 으로 **상시 예약**한다. 선택 여부와 무관하게 항상 핸들 영역까지 포함시켜야 무효화 영역이 맞는다.
