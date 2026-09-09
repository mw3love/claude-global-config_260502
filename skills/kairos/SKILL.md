---
name: kairos
description: |
  mindlogic API Gateway(KAIROS 회사 계정 / JBNU 학교 계정)로 이미지·비디오·음성(TTS)을
  생성하고, GPT 계열 모델에 계획·코드 교차검증을 맡긴다.
  "이미지 만들어줘", "그림 생성", "TTS로 읽어줘", "음성 합성", "비디오/영상 생성",
  "gpt-image / veo / gemini 이미지·영상", "게이트웨이로 ~ 생성" 요청에 사용한다.
  또한 "계획 교차검증해줘", "이 코드 GPT로 검증해줘", "2차 소견 받아줘" 요청과,
  전역 규칙 11-b 스턱루프 2회째의 자동 교차검증에서도 이 스킬을 쓴다.
  현재 클로드코드 세션의 모델은 그대로 두고, 생성·교차검증만 게이트웨이에 위임한다.
argument-hint: "<생성 요청 또는 교차검증 요청>"
---

# KAIROS — mindlogic 게이트웨이 도구 (생성 + 교차검증)

mindlogic API Gateway를 **도구로** 호출해 이미지·비디오·음성을 생성하고, 다른 회사
모델(GPT 계열)에 교차검증을 맡긴다. 클로드코드 자체의 모델은 바꾸지 않는다. 게이트웨이는
평범한 REST이고, 헬퍼 스크립트가 base64 디코딩·비동기 폴링·PCM→WAV 변환을 처리한다.

## 계정 (2개, 용도 분리 — 자동 폴백 금지)

| 계정 | 월 크레딧 | 용도 | base URL |
|---|---|---|---|
| `kairos` (기본) | 40,000 | 코딩·교차검증 | `factchat.mindlogic-kr-api.com/v1/gateway` |
| `jbnu` | 10,000 | 번역·OCR 등 저비용 도구 | `factchat-cloud.mindlogic.ai/v1/gateway` |

모든 스크립트가 `--account kairos|jbnu` 를 받는다(생략 시 `kairos`).

⚠ **자동 폴백을 하지 않는다.** 두 계정은 용도가 분리된 별개 예산이라, kairos가 모자라도
말없이 jbnu를 끌어 쓰면 도구용 예산이 잠식된 걸 나중에야 알게 된다. kairos 잔액이 부족하면
**사용자에게 알리고 전환 여부를 물은 뒤** `--account jbnu` 로 명시 전환한다.

인증은 `Authorization: Bearer <KEY>`. 크레딧은 계정별 공용 풀에서 차감(매월 1일 리셋),
비디오는 건당 비용이 크다.

## API 키 (중요 — push되는 repo이므로 절대 하드코딩 금지)

스크립트는 계정별로 키를 이 순서로 찾는다:

| 계정 | 환경변수 | 파일 (첫 줄) |
|---|---|---|
| `kairos` | `KAIROS_GATEWAY_API_KEY` | `~/.claude/.secrets/kairos-gateway.key` |
| `jbnu` | `JBNU_GATEWAY_API_KEY` | `~/.claude/.secrets/jbnu-gateway.key` |

`.secrets/` 는 `.gitignore` 되어 있어 커밋·push되지 않는다. 키가 없으면 사용자에게
아래를 **사용자 본인이** 터미널에 입력하도록 안내한다(대화/트랜스크립트에 키를 남기지 않기 위해):

```
! printf '%s' '발급받은_키' > ~/.claude/.secrets/kairos-gateway.key
```

키·잔액 확인: `python skills/kairos/scripts/preflight.py` (두 계정 상태를 함께 표시)

## 스크립트 사용법

작업 폴더와 무관하게 절대경로로 호출한다(예시는 `~/.claude` 기준 상대경로).

