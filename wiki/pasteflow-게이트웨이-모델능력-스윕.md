---
repo: PasteFlow
remote: https://github.com/mw3love/Paste_flow.git
stack: [Python, OpenAI호환 API, Gemini]
tags: [LLM게이트웨이, 유령모델, 텍스트전용모델, 색판별, 자동폴백, grounding, 429, 모델능력]
reuse: 게이트웨이/BYOK LLM을 쓰는 모든 프로젝트(AI 사전·Reading Highlighter 등)
used: []
---

# OpenAI 호환 LLM 게이트웨이 — 모델 능력 전수 스윕

## 함정 — `/models`가 광고하는 모델이 실제로는 안 된다

OpenAI 호환 게이트웨이의 `/models` 목록을 믿으면 두 종류 지뢰를 밟는다.

- **유령 모델** — 목록엔 있는데 호출하면 **404**
- **텍스트 전용 모델** — 텍스트는 되는데 이미지 입력을 주면 **400**

목록만으로는 구분이 안 된다. OCR(비전 필수) 기능에 텍스트 전용 모델을 물리면 런타임에 터진다.

## 해법 — 단색 PNG로 능력을 직접 때려본다

- **단색 PNG 색 판별**로 이미지 입력 가능 여부를 실측한다.
- **빨강/파랑 교차 검증**으로 위양성(우연히 맞힌 것)을 제거한다.
- 결과로 **OCR용 모델 설정과 AI 질의용 모델 설정을 분리**한다.

## 함정 속 함정 — 자동 폴백이 실패를 성공처럼 감춘다

`_call_with_fallback` 같은 자동 폴백이 있으면, **유령 모델 호출 실패가 폴백 성공으로 덮여** 스윕 결과가 거짓 양성이 된다.

**해법:** `last_used_model != 요청 모델` 로 걸러낸다. 폴백이 다른 모델로 답했으면 원래 요청 모델은 실패한 것으로 친다.

## 인접 함정 — Gemini grounding 폴백

Gemini 웹검색 grounding(`google_search` 도구)을 쓸 때, **검색 무료 할당량이 없는 모델**은 `429`를 뱉는다. → 안전망 모델로 자동 폴백해야 한다. (SDK는 폐기된 `google-generativeai` → 신 `google-genai` 로 이전.)
