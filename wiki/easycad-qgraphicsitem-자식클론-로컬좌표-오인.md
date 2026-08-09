---
repo: Easy_CAD_260718
remote: https://github.com/mw3love/Easy_CAD_260718
stack: [PyQt6, QGraphicsScene]
tags: [QGraphicsItem, clone, setParentItem, 좌표계, 씬좌표, 로컬좌표, 포트, 복제]
used: []
---

# QGraphicsItem 자식(setParentItem)을 clone()할 때 pos()를 씬좌표로 오인 — 호스트가 원점 근처면 안 드러나는 함정

## 함정
"복제 후 델타만큼 이동" 관용구 `dup.setPos(src.pos() + delta)`는 src가 최상위(부모 없음)
아이템일 땐 정확하다(top-level item의 `pos()`가 곧 씬좌표이므로). 그런데 Easy CAD의
포트는 부착 시 `port.setParentItem(host)`로 **진짜 Qt 자식**이 되고, 이 상태의
`port.pos()`는 **호스트 기준 로컬좌표**다. `_qc_create`(큐닷 클릭=도형복제) 코드가 이
구분을 모르고 `dup.setPos(src.pos() + (center - sr.center()))`를 그대로 썼다 — `dup`은
새로 만든 최상위 아이템이라 이 setPos는 씬좌표로 해석되는데, 더해지는 `src.pos()`는
로컬좌표라 값이 완전히 어긋난다.

**재현이 늦어지는 이유**: 호스트가 씬 원점(0,0) 근처에 있으면 "로컬좌표 ≈ 씬좌표"가
우연히 성립해 버그가 안 드러난다. 실제로 이 프로젝트 자체 테스트를 `_mk_pen_rect(w, x=500,
y=500, ...)`(좌표를 `rect()` 자체에 굽고 `pos()`는 (0,0) 유지)로 짰다가 처음엔 버그를 못
잡았다 — `setPos()`로 진짜 위치를 옮긴 호스트로 다시 짜야 재현됐다. 사용자에겐 실사용
스크린샷(포트 옆에 나와야 할 복제가 화면 밖 엉뚱한 자리로 튀고 화살표만 길게 이어짐)으로
먼저 드러났다.

## 해법
`dup`(항상 최상위)의 목표 위치를 **dup 자신의 로컬 rect만 기준으로 목표 씬좌표에서
역산**한다 — `src.pos()`를 아예 참조하지 않는다:

```python
dup.setPos(center - dup.rect().center())   # center = 목표 지점의 씬좌표
```

무회전 최상위 아이템에서는 기존 공식과 대수적으로 완전히 동일함을 확인했다
(`sr.center() == src.pos() + src.rect().center()`이므로
`src.pos() + (center - sr.center()) == center - src.rect().center()`,
그리고 `dup.rect() == src.rect()`) — 즉 회귀 없이 부모 유무와 무관하게 항상 맞는 상위
호환 공식이다.

## 대가
없음 — 기존 공식의 상위 호환(수학적으로 동일 + 버그 케이스 추가 해결)이라 다른 곳을
손볼 필요가 없었다.

## 일반화된 교훈
아이템이 `setParentItem`으로 부모를 가질 수 있는 구조라면, "복제 후 재배치"·"델타 이동"
류 코드에서 `pos()`를 씬좌표로 가정하는 곳을 전부 의심할 것. 이런 버그를 잡는 테스트를
짤 때는 **호스트를 씬 원점에서 떨어뜨려 놓아야** 한다 — 원점 근처에서 짠 테스트는
로컬==씬이 우연히 성립해 통과해버린다(가짜 그린).
