---
name: gemini-byok-backend
description: "Gemini API를 세 번째 번역 백엔드로 추가한 작업 (A20·A21). BYOK(사용자 본인 키) 모델, 모델 선택(Flash/Flash-Lite), 429 cooldown, 팝업 마지막 백엔드 표시 포함. 2026-05-27 마무리."
metadata: 
  node_type: memory
  type: project
  originSessionId: 239715da-8cf2-4c4c-84ae-5a37073195a6
---

YouTube Dual Subtitle 확장에 Gemini를 세 번째 번역 백엔드로 추가한 작업.

**Why:** google-free 번역 품질이 어색해서 사용자가 AI 번역 옵션을 요청. Web Store 배포 가능성 고려해 BYOK(키 미포함) 구조로 설계.

**How to apply:** 새 백엔드 추가나 Gemini 동작 관련 질문이 오면 이 메모와 CLAUDE.md 섹션 5·6·7·11·비명백한 주의사항 참고.

**커밋**:
- A20 (2026-05-27): Gemini 백엔드 본 작업. v0.1.0 → v0.2.0. router 인터페이스에 `used` 추가, secrets.ts 신설(storage.local 분리), 옵션·팝업 UI, manifest 권한 추가, 4개 문서(CLAUDE.md/README/PRIVACY/STORE_LISTING) 동기화.
- A21 (2026-05-27): 429 cooldown 60s + 팝업 "최근 번역" 한 줄. 단 사용자 검증에서 라인이 안 뜨는 이슈 발견 — [[pending-last-backend-debug]] 참조.

**주요 설계 결정**:
- API 키는 `chrome.storage.local` (settings의 sync와 분리) — 웹스토어 배포 시 키 동기화 방지
- Gemini는 내부적으로 20개씩 chunk 분할 — LLM이 50개 받으면 짧은 cue를 묶어 길이 mismatch 발생
- 캐시 키에 모델 합성(`gemini:flash` / `gemini:flash-lite`) — 백엔드 enum은 'gemini' 하나 유지하면서 모델별 결과 분리
- 테스트 버튼은 router 우회 (`TEST_GEMINI` 메시지 + `testGeminiKey` 직접 호출) — fallback이 키 오류를 가려 "성공"으로 보이는 사고 방지

**미해결 항목**:
- [[pending-last-backend-debug]] — 팝업 "최근 번역" 라인 안 뜨는 이슈
- capture 실패 문제 (`[YDT/main] gave up on timedtext after 3 attempts`) — TED 영상 등에서 가끔 발생. PoToken (lang, kind) binding 추정. 별도 큰 task.
