---
name: jbnu-gateway
description: |
  전북대(mindlogic) API Gateway로 이미지·비디오·음성(TTS)·비-Claude LLM을 생성/호출한다.
  "이미지 만들어줘", "그림 생성", "TTS로 읽어줘", "음성 합성", "비디오/영상 생성",
  "gpt-image / veo / gemini 이미지·영상", "게이트웨이로 ~ 생성" 류 요청에 사용한다.
  현재 클로드코드 세션(Opus)은 그대로 두고, 멀티모달 생성만 게이트웨이에 위임한다.
argument-hint: "<생성 요청: 이미지/비디오/TTS 등>"
---

# JBNU Gateway — 멀티모달 생성 도구

전북대가 제공하는 mindlogic API Gateway를 **도구로** 호출해 이미지·비디오·음성을
생성한다. 클로드코드 자체의 모델은 바꾸지 않는다(= 지금 Opus 세션 유지). 게이트웨이는
평범한 REST이고, 헬퍼 스크립트가 base64 디코딩·비동기 폴링·PCM→WAV 변환을 처리한다.

- 베이스 URL: `https://factchat-cloud.mindlogic.ai/v1/gateway`
- 인증: `Authorization: Bearer <KEY>`
- 크레딧: 전 기능 공용 풀에서 차감(매월 1일 리셋). 비디오는 건당 비용 큼.

## API 키 (중요 — push되는 repo이므로 절대 하드코딩 금지)

스크립트는 키를 이 순서로 찾는다:
1. 환경변수 `JBNU_GATEWAY_API_KEY`
2. 파일 `~/.claude/.secrets/jbnu-gateway.key` (첫 줄)

`.secrets/` 는 `.gitignore` 되어 있어 커밋·push되지 않는다. 키가 아직 없으면 사용자에게
아래를 **사용자 본인이** 터미널에 입력하도록 안내한다(대화/트랜스크립트에 키를 남기지 않기 위해):

```
! mkdir -p ~/.claude/.secrets && printf '%s' 'DUAL_SUB에서_쓰던_키' > ~/.claude/.secrets/jbnu-gateway.key
```

키가 설정됐는지 확인: `python skills/jbnu-gateway/scripts/credits.py`

## 스크립트 사용법

작업 폴더와 무관하게 절대경로로 호출한다(예시는 `~/.claude` 기준 상대경로).

### 이미지 생성 (✅ 실조건 검증됨: gemini-2.5-flash-image)
```
python skills/jbnu-gateway/scripts/image.py \
  --prompt "노을 진 산맥, 드라마틱한 구름" --model gemini-2.5-flash-image --aspect 16:9 --out out.png
```
- **모델별 크기 파라미터가 다름**(중요):
  - Google `gemini-2.5-flash-image` → `--aspect 1:1|16:9|9:16|4:3` 사용
  - OpenAI `gpt-image-2` → `--aspect` 무시됨(빈 결과) → `--size 1024x1024` 써야 함
- 동기 모델은 즉시 저장(이미지는 `data[].url`에 data URI로 옴 → 스크립트가 디코딩)
- 비동기 모델: `black-forest-labs/flux-2-pro`, `xai/grok-imagine-image` — 폴링(스크립트가 처리)
- `--n` 여러 장 / `--quality standard|hd`(gemini) 또는 `low|medium|high`(gpt-image-2)

### TTS 음성
```
python skills/jbnu-gateway/scripts/tts.py \
  --text "안녕하세요, 테스트입니다" --voice Aoede --out speech.wav
```
- 모델: `gemini-2.5-flash-preview-tts`(기본), `gemini-2.5-pro-preview-tts`
- 음성: 여성 Aoede/Kore/Achernar 등, 남성 Charon/Puck/Fenrir 등 30여 종
- 응답은 raw PCM이지만 스크립트가 **WAV로 변환 저장**(.wav 강제) → 바로 재생 가능

### 비디오 생성 (비동기, 30~120초)
```
python skills/jbnu-gateway/scripts/video.py \
  --prompt "해돋이 무렵 고요한 산정호수" --model veo-3.1-fast-generate-preview --out out.mp4
```
- 모델/크레딧: `veo-3.1-fast`(600) `veo-3.1`(1600) `kling-v2.5`(350) `seedance-1-pro`(60) `hailuo-02`(270)
- image-to-video: `--image <URL>`
- 스크립트가 제출→폴링→다운로드 3단계를 자동 처리. `--timeout`(기본 240s) 초과 시
  `operation_id`를 안내하므로 나중에 재확인 가능.

### 사전 고지 (preflight) — 생성 전 잔액·모델·예상비용
```
python skills/jbnu-gateway/scripts/preflight.py video   # image | tts | chat | (없으면 잔액만)
```
실시간 잔액 + 해당 기능의 모델·단가·"잔액으로 N개 가능"을 출력. 단가표는 `costs.json`
(이미지/비디오/TTS 모델·단가는 /models API에 없어 문서·실측 기준). 단순 잔액만: `credits.py`.

## 사전 고지·승인 규칙 (필수)

생성 스크립트를 돌리기 **전에 반드시** `preflight.py <기능>` 결과를 사용자에게 보여준다.
출력에 ★추천 모델과 용도가 찍히므로, **어떤 모델을 왜 쓸지(추천+이유 1줄)를 항상 함께 말한다.**
"승인 불필요"가 "모델을 말없이 고름"이 되면 안 된다 — 추천은 항상 고지하고, 사용자가
다른 모델을 원하면 즉시 교체한다.
- **비디오** = 고비용(300~1600) → 추천 모델·예상비용 보여주고 **명시적 승인을 받은 뒤** 생성.
- **이미지·TTS** = 저렴 → 추천 모델·이유·비용을 **보여준 뒤 진행**(승인 대기는 불필요, 교체는 허용).
  용도가 추천 기본값과 다르면(예: 이미지에 글자 → `gpt-image-2`) 그 모델을 추천에 반영해 제시.

## 진행 방식

1. 요청에서 종류(이미지/TTS/비디오)와 파라미터를 정한다. 모델이 불명확하면 기본값 사용.
2. **`preflight.py <기능>` 실행 → 잔액·모델·예상비용을 사용자에게 보여준다**(위 승인 규칙).
3. 키 미설정 에러가 나면 위 "API 키" 안내로 사용자가 키를 넣게 한 뒤 재시도.
4. 생성 스크립트 실행 → 저장 경로를 사용자에게 보고. 이미지는 Read로 보여줄 수 있음.

## 주의

- **Cloudflare 403 / `error code: 1010`** 이 뜨면 키 문제가 아니라 User-Agent 차단이다.
  `_gw.py`가 브라우저형 User-Agent를 보내 해결해 둠. 그래도 막히면 UA 문자열을 갱신한다.
- 비동기 이미지의 폴링 status 엔드포인트는 문서에 명시가 약하다 → flux/grok에서 폴링이
  안 끝나면 응답 원문을 보고 경로를 조정한다(`image.py`의 폴링부). 동기 모델은 영향 없음.
- 이 스킬은 게이트웨이의 **생성 기능**만 다룬다. 클로드코드의 두뇌를 게이트웨이로 바꾸는
  것(`ANTHROPIC_BASE_URL` 교체)은 별개이며 여기서 하지 않는다.