### 이미지 생성 (✅ 실조건 검증됨: gemini-2.5-flash-image)
```
python skills/kairos/scripts/image.py \
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
python skills/kairos/scripts/tts.py \
  --text "안녕하세요, 테스트입니다" --voice Aoede --out speech.wav
```
- 모델: `gemini-2.5-flash-preview-tts`(기본), `gemini-2.5-pro-preview-tts`
- 음성: 여성 Aoede/Kore/Achernar 등, 남성 Charon/Puck/Fenrir 등 30여 종
- 응답은 raw PCM이지만 스크립트가 **WAV로 변환 저장**(.wav 강제) → 바로 재생 가능

### 비디오 생성 (비동기, 30~120초)
```
python skills/kairos/scripts/video.py \
  --prompt "해돋이 무렵 고요한 산정호수" --model veo-3.1-fast-generate-preview --out out.mp4
```
- 모델/크레딧: `veo-3.1-fast`(600) `veo-3.1`(1600) `kling-v2.5`(350) `seedance-1-pro`(60) `hailuo-02`(270)
- image-to-video: `--image <URL>`
- 스크립트가 제출→폴링→다운로드 3단계를 자동 처리. `--timeout`(기본 240s) 초과 시
  `operation_id`를 안내하므로 나중에 재확인 가능.

### 사전 고지 (preflight) — 생성 전 잔액·모델·예상비용
```
python skills/kairos/scripts/preflight.py video   # image | tts | chat | (없으면 잔액만)
```
실시간 잔액 + 해당 기능의 모델·단가·"잔액으로 N개 가능"을 출력. 단가표는 `costs.json`
(모델·단가가 /models API에 없어 문서·실측 기준). 단순 잔액만: `credits.py`.

`chat`은 1M 토큰당 크레딧(2026-09-09 실측, **1크레딧 = $0.001**로 실제 API 정가와 1:1).
**캐시읽기는 입력의 10%** — GPT 계열은 `/chat/completions/`에서 자동 적용되지만 Claude는
`/claude/v1/messages` + `cache_control` 블록을 써야 하고, OpenAI 호환 경로로 부르면
캐시가 아예 안 걸린다(실측 절감 0%).

### 교차검증 (✅ 실조건 검증됨: gpt-6-astra, 2026-09-09)

다른 회사 모델에 계획·코드의 **2차 소견**을 받는다. 수동 호출과 전역 규칙 11-b
스턱루프 2회째의 자동 호출이 **같은 스크립트**를 쓴다.

```
python skills/kairos/scripts/crosscheck.py --mode plan \
  --req "사용자 원문 요구사항" --target 계획.md
python skills/kairos/scripts/crosscheck.py --mode code \
  --req "요구사항" --target src/auth.py --error error.log
```

- `--req` · `--target` · `--error` 는 **파일 경로 또는 문자열** 둘 다 받는다.
- `--dry-run` 으로 보낼 내용과 예상 비용을 먼저 확인할 수 있다(비용 추정은 상한값).
- `--model` 기본 `gpt-6-astra`. 저렴하게 하려면 `gpt-5.6-sol` / `gpt-5.6-terra`.
- ⚠ `--max-tokens` 기본 4000. **추론 모델이라 이 값이 작으면 답변 없이 크레딧만 나간다**
  (실측: 500으로 주면 500 전부가 reasoning_tokens로 소모되고 본문이 비어 나옴).

**전달 규격 — 이 스킬의 존재 이유다. 반드시 지킬 것:**

| 넘긴다 | 넘기지 않는다 |
|---|---|
| 사용자 원문 요구사항 | **내 추론 과정** |
| 코드·계획 원문 | 내가 세운 가설 |
| 에러·로그 원문 | 내가 이미 시도한 것의 해석 |

내 추론을 넣으면 검증자가 내 프레임에 끌려와 독립성이 사라진다. 같은 컨텍스트를
공유하면 **같은 오해도 공유**하므로, 1차 자료만 넘기는 것이 핵심이다.

**비용 감각** — 계획 검증은 대개 소형(입력 20k 이하)이라 astra로도 300 크레딧 미만.
실측 예: 입력 217 / 출력 345 토큰 = 19.4 크레딧. 월 26회 기준 예산의 20% 수준.

