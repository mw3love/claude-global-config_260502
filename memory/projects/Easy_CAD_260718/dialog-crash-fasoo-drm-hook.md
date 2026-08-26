---
name: dialog-crash-fasoo-drm-hook
description: "Mermaid/SVG 창을 X버튼으로 열고닫기를 반복하면 앱 전체가 죽는 문제 — 원인은 EasyCAD 코드가 아니라 이 PC에 깔린 Fasoo DRM(f_sps.dll, 'Secure Print Support Module')이 Qt 창 관리에 개입하다 Qt6Core.dll 안에서 충돌하는 것(2026-08-26 minidump 분석으로 확정)"
metadata:
  type: project
  originSessionId: (2026-08-26 세션)
  modified: 2026-08-26T12:28:48.244Z
---

**증상**: `python run.py`(또는 `run.pyw`)로 앱을 켜고 Mermaid 가져오기/AI SVG 생성 창을
열었다 우상단 X로 닫기를 몇 번(사용자 체감 약 3회) 반복하면 앱 프로세스 전체가 조용히
죽는다(Python 예외·콘솔 출력 없음).

**원인(확정)**: EasyCAD 코드 버그가 아니다. Windows Event Viewer(`Get-WinEvent
-FilterHashtable @{LogName='Application'; ProviderName='Application Error'}`)와
`%LOCALAPPDATA%\CrashDumps\pythonw.exe.*.dmp`(Python `minidump` 패키지로 파싱,
`pip show minidump`로 이미 설치돼 있음)를 분석한 결과:
- 모든 크래시가 **정확히 같은 주소**(`Qt6Core.dll+0x1bbd8`, exception code
  `0xc0000409` = STATUS_STACK_BUFFER_OVERRUN/fail-fast)에서 발생 — 우연이 아니라
  결정론적인 진입점.
- 크래시 스레드(항상 메인 UI 스레드)의 스택을 덤프에서 직접 읽어보면 `user32.dll`
  (`SendMessage`/`DispatchMessage`류) ↔ **`C:\Program Files\Fasoo DRM\f_sps.dll`**
  (파일 설명: "Fasoo Secure Print Support Module", Fasoo Co., Ltd.) ↔ `Qt6Widgets`/
  `Qt6Gui`/`Qt6Core`가 반복적으로 서로를 호출하는 전형적인 **윈도우 프로시저 후킹
  체인**(hook → CallWindowProc → 원래 wndproc → hook…) 패턴이 나온다.
- 같은 offset의 크래시가 **2026-08-22부터** Event Log에 남아있다 — 이 세션(08-26)
  이전, 심지어 08-25 "Mermaid/SVG 창 인스턴스 재사용" 변경 이전부터 있던 것이므로
  최근 코드 변경과 무관함을 교차 확인.

**결론**: 이 PC에 설치된 Fasoo DRM(인쇄 보안/화면보호 에이전트로 추정, 기업/공공기관
환경에 흔함)이 프로세스에 전역 후킹을 걸어 모든 최상위 창(HWND) 생성·소멸을 가로채는데,
Qt6(PyQt6)가 다이얼로그를 반복적으로 열고 닫을 때 이 후킹과 상호작용하다 Qt 내부
상태가 깨져 크래시하는 것 — **애플리케이션 코드로 근본 수정 불가능한 환경 요인**이다.

**대응(코드로 못 고침, 사용자가 취해야 할 조치)**:
1. 사내 IT/보안팀에 "Fasoo f_sps.dll이 Python/PyQt6 프로세스(`python.exe`/
   `pythonw.exe`, 또는 EasyCAD 실행파일)에서 반복 창 열고닫기 시 크래시를 일으킨다"고
   보고 — Fasoo 에이전트 최신 버전에 이미 수정됐을 가능성.
2. 가능하면 EasyCAD 실행파일(빌드된 `.exe` 또는 `python.exe`/`pythonw.exe` 경로)을
   Fasoo 후킹 대상에서 제외(exclusion/allowlist) 요청 — 많은 DRM 에이전트가 이 옵션을
   제공.
3. 임시 완화책으로 사용자에게 "같은 창을 빠르게 여러 번 열고 닫지 말고, 필요한 작업을
   한 번에 끝내고 닫으라"고 안내할 수 있으나 근본 해결은 아님.

**진단에 쓴 도구/기법(재사용 가능)**: `Get-WinEvent -FilterHashtable
@{LogName='Application'; ProviderName='Application Error'}`로 크래시 이벤트(ID 1000)
확인 → `%LOCALAPPDATA%\CrashDumps\`에 자동 생성된 `.dmp` 파일을 Python
`minidump` 패키지(`MinidumpFile.parse(path)`)로 파싱 → `mf.exception.exception_records[0]`
에서 크래시 스레드ID·주소, `mf.modules.modules`에서 그 주소가 속한 모듈, 크래시
스레드의 `ContextObject.Rsp`부터 스택 메모리를 `mf.get_reader().read(rsp, size)`로
읽어 8바이트씩 스캔하며 로드된 모듈 주소 범위와 매칭 — 심볼(PDB) 없이도 "어떤 DLL들이
스택에 관여했는지"는 충분히 알아낼 수 있다. [[qt-dialog-crash-debug-real-click]](이전
세션이 진짜 마우스클릭 재현법을 남긴 것)과 짝을 이루는 사후 분석 기법 — 재현까지는
그 메모리대로, 원인 규명은 이 방법으로.

**주의**: 이전 메모리 [[qt-dialog-crash-debug-real-click]]는 2026-08-22의 "X버튼
닫기 크래시"를 QThread 라이프사이클 버그로 진단·수정했다(2026-08-23 `_detach_worker`
도입). 이번에 minidump로 새로 발견한 Fasoo 크래시는 **같은 날짜대의 로그에 섞여
있던 별개의 원인**이다 — "X버튼 닫기 크래시"라는 증상만으로 QThread 버그로 단정하지
말고, 이 문서의 진단 절차로 먼저 실제 크래시 덤프를 확인할 것.
