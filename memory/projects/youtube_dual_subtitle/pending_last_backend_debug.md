---
name: pending-last-backend-debug
description: "A21 푸쉬 직후 팝업 \"최근 번역: X · N분 전\" 라인이 안 뜨는 미해결 이슈. storage.local.lastBackend가 빈 채로 유지됨. 다음 세션에서 진단 테스트 3건으로 원인 좁히면 됨."
metadata: 
  node_type: memory
  type: project
  originSessionId: 239715da-8cf2-4c4c-84ae-5a37073195a6
---

A21 (cooldown + 팝업 마지막 백엔드 표시) 푸쉬 후 실제 검증에서 팝업의 "최근 번역" 라인이 안 뜨는 증상 관찰.

**현재까지 확인된 것**:
- 빌드 산출물에 `setLastBackend` 호출 (background bundle)·`getLastBackend` 호출 (popup bundle) 모두 정상 포함 확인
- 팝업 DevTools에서 `chrome.storage.local.get('lastBackend')` → `{}` (빈 객체)
- 자막은 정상 표시 중 (32줄 cue + Gemini 품질 한국어 번역) → translateBatch는 성공하는데 setLastBackend가 안 호출되거나 storage write가 안 됨

**Why:** A21이 단순 추가 기능(번역 자체엔 영향 없음)이지만 사용자가 SW devtools 없이 백엔드 동작 확인하려고 만든 핵심 UX 장치라서 동작 안 하면 의미 큼.

**How to apply:** 새 세션 시작 시 사용자에게 디버깅 이어가는지 확인. 이어가면 다음 3개 테스트를 팝업 DevTools(팝업 우클릭 → 검사)에서 실행 요청:

1. storage 자체 동작 확인: `chrome.storage.local.set({ydt_test: 'x'}).then(() => chrome.storage.local.get('ydt_test'))`
2. lastBackend 수동 write 후 팝업 재오픈: `chrome.storage.local.set({lastBackend: {used:'gemini', preferred:'gemini', at:Date.now()}})` — 팝업에 라인 뜨면 popup 코드는 정상, background가 호출 안 하는 것
3. SW devtools에서 `chrome.storage.local.get(null)` → 전체 키 dump해서 `geminiApiKey`는 있고 `lastBackend`만 없는지 확인

결과 종합하면 원인 단번에 잡힘. 의심 후보:
- (가장 유력) background의 `void setLastBackend(...).catch(...)` 가 comma-chain 안에서 esbuild가 이상하게 처리하는 케이스
- 또는 translateBatch가 성공처럼 보여도 어딘가에서 throw해서 setLastBackend 라인 못 가는 케이스
- 또는 storage write 자체가 무언가에 의해 차단되는 케이스 (manifest 권한은 정상)

관련: [[gemini-byok-backend]] 이 추가 작업의 일부.
