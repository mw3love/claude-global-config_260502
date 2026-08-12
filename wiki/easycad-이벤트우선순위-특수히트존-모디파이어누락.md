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

## 재발 (2026-08-10, §8 항목17 TRIM/EXTEND)
같은 클래스의 버그가 **한 세션 안에서 3번 더** 나왔다 — 이번엔 모디파이어(Alt)가 아니라
새 **도구**(`current_tool == "trim"`)가 조기반환 체인을 못 뚫는 문제였음에도 패턴은 동일:

1. `_connect_port_at`(qc-dot 접속점) — 선택된 도형의 qc-dot 근처 press를 도구 무관하게
   가로채, EXTEND 목표 지점이 그 도형의 qc-dot과 겹치면(흔함 — 원래 붙어있던 자리라서)
   TRIM/EXTEND 분기에 도달도 못 함.
2. `mouseDoubleClickEvent`의 라벨편집 분기 — 같은 자리를 빠르게 두 번 누르면(EXTEND
   재시도가 전형적으로 이럼) Qt가 두 번째 클릭을 `mousePressEvent`가 아니라
   `mouseDoubleClickEvent`로 보내는데, 그 핸들러의 "선/화살표 더블클릭=라벨편집"이
   도구 무관하게 먼저 채감.
3. `_selected_endpoint_item`(선택된 선의 끝점 드래그 핸들) — EXTEND 대상 선이 선택된
   상태면(방금 자른 직후라 흔함) 그 끝점 핸들이 화면상 정확히 EXTEND를 눌러야 할 그
   자리를 뒤덮어 클릭을 가로챔.

**셋 다 위 교훈("모든 조기-반환 분기를 먼저 나열")을 진작 적용했으면 한 번에 찾았을
자리다** — 첫 번째(qc-dot)를 실사용 버그로 발견한 시점에 "도구 무관 조기반환 분기가
또 있는가"로 `mousePressEvent`/`mouseDoubleClickEvent` 전체를 훑었어야 했는데, 매번
사용자가 새 증상을 보고한 뒤에야 그 지점만 개별로 찾아 고쳤다. 수정 자체는 항상 같은
모양(`... and self._owner.current_tool != "trim"` 가드 추가)이었다.

**다음에 새 도구/모드를 추가할 때 체크리스트**: `current_tool`을 확인하지 않는
early-return 분기를 `mousePressEvent`·`mouseMoveEvent`·`mouseDoubleClickEvent`
전체에서 먼저 grep(`grab`·`hit is not None`·`return` 패턴)해 새 도구가 통과해야
하는 우선순위표를 만들고 나서 구현을 시작할 것.
