---
repo: PasteFlow
remote: https://github.com/mw3love/Paste_flow.git
stack: [PyQt6]
tags: [모달, QDialog, exec, ApplicationModal, WindowModal, 재진입가드]
used: []
---

# Qt 모달 범위 함정 (ApplicationModal이 남의 창까지 잠근다)

## 증상

설정창을 열어 둔 상태에서 캡처 오버레이가 떠도 **클릭이 안 먹는다.**

## 원인

`QDialog.exec()` 의 기본 모달성은 **`ApplicationModal`** 이다. 이게 앱 전역으로 입력을 차단하므로, **부모가 없는 최상위 Tool 윈도우**(오버레이)의 입력까지 함께 막힌다.

## 해법

`exec()` 직전에 범위를 좁힌다.

```python
dlg.setWindowModality(Qt.WindowModality.WindowModal)
dlg.exec()
```

창 모달로 좁히면 **부모 창(패널)만 잠기고**, 부모 없는 오버레이는 입력을 통과시킨다.

## 대가 — 중첩 `exec()` 가 실제로 발생한다

창 모달은 트레이 메뉴나 에러 자동 오픈 경로를 막지 않는다. 그래서 `exec()` 안에서 또 `exec()` 가 열리는 상황이 **실제로 난다.** → **재진입 가드 필수.**

## 검증 방법

`SendInput` 으로 실제 클릭을 주입해 비교했다.

| 모달성 | `mousePressEvent` |
|---|---|
| `ApplicationModal` | 미수신 |
| `WindowModal` | 수신 |
