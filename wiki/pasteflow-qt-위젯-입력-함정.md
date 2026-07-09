---
repo: PasteFlow
remote: https://github.com/mw3love/Paste_flow.git
stack: [PyQt6]
tags: [QComboBox, currentText, 배지, DecorationRole, 그룹헤더, 유령포커스, setEnabled, NoFocus, 오진]
used: []
---

# Qt 입력 위젯이 조용히 값·포커스를 바꾸는 함정 두 개

## 함정 1 — editable QComboBox 항목에 텍스트 배지를 붙이면 저장값이 오염된다

콤보박스 항목에 `"model ⭐"` 처럼 텍스트 접미사로 배지를 달았더니 API 호출이 깨졌다.

**원인:** editable QComboBox는 `currentText()` 가 **곧 저장값**이다. `"model ⭐"` 가 API 모델명으로 그대로 저장돼 호출이 404난다.

**해법:**
- 배지는 텍스트가 아니라 `QIcon` **`DecorationRole`** 로 단다.
- 그룹 헤더는 **선택 불가**로 — `model().item(i).setEnabled(False)`.
- **함정 속 함정:** `clear()` 직후 Qt가 0번(헤더)을 자동 선택한다. → `_select_first_enabled()` 로 첫 실제 항목을 복구해야 한다.

## 함정 2 — 버튼 비활성화가 콤보박스를 "깜빡이는 버그"처럼 보이게 한다

조회 중에 텍스트가 파랗게 반전됐다 사라지는 현상. `clear()` 나 `repaint()` 탓으로 **오진하기 쉽다.**

**진짜 원인:** `QPushButton.setEnabled(False)` 를 하면 Qt가 포커스를 **다음 위젯으로 넘긴다.** 그 다음 위젯이 editable QComboBox면, 포커스를 받는 순간 `lineEdit` 을 **전체 선택**한다. 그게 파란 반전으로 보인다.

**해법:** 그 버튼에 `setFocusPolicy(Qt.FocusPolicy.NoFocus)`. 비활성화돼도 포커스를 넘기지 않게 한다.