## 사전 고지·승인 규칙 (필수)

생성 스크립트를 돌리기 **전에 반드시** `preflight.py <기능>` 결과를 사용자에게 보여준다.
출력에 ★추천 모델과 용도가 찍히므로, **어떤 모델을 왜 쓸지(추천+이유 1줄)를 항상 함께 말한다.**
"승인 불필요"가 "모델을 말없이 고름"이 되면 안 된다 — 추천은 항상 고지하고, 사용자가
다른 모델을 원하면 즉시 교체한다.
- **비디오** = 고비용(300~1600) → 추천 모델·예상비용 보여주고 **명시적 승인을 받은 뒤** 생성.
- **이미지·TTS** = 저렴 → 추천 모델·이유·비용을 **보여준 뒤 진행**(승인 대기는 불필요, 교체는 허용).
  용도가 추천 기본값과 다르면(예: 이미지에 글자 → `gpt-image-2`) 그 모델을 추천에 반영해 제시.

## 진행 방식

**생성(이미지/TTS/비디오)**

1. 요청에서 종류와 파라미터를 정한다. 모델이 불명확하면 기본값 사용.
2. **`preflight.py <기능>` 실행 → 잔액·모델·예상비용을 사용자에게 보여준다**(위 승인 규칙).
3. 키 미설정 에러가 나면 위 "API 키" 안내로 사용자가 키를 넣게 한 뒤 재시도.
4. 생성 스크립트 실행 → 저장 경로를 사용자에게 보고. 이미지는 Read로 보여줄 수 있음.

**교차검증**

1. 검토 대상(계획/코드)과 **사용자 원문 요구사항**을 모은다. 내 추론은 넣지 않는다.
2. `crosscheck.py` 실행. 저비용이라 사전 승인은 불필요하되 **어떤 모델을 쓰는지는 고지**한다.
3. 받은 소견을 답에 반영하고, 이 한 줄을 남긴다:
   `외부 교차검증: {모델} — 질의 {요지} / 결과 {한 줄}`
4. 소견에 동의하지 않으면 **동의하지 않는다고 근거와 함께 쓴다**. 외부 모델 말이라고
   무조건 따르는 것은 교차검증이 아니라 책임 전가다.

## 주의

- **Cloudflare 403 / `error code: 1010`** 이 뜨면 키 문제가 아니라 User-Agent 차단이다.
  `_gw.py`가 브라우저형 User-Agent를 보내 해결해 둠. 그래도 막히면 UA 문자열을 갱신한다.
- 비동기 이미지의 폴링 status 엔드포인트는 문서에 명시가 약하다 → flux/grok에서 폴링이
  안 끝나면 응답 원문을 보고 경로를 조정한다(`image.py`의 폴링부). 동기 모델은 영향 없음.
- 이 스킬은 게이트웨이의 **생성 기능**만 다룬다. 클로드코드의 두뇌를 게이트웨이로 바꾸는
  것(`ANTHROPIC_BASE_URL` 교체)은 별개이며 여기서 하지 않는다.
- ⚠ 그 교체를 굳이 한다면 **비용을 먼저 보라**. 2026-09-09 실측: 8일간 입력 11억 토큰,
  실제 활성 작업 17.1시간. 크레딧으로 환산하면 **활성 1시간당 약 29,000 크레딧**이라
  4만 크레딧은 **실제 코딩 1.4시간**이다(캐시가 정상 작동하는 조건에서). 같은 페이스를
  30일 지속하면 월 약 187만 크레딧이 필요하다.
  에이전트 코딩은 매 턴 컨텍스트를 통째로 재전송하므로 입력:출력이 223:1이고,
  비용의 98%가 캐시읽기에서 나온다. **크레딧을 메인 코딩에 쓰는 것은 어떤 모델로도 불가.**
  ※ "N일치"로 세지 말 것 — 달력 시간은 대기 시간을 포함해 실제보다 후하게 보인다.
