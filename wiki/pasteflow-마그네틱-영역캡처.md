---
repo: PasteFlow
remote: https://github.com/mw3love/Paste_flow.git
stack: [PyQt6, Windows, Win32]
tags: [영역캡처, 오버레이, 입력소유, MSAA, accHitTest, DWM, 멀티모니터, DPI, 검은깜빡임,
       hover지연, 버벅임, ChildWindowFromPointEx, WindowFromPoint, oleacc, 크로스프로세스COM,
       DirectUIHWND, 탐색기, 입력투명자식]
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

## 함정 5 — 창 스코프 hit-test를 "최상위 창"부터 하강하면 탐색기에서 59ms가 걸린다

함정 2의 해법(창 스코프)을 그대로 쓰면 hover가 눈에 띄게 버벅인다. 마우스는 부드러운데 **하이라이트만 항목을 건너뛰며 뒤늦게 따라온다.**

원인: `accHitTest` 한 단계가 **크로스프로세스 COM 호출(~4ms)** 이다. 최상위 창(`CabinetWClass`) 루트부터 하강하면 리본·주소창·탭 컨테이너 같은 껍데기 계층을 전부 걸어 내려가느라 **탐색기에서 13단계 = 58.6ms**(실측). 60fps tick(16ms)의 3.7배라 매 프레임 메인 스레드가 멈춘다. 껍데기 11단계는 요소 정확도에 기여가 **0**이다(결과 rect 동일).

빠뜨린 것은 **`oleacc`가 `AccessibleObjectFromPoint` 안에서 먼저 하는 `WindowFromPoint`** — 즉 "점 아래 **최말단 자식 HWND**를 찾고 거기서부터 하강"이다. 점 기반 API가 3.5ms인데 창 스코프가 59ms였던 것이 이 누락의 증거였다.

**해법:** MSAA 루트를 잡기 전에 `ChildWindowFromPointEx` 재귀(비용 0.03ms)로 최말단 자식 HWND를 찾고 **그 hwnd를 루트로** 쓴다. 탐색기는 `DirectUIHWND`에서 **2단계 = 3~5ms**로 같은 rect가 나온다(격자 48점 48/48 동일, 47ms → 3.7ms). 자식이 요소를 안 주면 최상위 창 루트로 폴백하면 품질 후퇴가 없다.

⚠ **자기 오버레이를 짚을 위험은 없다** — 넘겨받은 대상 창의 *자식만* 뒤지므로, 별개 최상위 창인 오버레이는 후보에 없다(점 기반으로 되돌아가는 게 아님).

### 함정 5-b — `CWP_SKIPINVISIBLE`만 주면 크롬이 깨진다

`ChildWindowFromPointEx`는 **순수 기하** hit-test라 입력을 받지 않는 창도 짚는다. 크롬은 클라이언트 전체를 덮는 합성용 자식(`Chrome_RenderWidgetHostHWND`, `Intermediate D3D Window`)이 있는데, 이들을 루트로 잡으면 **그 창의 별개 접근성 트리**에서 엉뚱한 rect가 나온다(격자 48점 중 12점 불일치, 최악은 창 전체 1920×1040). 크롬은 원래 3.7ms로 빨랐으므로 **속도는 그대로인데 품질만 깎이는** 조용한 회귀다.

`WindowFromPoint`는 이런 창을 건너뛴다(`WM_NCHITTEST`/`HTTRANSPARENT` 인식). 기하 API로 그 동작을 재현하려면 플래그가 필요하다:

**해법:** `CWP_SKIPINVISIBLE | CWP_SKIPDISABLED | CWP_SKIPTRANSPARENT` (0x1|0x2|0x4). 그러면 크롬은 자식이 전부 걸러져 최상위 창이 루트로 남아 옛 동작과 **48/48 일치**하고, 탐색기는 여전히 `DirectUIHWND`를 찾아 3.3ms.

**대안 실측(둘 다 실패):** `RealChildWindowFromPoint` → 크롬 투명 자식을 그대로 짚어 36/48. 스로틀 강화·하강 깊이 제한 → 59ms라는 **호출 단가**를 못 건드려 무의미.

### 대가 / 곁가지

- hover hit-test에 걸어 뒀던 **30ms 스로틀**은 59ms 시절의 방어막이라 존재 이유가 사라진다(그대로 두면 하이라이트가 33Hz로 묶여 "건너뛰는 느낌"이 일부 남는다). 제거하되 **커서가 안 움직이면 hit-test를 스킵**해 유휴 비용을 0으로 둔다.
- **증상 재보고를 의심하기 전에 "앱을 재시작했는가"를 먼저 묻는다** — 실행 중 프로세스는 옛 모듈을 메모리에 물고 있어, 고친 뒤에도 사용자는 옛 동작을 본다(이번에 실제로 그래서 "아직 버벅인다"는 오보고가 한 번 있었다).

## 그 외

- 크로스 DPI 멀티모니터 합성 처리 필요.

## 캡처 → 핀(pin) 제자리 덮기

캡처한 이미지를 원래 위치에 겹쳐 띄우는 기능. 비자명한 지점 두 개:

- 캡처 시점의 **논리 사각형을 기억**하고, **클립보드가 그 이미지일 때만** 1:1로 정확히 덮는다(다른 걸 복사하면 무효화).
- **줌 = 사각형폭 / 픽맵폭** 으로 계산하면 DPI에 무관해진다. (픽셀폭이 아니라 논리폭 기준이라 배율이 자동으로 맞음.)
