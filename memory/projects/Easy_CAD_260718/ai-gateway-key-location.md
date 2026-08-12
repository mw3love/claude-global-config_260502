---
name: ai-gateway-key-location
description: Easy CAD의 AI 이미지→도면 기능이 쓰는 게이트웨이 API 키 저장 위치와 해석 순서
metadata: 
  node_type: memory
  type: reference
  originSessionId: 01d3d827-622f-46cc-814d-d6bc99491335
  modified: 2026-08-11T12:20:01.963Z
---

`easycad/ai/gateway.py`(§8 항목18)가 쓰는 factchat 게이트웨이(`https://factchat.mindlogic-kr-api.com/v1/gateway`,
kairos 계정) 키는 `~/.claude/.secrets/easycad-gateway.key`(첫 줄, `.gitignore`됨)에서
읽는다 — `resolve_api_key()`의 최우선 소스(그다음 QSettings, 마지막 환경변수
`EASYCAD_GW_KEY`).

**주의: `jbnu-gateway` 스킬이 쓰는 `~/.claude/.secrets/jbnu-gateway.key`와는 다른
계정이다**(jbnu-gateway=전북대 학교 계정, easycad-gateway=kairos 회사 계정, base URL도
다름: `factchat-cloud.mindlogic.ai` vs `factchat.mindlogic-kr-api.com`). 두 파일을
섞어 쓰지 말 것.

**Why:** 2026-08-11 세션에서 사용자가 `!` 프리픽스로 키를 직접 타이핑하다 PowerShell
문법(`$env:...`)을 이 프로젝트의 Bash(Git Bash) 세션에 잘못 써서 명령이 실패하며 키가
대화 로그에 그대로 노출되는 사고가 발생했다. 재발 방지로 이 secrets 파일 관례를
도입했다 — 앞으로 이 기능을 실행/검증할 땐 사용자에게 키를 물어보거나 `!`로 타이핑
받지 말고, 이 파일이 이미 있는지부터 확인할 것(`Path.home()/".claude"/".secrets"/
"easycad-gateway.key"`가 존재하면 그냥 실행하면 된다).
