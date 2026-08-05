---
name: new-pc-shortcut-rebind
description: 새 PC에 확장 로드 시 Ctrl+Shift+Y 단축키가 안 먹는 셋업 함정과 해결법
metadata: 
  node_type: memory
  type: project
  originSessionId: 1aee1571-8c7b-4383-b1a3-df1140c868fa
---

AI Dictionary 확장을 새 PC에 unpacked(`dist/`)로 로드하면 manifest의 `suggested_key`(Ctrl+Shift+Y)가 실제로 바인딩되지 않는 경우가 있다 — 눌러도 팝업이 안 뜸. 코드·manifest 문제 아님.

**Why:** Chrome은 `suggested_key`를 "제안"으로만 취급. 설치 시점에 미할당으로 남으면 단축키가 죽어 있음. `_execute_action` 팝업은 아이콘 클릭으론 정상이라, 클릭 vs 단축키로 원인을 가를 수 있다.

**How to apply:** 새 PC에선 `chrome://extensions/shortcuts`에서 "AI 사전 열기" 단축키를 한 번 재지정(다른 조합 → 다시 Ctrl+Shift+Y라도 OK)하면 등록됨. 진단 순서: ① 아이콘 직접 클릭 → 뜨면 단축키 전달 문제 ② 일반 http 페이지에서 테스트(chrome:// 페이지선 액션 팝업 단축키 안 먹음) ③ 다른 조합으로 바꿔 테스트 → 가로채기 여부 판별.
