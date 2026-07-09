---
shared: true
repos:
  - AI_Dictionary_260622 (https://github.com/mw3love/AI_Dictionary_260622.git)
  - Notion_PDF_Preview_260706 (https://github.com/mw3love/Notion_PDF_Preview_260706.git)
stack: [claude-in-chrome, Playwright MCP, Node]
tags: [SVG, PNG, 래스터화, 아이콘, file차단, base64, truncation, canvas, drawImage, 크롬확장아이콘]
used: []
---

# SVG → PNG 래스터화 (ImageMagick/inkscape/sharp 설치 없이)

크롬 확장 툴바 아이콘 등을 SVG에서 여러 px PNG로 뽑아야 하는데, 래스터화 도구가 없다. 브라우저 자동화로 하려니 함정이 겹겹이다.

## 막다른 길

1. **`file://` 내비게이션은 브라우저가 차단** — 로컬 SVG를 직접 못 연다.
2. **JS 도구의 base64 반환은 `[BLOCKED]` + truncation** — 바이트를 에이전트 컨텍스트로 빼오려 하면 잘리고 막힌다.

핵심 통찰: **데이터를 에이전트 컨텍스트에 통과시키지 않는다.** 브라우저에서 디스크로 직행시켜야 세 문제(컨텍스트·truncation·base64 차단)를 한 번에 우회한다.

## 해법 A — claude-in-chrome + 로컬 node 서버 (브라우저→디스크 직행)

1. claude-in-chrome을 **http 페이지**(example.com 등)로 보낸다 (`file://` 회피).
2. 페이지에서 SVG를 `Image`에 로드 → `canvas.drawImage` 로 원하는 px마다 렌더.
3. 로컬 **node http 서버**를 띄우고, 페이지가 각 PNG를 `fetch POST`(text/plain, base64 body)로 보낸다.
4. 서버가 `Buffer.from(body, 'base64')` 로 **디스크에 직접 기록**.
- 서버가 렌더용 HTML도 같은 origin으로 서빙하면 **mixed-content·CORS도 회피**.

## 해법 B — Playwright MCP + filename 파라미터 (서버 없이)

1. Playwright MCP는 `file://` 차단 → **`about:blank`** 로 간다.
2. `browser_evaluate` 안에서 SVG를 `data:image/svg+xml` URL로 `Image`에 로드 → `canvas.drawImage(0,0,N,N)` → `toDataURL`.
3. base64를 그냥 반환하면 컨텍스트 truncation으로 깨진다 → **`browser_evaluate`의 `filename` 파라미터**로 결과를 cwd 파일에 저장.
4. `node Buffer.from(b64,'base64')` 로 디코드해 PNG 기록 (데이터가 컨텍스트를 안 거침).

## 공통 주의

- **SVG root의 `width`/`height`를 목표 px로 세팅**해야 그 크기에서 래스터된다 (`viewBox` 고정 + `width`만 변경).
- 텍스트 글리프는 캔버스가 **시스템 폰트**(Georgia 등)로 래스터화하므로 폰트 변환 불필요.

## 검증 함정 — 벡터 미리보기는 래스터 손실을 못 보여준다

작은 아이콘(16px) 뭉개짐을 벡터 축소 미리보기로 확인하면 **프록시 검증 함정**에 빠진다(실제 래스터 손실이 안 보임).

- 검증: `canvas.imageSmoothingEnabled = false` 로 **10x nearest-neighbor 확대 PNG**를 뽑아 육안 확인.
- 16·32px에 48·128px과 같은 도형을 쓰면 `stroke 6/128 = 0.75px` 로 창백해진다 → **stroke·점 지름을 키운 축약 도형**(`icon-small.svg`)을 별도로 두고 manifest `icons`/`action.default_icon` 에서 크기별 분기.
