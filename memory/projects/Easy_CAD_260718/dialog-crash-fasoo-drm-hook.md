---
name: dialog-crash-fasoo-drm-hook
description: "Mermaid/SVG 생성창을 반복 열고 X로 닫으면 앱이 죽던 크래시 — 진짜 원인은 죽은 QThread 래퍼 참조(RuntimeError가 QDialog.done() 밖으로 나가 PyQt6가 abort). Fasoo DRM·한글IME 가설은 둘 다 반증됨. 진단 핵심: fastfail 코드 7 = abort = 파이썬 예외, 커스텀 sys.excepthook으로 traceback 포착"
metadata:
  type: project
  originSessionId: (2026-08-26 세션)
  modified: 2026-08-26T13:31:30.128Z
---

**증상**: Mermaid 가져오기 / AI SVG 에셋 생성 창을 열었다 우상단 X로 닫기를 2~6번
반복하면 앱 프로세스 전체가 조용히 죽는다(타이핑 없이 열자마자 닫기만 해도 재현).

**진짜 원인(확정, 2026-08-26)**: `host_dialogs.py`의 `_detach_worker()`는 다이얼로그가
닫힐 때 아직 도는 워커(QThread)를 고아로 떼어낸 뒤 `finished`에서 `deleteLater()`로
C++ 객체를 지운다. 그런데 다이얼로그는 2026-08-25부터 **인스턴스를 재사용**(닫아도 안
죽고 숨기만 함)하는데 `self._model_list_worker` / `self._workers` 참조를 안 비웠다 →
다음 번 닫기에서 이미 파괴된 C++ 객체에 `worker.isRunning()`을 불러
`RuntimeError: wrapped C/C++ object of type _ModelListWorker has been deleted` 발생 →
이 예외가 **Qt 가상함수 재구현인 `QDialog.done()` 밖으로 탈출** → PyQt6가 `qFatal()`
→ `abort()` → 프로세스 즉사. 워커가 닫는 시점에 "돌고 있었는지"(모델목록 네트워크
조회 속도)에 따라 몇 번째에 죽는지가 달라져 재현 횟수가 들쭉날쭉했다.
**수정**: 각 `done()`에서 detach 직후 참조를 `None`/`[]`로 끊고, 공용 헬퍼
`_detach_worker`도 죽은 래퍼(`RuntimeError`)를 만나면 조용히 반환하게 함.
회귀 테스트 2종(`sip.delete()`로 죽은 래퍼를 결정론적으로 재현) 추가 — 수정 전 코드에서
프로덕션과 똑같은 RuntimeError로 실패함을 확인했다.

**반증된 가설 2개(같은 세션에서 순차적으로 틀림 — 교훈용으로 남김)**:
1. **Fasoo DRM(f_sps.dll) 후킹 탓** — 크래시 스택에 이 DLL이 자주 보여 지목했으나,
   사용자가 삭제+재부팅한 뒤에도 동일 재현되고 새 덤프엔 그 DLL이 아예 없었다. 이 PC의
   거의 모든 프로세스(Chrome·PowerShell 등 30개+)에 주입되는 흔한 DLL이라 마침 같이
   잡혔을 뿐인 방관자였다.
2. **한글 IME(imkrtip.dll/msctf.dll) 탓** — Fasoo 배제 후 모든 덤프의 유일한 공통
   모듈이라 지목하고 `clearFocus()` 완화책을 넣었다. 20회 무크래시로 "개선됐다"고
   봤지만 사용자 재현에서 2회 만에 재발 → 이것도 방관자(GUI 앱 메시지 루프엔 항상
   IME 모듈이 얹힌다). 진짜 원인 확정 후 `clearFocus()`는 **제거**했다(틀린 근거로 남은
   코드는 미래를 오도한다).

⚠ **교훈: "크래시 스택에 낯선 DLL이 보인다"는 원인 지목의 근거가 못 된다.** GUI 앱의
메시지 루프 스택엔 항상 후킹 DLL·IME·테마 DLL이 얹혀 있다. 반드시 **그 후보를 실제로
제거/무력화한 뒤에도 재현되는지**로 반증을 시도할 것.

**결정적 진단 기법(이걸 처음부터 했으면 훨씬 빨랐다)**:
1. `%LOCALAPPDATA%\CrashDumps\*.dmp`를 Python `minidump` 패키지로 파싱해
   **`ExceptionRecord.ExceptionInformation`(fastfail 코드)**까지 볼 것.
   `0xC0000409` + `ExceptionInformation[0] == 7` = `FAST_FAIL_FATAL_APP_EXIT` =
   **누군가 `abort()`를 명시적으로 불렀다** = 메모리 손상이 아니다. PyQt6에서 이건
   대부분 **Qt 가상함수/슬롯 안에서 처리 안 된 파이썬 예외**다. (크래시 주소가 매번
   똑같이 고정인 것도 "우연한 손상"이 아니라 "고정된 abort 호출지점"의 신호.)
2. `pythonw.exe`(콘솔 없음)에서는 그 traceback이 그냥 사라진다. **커스텀 진단 런처**로
   ⓐ `sys.excepthook` ⓑ stderr 미러링 ⓒ `qInstallMessageHandler` ⓓ `faulthandler`를
   전부 파일로 **즉시 flush** 하면 크래시 직전 traceback이 그대로 잡힌다.
   ⚠ 부수효과: **커스텀 `sys.excepthook`을 설치하면 PyQt6가 abort를 안 한다** — 그래서
   진단 런처로는 크래시가 재현 안 되는 것처럼 보인다(이것 자체가 "파이썬 예외가
   원인"이라는 강력한 증거다). 최종 검증은 반드시 평범한 `python run.py`로 할 것.
   이 세션에서 쓴 런처: 스크래치패드 `diag_launcher.py`(세션 종료 시 사라짐 — 필요하면
   `tools/`로 승격 검토).
3. 재현 자동화는 [[qt-dialog-crash-debug-real-click]]의 진짜 마우스클릭 기법
   (PowerShell + `AttachThreadInput`으로 `SetForegroundWindow` 강제)을 반복 루프로 감싸
   "몇 번째에 죽는지"를 수치로 비교. 수정 전 4회 → 수정 후 24회+ 무크래시.
   ⚠ PowerShell 도구 호출은 매번 새 세션이라 `Add-Type`한 타입이 안 남는다 — 반복
   측정 스크립트는 한 호출 안에 자족적으로 담을 것.
