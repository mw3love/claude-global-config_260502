---
repo: Easy_CAD_260718
remote: https://github.com/mw3love/Easy_CAD_260718
stack: [PyQt6, Windows]
tags: [QGraphicsItem, boundingRect, prepareGeometryChange, 캐시무효화, non-virtual, setFont, 다중선택드래그, 성능]
used: []
---

# QGraphicsItem.boundingRect() 캐시 — 이벤트 무효화 대신 값 비교

## 함정

다중선택 그룹드래그(200개+) 성능 조사에서, `boundingRect()`가 매 호출(Qt가 인덱싱·
히트테스트·페인트 판정마다 매우 자주 부름) 비싼 기하 계산(포트/핸들 위치 재투영)을
처음부터 다시 도는 게 병목이었다. 첫 시도는 다른 클래스(`_PolyArrowItem`)에서 이미
검증된 패턴 — `_geom_version` 정수 캐시 키 + 기하가 바뀌는 모든 지점에서
`prepareGeometryChange()`를 부르며 버전 증가 — 를 이 클래스(공용 mixin,
`_HandleResizeMixin`)에도 그대로 확장하는 것이었다. 실측(성능)까지는 잘 됐지만, 회귀
테스트 하나가 즉시 걸렸다: 라벨(`QGraphicsTextItem` 상속)의 `setFont()` 호출 후에도
옛 boundingRect가 캐시에 남아 라벨 위치가 11~32유닛 어긋났다.

**원인**: `QGraphicsItem.prepareGeometryChange()`는 Qt C++에서 **non-virtual**이다.
`QGraphicsRectItem.setRect()`/`QGraphicsTextItem.setFont()`/`setPlainText()` 같은
**Qt 네이티브 메서드가 내부적으로 부르는 prepareGeometryChange는 Python 서브클래스의
오버라이드를 타지 않는다** — 그래서 "버전키를 올리는" 우리 쪽 훅이 안 불려 캐시가
조용히 stale해진다. `_PolyArrowItem`의 원래 캐시가 안전했던 이유는 그 클래스의 기하
변경이 전부 이 코드베이스 자체 파이썬 메서드(`_set_endpoint` 등)를 거쳐서였다 —
**native setRect()/setFont() 같은 Qt 자체 API로 기하가 바뀔 수 있는 클래스에는 이
"이벤트 기반 무효화" 캐시 패턴을 그대로 옮기면 안 된다.**

## 해법

이벤트/시그널 무효화에 의존하지 않는다. 대신 `boundingRect()`가 **어차피 매 호출
계산해야 하는 저비용 값**(이 프로젝트에서는 `content_rect()`·`scale`·`handle_px`)을
캐시 **키**로 직접 비교해, 그 키가 지난 호출과 같으면 비싼 부분(포트/핸들 재투영)의
결과를 재사용하고 다르면 재계산한다.

```python
key = (cr.x(), cr.y(), cr.width(), cr.height(), s, h)
if self._bbox_cache_key == key:
    return self._bbox_cache_rect
... # 비싼 계산
self._bbox_cache_key = key
self._bbox_cache_rect = result
return result
```

핵심은 **"이벤트가 와야 무효화"가 아니라 "매번 직접 확인"**이라는 것 — native
`setFont()`/`setRect()` 경로가 캐시를 우회할 여지 자체가 없다(그 호출들이 만든 새
`content_rect()` 값을 다음 호출이 그대로 다시 읽어서 비교하므로, 무효화 훅이 필요
없다). `content_rect()`가 Qt 네이티브 계산(`super().boundingRect()`)으로 귀결되는
서브클래스라면 이 비교가 항상 최신 상태를 본다.

실측(200개 다중선택 그룹드래그): 121.81ms→34.84ms(3.5배), `boundingRect()` 누적시간
33배 감소. 회귀 테스트(라벨 폰트변경 케이스 포함) 전원 통과.

## 대가

키 비교 대상 값(`content_rect()`/`scale`/`handle_px`) 자체는 캐시 히트 시에도 매번
다시 계산해야 한다 — "완전 스킵"은 아니고 "그 값들로 만드는 비싼 파생 계산만 스킵".
이 값들이 저비용(단순 산술)인 클래스에서만 이 패턴이 유효하다 — 그 자체가 비싸면
효과가 줄어든다.
