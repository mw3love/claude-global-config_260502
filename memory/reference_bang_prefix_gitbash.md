---
name: bang-prefix-runs-gitbash-not-powershell
description: "이 환경에서 사용자의 `!` 프리픽스 명령은 Git Bash로 실행된다 — PowerShell 문법을 안내하면 실패하며 그 과정에서 민감정보가 대화에 그대로 노출된다"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 01d3d827-622f-46cc-814d-d6bc99491335
  modified: 2026-08-11T10:20:29.763Z
---

이 프로젝트 세션(Windows, PowerShell 도구도 함께 제공되는 환경)에서 사용자가 `!` 프리픽스로
직접 입력하는 명령은 **Git Bash(POSIX sh)로 실행**되지, PowerShell로 실행되지 않는다.

2026-08-11(다른 PC 세션 인계 후 이 세션)에 API 키를 대화에 남기지 않으려고 사용자에게
`! $env:EASYCAD_GW_KEY="..."`(PowerShell 문법)를 안내했는데, 실제로는 bash가 이를
파싱하다 실패(`command not found`)했고 그 과정에서 **입력한 키 값이 이미 대화 로그에
그대로 남았다** — 정작 피하려던 노출이 문법 실수로 발생.

**Why:** 이 하네스는 Bash 도구(Git Bash)와 PowerShell 도구를 둘 다 제공하지만, 사용자가
채팅창에 `!`를 직접 타이핑해 실행하는 경로는 Bash(Git Bash)로 고정되어 있다 — Claude가
Bash/PowerShell 중 어느 쪽을 선택하는 것과 별개로, 사용자 직접입력 경로는 셸이 고정이다.

**How to apply:** 사용자에게 `!` 프리픽스로 환경변수·민감정보 설정을 요청할 때는
`export VAR="값"`(bash 문법)으로 안내한다. `$env:VAR="값"`(PowerShell) 문법을 쓰면 안 된다.
더 안전한 대안: 애초에 사용자에게 타이핑을 요청하지 말고, Claude가 Bash 도구로 직접
`EASYCAD_GW_KEY="키" python ...`처럼 한 호출 안에서 인라인으로 넘기도록 설계하면(이번
세션처럼 이미 노출된 값을 재사용하는 경우가 아니라 애초부터), 사용자가 셸 문법을 몰라도
되고 실패 여지도 없다. Bash 도구는 호출 간 셸 상태(export)가 유지되지 않으므로, 여러
호출에 걸쳐 키가 필요하면 매 호출마다 인라인 접두어로 다시 넘겨야 한다.
