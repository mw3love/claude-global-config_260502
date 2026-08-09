---
repo: Easy_CAD_260718
remote: https://github.com/mw3love/Easy_CAD_260718
stack: [PyQt6, QGraphicsView, mousePressEvent]
tags: [이벤트우선순위, 모디파이어, Alt, 드래그, hover, qc-dot, 조기반환, 포트]
used: []
---

# 특수 히트존(hover-port/qc-dot) 조기반환이 범용 모디파이어(Alt)보다 먼저 press를 가로챔

## 함정
"Alt+드래그 = 제자리 복제"는 이 앱에서 아이템 종류를 가리지 않는 전 도형 공통 규칙
(`_maybe_alt_drag_copy`)이다. 그런데 `mousePressEvent`의 select 도구 분기에서, 그보다
먼저 실행되는 특수 히트존 감지(`_hover_port_at` — 미선택 도형의 4방향 접속점 근처 press를
잡아 "드래그하면 화살표, 클릭하면 도형복제"로 처리하는 코드)가 **Alt 모디파이어를 전혀
확인하지 않고** 조건에 맞으면 조기 `return`했다. 그 결과 미선택 포트(또는 아무 도형의
접속점 근처)를 Alt+드래그하면 `_maybe_alt_drag_copy`에 도달하지도 못한 채 "화살표 뽑기"로
새어버렸다 — 사용자는 "Alt+드래그해도 복제가 안 되고 이상한 화살표만 생긴다"고 보고.

이 프로젝트는 과거 "포트만 특수 취급"을 4라운드 스턱루프 끝에 전부 되돌리고 "포트=평범한
도형"으로 수렴한 전례가 있다(`easycad-포트특례-병렬상호작용시스템-보편규칙전환.md` 참조).
그래서 이번에도 "포트일 때만 Alt를 특별히 봐준다"는 특례를 추가하면 같은 함정을
반복하는 셈이었다.

## 해법
아이템 종류로 예외를 만들지 않고, **모디파이어 우선순위를 조기반환 조건 자체에 승격**한다:

```python
if event.button() == Qt.MouseButton.LeftButton and not (
        event.modifiers() & (Qt.KeyboardModifier.ShiftModifier
                              | Qt.KeyboardModifier.AltModifier)):
    hp = self._hover_port_at(vpos)
    ...
```

Alt가 눌려 있으면 이 특수 히트존 자체를 건너뛰고 아래(빈 영역 판정 → `_maybe_alt_drag_copy`
→ Qt 기본 드래그)로 흘러가게 만든다 — 포트든 다른 도형이든 동일하게 적용되는 규칙이라
특례 지점이 늘지 않는다.

## 대가
없음 — Shift(다중선택)에도 이미 같은 패턴(비트마스크 OR)으로 처리돼 있어 자연스럽게
확장한 것.

## 일반화된 교훈
여러 겹의 클릭/드래그 핸들러(조기 return 체인)가 있는 캔버스 앱에서 새 전역 제스처
(Alt+드래그, Ctrl+클릭 등)를 추가하거나 검증할 때는, 그 제스처가 실제로 통과해야 하는
모든 조기-반환 분기를 먼저 나열하고 우선순위를 명시적으로 정할 것 — "규칙은 이미
있는데 안 먹힌다"는 보고는 대개 그 규칙에 도달하기 *전에* 다른 특수 분기가 먼저 가로채고
있다는 신호다. 그리고 아이템별 특례보다 모디파이어 우선순위 승격 쪽이 항상 특례 지점을
덜 늘린다.
