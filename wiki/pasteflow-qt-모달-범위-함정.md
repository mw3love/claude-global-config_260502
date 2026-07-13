---
repo: PasteFlow
remote: https://github.com/mw3love/Paste_flow.git
stack: [PyQt6]
tags: [모달, QDialog, exec, show, finished, NonModal, ApplicationModal, WindowModal, 재진입가드, 비모달, 입력차단]
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

---

# 후속 함정 — `setWindowModality(NonModal)` + `exec()` = 여전히 ApplicationModal (2026-07-13)

## 증상

위 해법(창 모달)을 쓰니 이번엔 **부모(패널) 자체가 잠겼다** — AI 질문창이 떠 있으면 패널 버튼이 안 눌린다. 그래서 "아예 비모달로 만들자"며 두 가지를 했는데 **증상이 그대로였다**:

1. `setWindowModality(Qt.WindowModality.NonModal)` 추가
2. `parent=None` 으로 바꿔 소유 창(Z-order) 관계까지 끊음

패널 클릭·영역 캡처(Alt+F2)·기록창이 계속 막혔고, 원인을 "Windows Z-order 규칙"으로 오진해 같은 자리를 두 번 더 팠다(사용자가 같은 증상을 재보고).

## 원인

**`exec()` 는 모달성 설정을 이긴다.** `QDialog::exec()` 는 창을 모달로 표시하는데, 이때 모달성이 `NonModal` 이고 **부모도 없으면 Qt가 `ApplicationModal` 로 승격**시킨다. 즉 `parent=None` 으로 바꾼 것이 오히려 승격을 확정지었다(부모가 있었으면 `WindowModal` 이 됐을 자리).

## 해법

`exec()` 를 버리고 **`show()` + `finished` 콜백**으로 결과를 받는다. 모달성 지정만으로는 절대 안 되고, **띄우는 방식 자체를 바꿔야** 한다.

```python
dialog = MyDialog(...)            # setWindowModality(NonModal)
self._dlg = dialog                # 강한 참조 유지 (GC 방지)

def _finished(code):
    self._dlg = None
    if code == QDialog.DialogCode.Accepted:
        ...                       # exec() 뒤에 있던 코드가 여기로
    dialog.deleteLater()

dialog.finished.connect(_finished)
dialog.show()
```

## 실측 (PyQt6)

| 띄우는 방법 | `QWindow.modality` |
|---|---|
| `exec()` (설정 없음) | `ApplicationModal` |
| `setWindowModality(NonModal)` + `exec()` | **`ApplicationModal`** ← 설정이 무시됨 |
| `setWindowModality(NonModal)` + `show()` | `NonModal` |

## 대가

- 호출부가 **동기 → 비동기**가 된다(`if dialog.exec() == Accepted:` 뒤의 코드를 전부 콜백으로 옮겨야 함).
- 비모달이라 같은 창을 **또 열 수 있다** → 위 «재진입 가드»가 여기서도 필수.
- 중첩 `QEventLoop` 로 동기 형태를 지키는 우회도 되지만, 이제 살아난 패널·단축키가 그 루프 아래에서 재진입하므로 기각.
