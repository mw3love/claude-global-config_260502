---
repo: PasteFlow
remote: https://github.com/mw3love/Paste_flow.git
stack: [Python, Win32, PyQt6]
tags: [SendInput, 클립보드주입, suppress, WH_KEYBOARD_LL, RegisterHotKey, AttachThreadInput, WM_PASTE, 앱별분기]
used: []
---

# Win32 입력 주입 3종 함정 (붙여넣기·단축키·외부앱)

## 함정 1 — 순차 붙여넣기: suppress를 하면 안 된다

클립보드를 교체하고 `Ctrl+V` 를 `SendInput` 으로 주입하는 방식. 여기서 핵심은 **원래 키 이벤트를 suppress하지 않는 것.** suppress하면 붙여넣기가 오히려 깨진다. (직관과 반대라 헤매기 쉬운 지점.)

## 함정 2 — 전역 단축키는 RegisterHotKey를 우회해야 한다

`RegisterHotKey` 대신 **`WH_KEYBOARD_LL` 저수준 키보드 훅**으로 전역 단축키를 잡는다.

- `RegisterHotKey`의 제약(수정자 조합 한계, 선점 충돌)을 우회
- 훅에서 직접 **suppress** 제어
- **입력기(IME) 전환 마스킹** 처리 필요

## 함정 3 — 외부 앱 붙여넣기는 앱마다 방식이 다르다

드래그해서 외부 앱에 붙여넣을 때, **하나의 방법으로 안 된다.** 앱 클래스별로 분기해야 한다.

- 일부 앱: `WM_PASTE` 메시지
- 일부 앱: `AttachThreadInput` + `SendInput`
- 나머지: 파일로 저장 후 전달

어느 앱이 어느 방식인지는 시행착오로 알아낸 것이라 코드에 분기가 남아 있다.
