---
repo: Easy_CAD_260718
remote: https://github.com/mw3love/Easy_CAD_260718
stack: [PyQt6, QtSvg, Windows, offscreen]
tags: [세그폴트, segfault, QPainter, CompositionMode, SourceIn, DestinationIn, SVG, 아이콘재칠, recolor, QIcon, offscreen플랫폼]
used: []
---

# PyQt6 오프스크린 환경에서 QPainter 합성모드로 SVG 아이콘 재칠 시 세그폴트

## 함정

SVG로 그린 아이콘(코랄 고정색)을 테마별 중립색으로 런타임 재칠하려고 `QPainter`의
`CompositionMode_SourceIn`(또는 `DestinationIn`)으로 색을 덮어씌우는, 아이콘 재칠의 표준
패턴을 썼다. 결과물 자체는 정상 렌더됐지만, `QT_QPA_PLATFORM=offscreen`에서 짧은 시간에
`CanvasWindow`(QMainWindow 기반, 상단바에 이 아이콘 ~18개 사용)를 수십 개 생성하는
스모크 테스트(`python tests/test_easycad.py`, 345종)를 돌리면 **재현 가능한 네이티브
세그폴트**가 발생했다. 항상 같은 지점(누적 33번째 테스트 직후)에서 죽어 시스템 부하로 인한
우연이 아니라 결정론적 버그임을 5회 반복 재현으로 확인(반대로 재칠 없는 버전은 5/5 통과).

시도했지만 전부 재현된 변형(각 5회 반복 테스트, 전부 크래시):
- `QPixmap` 2장(원본 렌더용 + 재칠용) + `SourceIn`
- `QImage` 1장으로 축소(중간 QPixmap 제거) + `SourceIn`
- `CompositionMode_DestinationIn`으로 교체(먼저 단색 채우고 SVG를 소스로 덮어씌우는 순서,
  한 페인터 세션으로 축소)
- `QImage.Format_ARGB32_Premultiplied` → `Format_ARGB32`(non-premultiplied)로 포맷 전환

호출 "빈도"가 원인이라는 가설도 기각됨: `_svg_icon_pixmap` 결과를 (이름,크기,색) 키로
캐싱해 실제 합성 호출을 36회까지 줄여도 크래시가 그대로 재현됐고, 캐시 키를 색 하나로
고정해(테마 분기 없이 항상 같은 색) 캐시 다양성을 아예 없애도 재현됐다 — "캐시된 픽스맵
개수"·"호출 횟수" 둘 다 원인이 아니었다.

## 해법

`QPainter` 합성모드를 **아예 쓰지 않고** 픽셀 단위로 직접 순회하며 재칠:

```python
img = QImage(size, size, QImage.Format.Format_ARGB32)
img.fill(Qt.GlobalColor.transparent)
p = QPainter(img)
p.setRenderHint(QPainter.RenderHint.Antialiasing)
renderer.render(p)   # QSvgRenderer로 원본(코랄) 렌더
p.end()
if color is not None:
    c = QColor(color)
    r, g, b = c.red(), c.green(), c.blue()
    for y in range(size):
        for x in range(size):
            a = img.pixelColor(x, y).alpha()
            if a:
                img.setPixelColor(x, y, QColor(r, g, b, a))   # RGB만 교체, 알파 유지
return QPixmap.fromImage(img)
```

이 버전만 5/5 통과. 아이콘이 22~24px라 픽셀 루프(최대 576회 순회) 비용은 무시 가능하고,
호출 자체도 결과 캐싱으로 사실상 1회성이라 성능 영향 없음.

## 대가

`QPixmap.pixelColor`/`setPixelColor`가 `QPainter` 합성모드보다 훨씬 느린 API이지만, 대상이
아이콘 크기(수백 픽셀)+캐시 적용이라 실질 비용은 무시 가능. 더 큰 이미지(예: 사용자 사진
전체)를 재칠해야 하는 상황이라면 이 방식은 부적합 — 그런 경우 이 함정을 다시 만나면
`QImage::bits()`로 numpy 배열 뷰를 얻어 벡터 연산하는 대안을 먼저 검토할 것(픽셀 루프
그대로 확장하면 너무 느림).

정확한 근본 원인(왜 `CompositionMode_SourceIn`/`DestinationIn`이 오프스크린 플랫폼
플러그인에서 불안정한지, PyQt6 바인딩 버그인지 Qt6 자체 오프스크린 래스터라이저 버그인지)은
확인하지 못했다 — 재현 스크립트로 어떤 조합이 죽고 사는지만 확정했다.
