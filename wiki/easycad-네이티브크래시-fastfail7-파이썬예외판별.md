---
repo: Easy CAD
remote: https://github.com/mw3love/Easy_CAD_260718.git
stack: [PyQt6, Windows, Python3.14]
tags: [크래시, minidump, fastfail, 0xC0000409, abort, qFatal, excepthook, QThread, deleteLater, sip, DRM후킹, IME, CrashDumps]
used: []
---

# PyQt 앱이 "몇 번 반복하면 조용히 죽을" 때 — 진짜 원인 판별법

증상: 다이얼로그를 열었다 X로 닫기를 2~6번 반복하면 프로세스 전체가 예외 메시지 하나
없이 사라짐. `pythonw.exe`라 콘솔도 없음.

## 함정

**1. 크래시 스택에 보이는 낯선 DLL을 원인으로 지목했다 — 두 번 연속 틀렸다.**

minidump 스택을 훑어 자주 보이는 모듈을 원인으로 찍었다:
- 1차: `C:\Program Files\Fasoo DRM\f_sps.dll`(사내 DRM 인쇄보안). → 사용자가 삭제하고
  **재부팅한 뒤에도 동일 재현**되고 새 덤프엔 그 DLL이 아예 없어 반증. 이 PC의 거의
  모든 프로세스(Chrome·PowerShell 등 30개+)에 주입되는 흔한 DLL이라 마침 같이 잡혔을 뿐.
- 2차: 한글 IME(`imkrtip.dll`/`msctf.dll`). Fasoo 배제 후 **모든** 덤프의 유일한 공통
  모듈이라 지목하고 `done()`에 `clearFocus()` 완화책을 넣었다. 자동화로 20회 무크래시가
  나와 "개선됐다"고 봤으나 사용자 재현에서 2회 만에 재발. 이것도 방관자였다.

⚠ **GUI 앱의 메시지 루프 스택엔 항상 후킹 DLL·IME·테마 DLL이 얹혀 있다.** "스택에
보인다"는 원인 지목의 근거가 못 된다. 반드시 **그 후보를 실제로 제거/무력화한 뒤에도
재현되는지**로 반증을 시도할 것.

**2. 완화책의 "N회 무크래시"를 해결로 오독했다.** 원인을 모른 채 횟수만 늘어난 것은
타이밍이 살짝 바뀐 것일 수 있다. 원인을 특정하기 전엔 "개선"으로만 보고할 것.

**3. 진단 런처를 붙이면 크래시가 재현되지 않아 혼란.** (아래 해법 참조 — 이것 자체가
결정적 단서였는데 처음엔 "환경 탓"으로 흘려보낼 뻔했다.)

## 해법

**① minidump의 fastfail 코드를 먼저 볼 것 — 여기서 절반이 끝난다.**

`%LOCALAPPDATA%\CrashDumps\*.dmp`(Windows가 자동 생성)를 Python `minidump` 패키지로 파싱:

```python
from minidump.minidumpfile import MinidumpFile
mf = MinidumpFile.parse(path)
er = mf.exception.exception_records[0].ExceptionRecord
print(er.ExceptionCode, hex(er.ExceptionAddress), er.ExceptionInformation)
```

`0xC0000409`(STATUS_STACK_BUFFER_OVERRUN) + **`ExceptionInformation[0] == 7`**
(`FAST_FAIL_FATAL_APP_EXIT`) = **누군가 `abort()`를 명시적으로 불렀다** = 메모리 손상이
아니다. PyQt에서 이건 대부분 **Qt 가상함수/슬롯 안에서 처리 안 된 파이썬 예외**다
(PyQt6는 그때 traceback을 stderr에 찍고 `qFatal()`→`abort()`).
크래시 주소가 매번 **똑같이 고정**인 것도 "우연한 손상"이 아니라 "고정된 abort
호출지점"의 신호다(손상이면 주소가 흔들린다).

fastfail 코드 참고: 0=GS위반, 2=스택쿠키, 3=리스트손상, 5=INVALID_ARG, **7=FATAL_APP_EXIT(abort)**.

**② 진단 런처로 traceback을 붙잡는다** — `pythonw.exe`엔 콘솔이 없고, 리다이렉트해도
stderr가 블록 버퍼링되면 `abort()` 시 유실된다. ⓐ `sys.excepthook` ⓑ stderr 미러링
ⓒ `qInstallMessageHandler` ⓓ `faulthandler`를 전부 **파일로 즉시 flush + `os.fsync`**
하는 런처를 만들어 그걸로 앱을 띄운다.

⚠ **부수효과이자 결정적 증거: 커스텀 `sys.excepthook`을 설치하면 PyQt6가 abort를 안 한다.**
그래서 진단 런처로는 크래시가 재현되지 않는 것처럼 보인다 — 이게 곧 "파이썬 예외가
원인"이라는 강력한 증거다. **최종 검증은 반드시 평범한 실행(`python run.py`)으로** 할 것.

**③ 이 사례의 실제 범인 — 죽은 QThread 래퍼 참조.**

```
RuntimeError: wrapped C/C++ object of type _ModelListWorker has been deleted
  host_dialogs.py in done()  →  _detach_worker(self._model_list_worker)
                             →  worker.isRunning()
```

다이얼로그가 닫힐 때 아직 도는 워커를 고아로 떼어내고 `finished`에서 `deleteLater()`로
C++ 객체를 지우는데, **다이얼로그 인스턴스를 재사용**하면서 파이썬 쪽 참조를 안 비웠다.
다음 닫기에서 죽은 래퍼에 `isRunning()`을 불러 `RuntimeError` → 그게 가상함수
`QDialog.done()` 밖으로 탈출 → abort. 닫는 시점에 워커가 돌고 있었는지(네트워크 속도)에
따라 몇 번째에 죽는지가 갈려 **재현 횟수가 들쭉날쭉했던 것**도 이걸로 설명된다.

수정: `done()`에서 detach 직후 참조를 `None`/`[]`로 끊기 + 공용 detach 헬퍼가 죽은
래퍼(`RuntimeError`)를 만나면 조용히 반환.

**④ 회귀 테스트는 `sip.delete()`로 결정론적 재현.**
`from PyQt6 import sip; sip.delete(worker)` 가 `deleteLater()`가 이벤트 루프에서 실제로
하는 일(C++ 객체만 파괴, 파이썬 래퍼는 낡은 참조로 남김)과 같은 상태를 즉시 만든다.
수정 전 코드에서 프로덕션과 **똑같은 RuntimeError로 실패**함을 확인해 인과관계를 증명할 것.

**⑤ 재현 자동화는 횟수를 수치로.** 진짜 마우스클릭(PowerShell + `AttachThreadInput`으로
`SetForegroundWindow` 강제)을 반복 루프로 감싸 "몇 번째에 죽는지"를 수정 전/후 비교.
수정 전 4회 → 수정 후 24회+ 무크래시, 새 덤프 0건.
⚠ PowerShell 도구 호출은 매번 새 세션이라 `Add-Type`한 타입이 안 남는다 — 측정
스크립트는 **한 호출 안에 자족적으로** 담을 것.

## 대가

진단 런처는 `sys.excepthook`을 가로채므로 **그 상태로는 원래 크래시가 재현되지 않는다**.
"런처로 돌렸더니 안 죽네 = 고쳐졌네"로 착각하지 말 것. 런처는 원인 포착용이고,
검증은 평범한 실행으로 따로 해야 한다.
