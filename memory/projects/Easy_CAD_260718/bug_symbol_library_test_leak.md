---
name: bug-symbol-library-test-leak
description: 전체 pytest 스위트 실행이 symbol_library.json을 오염시키는 것으로 의심됐으나, 최종 검수 Phase 1(2026-08-25)에서 정식 스위트 2회 연속 무오염 재확인 — 실제 원인은 격리 안 된 수동/애드혹 스크립트로 재규명
metadata:
  node_type: memory
  type: project
  originSessionId: cbf55c56-1c43-4231-9aa8-74b8c4178464
  modified: 2026-08-25T12:36:04.276Z
---

**최초 관찰(같은 날 다른 세션)**: `python -m pytest tests/` 전체 실행 후 실제
`symbol_library/symbol_library.json`이 변조됨(심볼 `id`/`name` 값 변경). 원인 미조사, `git
checkout --`로 복구만 함.

**최종 검수 Phase 1 재조사(2026-08-25, 같은 날 후속) 결과 — 정식 스위트는 무죄로 확인**:
`python -m pytest tests/`(1001종)와 `python tests/test_easycad.py`(865종, 자체 러너) 둘 다
**연속 2회** 실행 후 `git diff symbol_library/symbol_library.json`이 매번 빈 결과 — 정식 테스트
스위트 자체는 `_isolated_symbol_library()` 격리를 빠짐없이 지키고 있는 것으로 재확인됨.

같은 세션에서 **실제 오염 재현에 성공한 경로**: Claude가 exit-127 크래시를 진단하려고 만든
임시 1회성 스크립트(`register_selection_as_symbol()`을 `_isolated_symbol_library()` 없이
직접 호출)가 실제 파일을 오염시켰다 — 최초 관찰도 이런 종류의 애드혹 스크립트(또는 유사하게
격리를 빠뜨린 일회성 실행)가 원인이었을 가능성이 높음. **`_shared.py`/`tests/`의 정식 테스트
파일이 아니라, symbol_library를 건드리는 임시 진단 스크립트를 짤 때 `_isolated_symbol_library()`
컨텍스트매니저를 빠뜨리는 습관이 실제 위험 지점.**

**How to apply**: 정식 `pytest tests/` 실행 후에는 더 이상 매번 `git status` 확인이 필수는
아님(2회 연속 무오염 확인됨) — 다만 습관적으로 확인하면 안전. **symbol_library를 건드리는
임시/1회성 진단 스크립트를 짤 때는 반드시 `with _isolated_symbol_library():`로 감쌀 것** —
이게 실제 위험 지점이다. 만약 정식 스위트 실행 후 다시 오염이 관찰되면(재발), 그때는 정말
격리 누락 테스트가 있다는 뜻이므로 `git bisect`류로 좁힐 것.
