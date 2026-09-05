---
name: feedback_console_cp949_pythonioencoding
description: 이 PC 콘솔은 cp949 — 한글/유니코드 출력하는 Python 실행 시 PYTHONIOENCODING=utf-8 필요
metadata: 
  node_type: memory
  type: feedback
  originSessionId: b75f0611-379a-4c7e-9f90-4bcad1e7599b
---

이 프로젝트 실행 환경의 Windows 콘솔 기본 인코딩은 **cp949**다. 한글이나 유니코드 기호(em dash `—`, `±`, `✓` 등)를 `print`하는 Python 스크립트/테스트를 그냥 실행하면 `UnicodeEncodeError: 'cp949' codec can't encode character`로 **스크립트 본 로직과 무관하게 출력 단계에서 죽는다.**

**Why:** 이번 세션에서 `tests/test_chaos.py`가 시작 배너의 `—` 때문에 1차 실패했다 — 테스트 로직은 멀쩡했고 순전히 콘솔 인코딩 문제였다. 이걸 모르면 멀쩡한 코드를 버그로 오진할 수 있다.

**How to apply:** 한글/유니코드를 출력하는 Python 명령은 `PYTHONIOENCODING=utf-8`을 앞에 붙여 실행한다 (Bash 도구: `PYTHONIOENCODING=utf-8 python ...`). pytest도 동일. 출력 단계 크래시를 코드 결함으로 오해하지 말 것.
