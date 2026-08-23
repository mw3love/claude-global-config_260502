---
repo: Easy_CAD_260718
remote: https://github.com/mw3love/Easy_CAD_260718.git
stack: [PyQt6, QGraphicsView, Windows]
tags: [드래그앤드롭, dragEnterEvent, dragMoveEvent, dropEvent, QGraphicsView, viewport, setAcceptDrops, eventFilter, 파일드롭]
used: []
---

# QGraphicsView 뷰포트가 부모 QMainWindow의 드래그 이벤트를 가로채 dropEvent가 안 불림

## 함정

캔버스(QMainWindow, `CanvasWindow`)에 `.ecad`/`.dxf`/`.svg` 등 파일 드래그앤드롭을 추가하려고
`dragEnterEvent`/`dropEvent`(host_fileio.py)에 확장자 라우팅을 넓혔다. pytest로 이 핸들러들을
직접 호출하는 단위 테스트는 전부 통과했는데, 실제 창(`python run.py`)에서 파일을 캔버스
중앙으로 끌면 **항상 금지 커서만 뜨고 아무 일도 안 일어났다.**

1차 진단이 완전히 틀렸다: "코드 수정 전에 이미 떠 있던 옛 프로세스라 반영이 안 됐다"고
판단했는데, 사용자가 완전히 새로 켜서 재현해도 동일했다. 프로세스 시작시각 vs 파일
저장시각을 실측 비교해 이 진단이 틀렸음을 스스로 확인한 뒤 재조사.

진짜 원인은 `QWidget.setAcceptDrops(True)`가 걸린 **자식 위젯**은 그 위젯이 커서 아래
있는 동안 드래그/드롭 이벤트를 전부 자기가 받는다는 것 — 부모가 같은 플래그를 가지고
있어도 자식이 있으면 그쪽으로 안 넘어간다. 이 앱은 캔버스 뷰(`QGraphicsView`)의
`viewport().setAcceptDrops(True)`가 이미 걸려 있었다(2026-08-19, 팔레트 도형 드래그
지원을 위해 추가된 것 — M3 #17). 그래서 파일 URL 드래그도 `CanvasWindow`가 아니라
뷰포트로 직접 갔고, `QGraphicsView` 자신의 기본 드래그 처리는 "그 위치에 드롭을 받는
씬 아이템이 있는지"로 매번 재판정한다 — 우리 도형·화살표는 드롭 수용 아이템이 아니라서
거부됐다.

**핵심 실측 포인트: `dragEnterEvent`와 `dragMoveEvent`가 서로 다른 결과를 낸다.**
`app.sendEvent(viewport, QDragEnterEvent(...))` → `isAccepted()` True (낙관적으로
일단 받아줌). 이어서 `app.sendEvent(viewport, QDragMoveEvent(...))` → `isAccepted()`
**False**(실제 위치별 재판정에서 거부). **커서 아이콘(허용/금지)은 dragMove 기준이라**,
dragEnter만 확인하면 "정상인데 왜 커서는 금지로 뜨지" 같은 착시가 생긴다. pytest로
핸들러를 직접 호출하는 테스트는 이 위젯 계층 라우팅 자체를 우회하므로 이 버그를 절대
못 잡는다 — Qt의 실제 이벤트 디스패치를 재현하려면 `QApplication.sendEvent(대상위젯, ev)`
로 진짜 대상(뷰포트)에 보내야 드러난다.

## 해법

부모(`CanvasWindow`)의 `dragEnterEvent`/`dropEvent`를 아무리 넓혀도 소용없다 — 뷰포트가
이미 가로채므로 호출될 기회가 없다. 팔레트 도형 드래그가 이미 이 문제를 겪고 풀어둔
패턴(뷰포트에 건 `eventFilter`가 DragEnter/DragMove/Drop을 직접 가로챔)을 URL 드래그에도
그대로 확장해야 한다:

```python
def eventFilter(self, obj, event):
    if obj is self._view.viewport():
        et = event.type()
        if et in (QEvent.Type.DragEnter, QEvent.Type.DragMove):
            md = event.mimeData()
            if md.hasFormat(_PALETTE_MIME):
                event.acceptProposedAction(); return True
            if md.hasUrls() and any(<확장자 체크>):
                event.acceptProposedAction(); return True
        elif et == QEvent.Type.Drop:
            md = event.mimeData()
            if md.hasUrls():
                scene_pos = self._view.mapToScene(event.position().toPoint())
                if self._handle_url_drop(md, scene_pos):
                    event.acceptProposedAction()
                return True
    return super().eventFilter(obj, event)
```

처리 본문(`_handle_url_drop`)은 `dropEvent`(뷰포트 밖에 떨어졌을 때만 쓰는 폴백)와
`eventFilter`(뷰포트 레벨, 실사용 경로)가 공유하도록 추출하면 중복이 없다.

## 검증법 (진단이 맞는지 확인하는 법)

pytest로 핸들러를 직접 호출하지 말고, 실제(오프스크린 아닌) 창에 실제 이벤트를
`sendEvent`로 보내라:

```python
app = QApplication.instance() or QApplication([])
w = CanvasWindow(); w.show(); app.processEvents()
vp = w._view.viewport()
md = QMimeData(); md.setUrls([QUrl.fromLocalFile(r"C:\fake\test.ecad")])
pos = QPointF(vp.rect().center()).toPoint()

ev1 = QDragEnterEvent(pos, Qt.DropAction.CopyAction, md, Qt.MouseButton.NoButton, Qt.KeyboardModifier.NoModifier)
app.sendEvent(vp, ev1); print("dragEnter:", ev1.isAccepted())

ev2 = QDragMoveEvent(pos, Qt.DropAction.CopyAction, md, Qt.MouseButton.NoButton, Qt.KeyboardModifier.NoModifier)
app.sendEvent(vp, ev2); print("dragMove:", ev2.isAccepted())   # 여기서 False면 이 함정
```

`QMessageBox.warning`/`information`을 미리 no-op으로 스텁해두지 않으면, 실패 경로에서
뜨는 경고창이 `.exec()`로 진짜 이벤트루프를 막아 스크립트가 무한 대기한다(별도 함정,
`QMessageBox.warning = staticmethod(lambda *a, **k: QMessageBox.StandardButton.Ok)`).

## 대가

없음 — 뷰포트 `eventFilter`가 이미 팔레트 mime을 처리하던 자리에 조건 하나만 더 태운
것이라 새 위험이 생기지 않았다. 다만 `dropEvent`(창 레벨)는 이제 "뷰포트 밖에 떨어졌을
때만" 실행되는 좁은 폴백이 됐다는 걸 다음에 이 코드를 만지는 사람이 기억해야 한다 —
캔버스 중앙 드롭을 디버깅할 땐 `dropEvent`가 아니라 `eventFilter`부터 봐야 한다.
