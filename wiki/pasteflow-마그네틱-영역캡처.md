---
repo: PasteFlow
remote: https://github.com/mw3love/Paste_flow.git
stack: [PyQt6, Windows, Win32]
tags: [영역캡처, 오버레이, 입력소유, MSAA, accHitTest, DWM, 멀티모니터, DPI, 검은깜빡임]
used: []
---

# 마그네틱 영역 캡처 (Snipaste식 요소 스냅)

커서 아래 UI 요소의 경계에 자동으로 달라붙는 화면 캡처 오버레이. 함정이 네 겹으로 쌓여 있어 하나씩 뚫어야 한다.

## 함정 1 — 클릭통과 오버레이는 커서를 뺏긴다

오버레이를 클릭통과(click-through)로 만들면, 커서 밑의 앱이 `WM_SETCURSOR`로 자기 커스텀 커서를 세운다. 그 순간 십자 커서가 벗겨진다.

**해법:** 오버레이가 **입력을 소유**하게 하고 `setCursor`로 직접 세운다. 그래야 어떤 앱 위에서든 십자가 유지된다.

## 함정 2 — 점 기반 hit-test는 자기 자신을 짚는다

입력을 소유하면 이번엔 요소 hit-test가 오버레이 자신을 짚는다.

**해법:** **창 스코프**로 전환한다.

1. 시작 시점에 최상위 창 Z-order를 얼린다 — `GetTopWindow` + `GW_HWNDNEXT`
2. 그 `hwnd`에 `AccessibleObjectFromWindow`로 MSAA 객체를 얻고
3. `accHitTest`를 반복 하강시켜 요소를 스냅한다
4. 못 짚으면 창 전체로 폴백

MSAA가 UIA보다 개별 요소 정확도가 높다 (크롬 북마크 기준. Snipaste도 OLEACC를 쓴다).

## 함정 3 — 창 사각형에 `GetWindowRect`를 쓰면 검은 테두리가 생긴다

크롬 웹 본문은 MSAA가 `None`이라 창 폴백을 타는데, `GetWindowRect`는 **DWM의 비가시 리사이즈 테두리(좌·우·하 8px)** 를 포함한다. 그래서:

- 창이 모니터 경계를 초과하고 → 코랄(선택 영역)이 옆 모니터로 넘침
- 모니터 밖 빈 공간이 crop되어 검은 캔버스로 잡힘 → **검은 테두리**

**해법:** `DwmGetWindowAttribute(DWMWA_EXTENDED_FRAME_BOUNDS = 9)` 로 **보이는 경계**를 쓴다. DWM 호출 실패 시에만 `GetWindowRect` 폴백.

## 함정 4 — 프레임리스 반투명 창의 첫 프레임이 검게 깜빡인다

**해법:** `WA_OpaquePaintEvent` + `show()` 직후 `repaint()` 로 첫 페인트를 동기 처리.

## 그 외

- 크로스 DPI 멀티모니터 합성 처리 필요.
