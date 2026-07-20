---
repo: Easy CAD
remote: https://github.com/mw3love/Easy_CAD_260718.git
stack: [PyQt6, QGraphicsScene, Windows]
tags: [QGraphicsItem, 자식아이템, 라벨, _sync_label, scene멤버십, 라벨쏠림, 중앙정렬, devicePixelRatio, 헤드리스, offscreen, view.grab, 폰트, 맑은고딕, 삽입헬퍼]
used: []
---

# Qt 자식 라벨의 위치동기는 부모가 씬에 든 뒤라야 동작 (씬 전엔 조용히 no-op)

## 함정
삽입 헬퍼가 도형을 만들며 라벨을 붙일 때, **addItem 전에** `ensure_label().setPlainText()`를 호출하면 라벨이 도형 **좌상단(부모 로컬 0,0)** 에 박혀 "글자가 위/왼쪽으로 쏠려" 보인다. 원인: `_CenterLabelMixin._sync_label`이 `_label_alive()`(= `lbl.scene() is not None`)를 가드로 두는데, 부모가 아직 씬에 없으면 자식 라벨의 `scene()`도 None → **위치 계산 없이 조용히 return**. 라벨은 초기 pos (0,0)에 그대로 남는다.

3번 헛수정한 막다른 길(전부 **엉뚱한 원인**이었다):
- 폰트 세로 편향(baseline·ascent/descent) → `_ink_center_dy`로 잉크 픽셀 중심 보정. ±2px 다듬기일 뿐 쏠림의 원인 아님.
- `QFontMetricsF`/`tightBoundingRect` 공식 → 실렌더와 부호까지 반대라 무의미.
- `devicePixelRatio=1.25`(Windows 125% 배율) 의심 → dpr 격리 뷰에서도 중앙이라 무관.

**왜 못 잡았나:** 자체검증을 전부 dpr 1.0 렌더(헤드리스 tofu·`scene.render`)로만 했는데, 그 테스트 경로는 우연히 **addItem 후 `_sync_label`** 하는 순서라 중앙으로 보였다. 사용자 화면(실제 위젯 paint)만이 **addItem 전 sync** 상태를 드러냈다. 관측 대상이 사용자 화면과 달라, 성실한 조사가 열등한 가설(폰트/dpr)에 근거·추천 딱지를 붙여줬다.

## 해법
씬에 넣은 **뒤에** 위치동기를 재호출한다.
```python
self._scene.addItem(it)
it._sync_label()          # 노드 라벨 — 씬 멤버십 확보 후라야 중앙 정렬됨
# 엣지(화살표) 라벨도 동일. build_elbow가 무변경이면 내부 sync가 생략되므로 명시적으로:
self._scene.addItem(arr)
arr.build_elbow()
arr._sync_label()
```
삽입 헬퍼는 "**addItem → sync**" 순서를 강제할 것. (일반 그리기 경로는 도형을 먼저 씬에 넣고 더블클릭으로 라벨을 달아 이 함정에 안 빠진다 — 라벨을 코드로 미리 붙이는 삽입/가져오기 경로만 위험.)

## 재현·검증 기법 (헤드리스로는 못 본다)
- **헤드리스(`QT_QPA_PLATFORM=offscreen`)엔 한글 폰트가 없어** 라벨이 tofu(□)로 떠서 *정렬*을 눈으로 못 본다(부착 여부만 확인됨).
- **비-헤드리스 Windows python**(그냥 `python`, offscreen 아님)은 실폰트(맑은 고딕)를 래스터화하므로, `QGraphicsView.grab().toImage()`로 **사용자 화면을 그대로 재현**해 라벨/도형 픽셀 중심을 측정할 수 있다. 색을 도형=파랑·라벨=초록처럼 구별하면 팔레트/툴바 픽셀과 안 겹쳐 격리 측정된다.
- **주의:** `scene.render()`가 "중앙"이라고 위젯 paint도 중앙이라 단정 말 것 — 둘이 갈릴 수 있다(이 함정에서 갈렸다). 사용자가 보는 경로(`grab`)로 검증하라.

## 대가
`_sync_label`이 `_ink_center_dy`에서 오프스크린 렌더를 하므로 라벨 텍스트 변경 시 ~2.5ms/label(같은 텍스트·폰트크기는 캐시). 짧은 라벨엔 무해.
