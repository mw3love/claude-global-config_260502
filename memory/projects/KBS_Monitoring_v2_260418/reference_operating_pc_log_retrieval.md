---
name: reference-operating-pc-log-retrieval
description: "송출센터 감시PC(운영 PC)의 실제 로그를 확인해야 할 때, 사용자가 Google Drive 경로로 복사해 전달하는 방식"
metadata: 
  node_type: memory
  type: reference
  originSessionId: c7c7fe2d-6761-4f81-9329-8f0d1d194ec8
  modified: 2026-08-07T04:11:01.458Z
---

운영 PC(전주총국 감시PC)는 Claude Code가 직접 접근할 수 없다. 로그 확인이 필요하면 사용자가 운영 PC의 `logs/` 폴더를 통째로 복사해 `H:\내 드라이브\logs`(Google Drive, 이 PC에서는 `/h/내 드라이브/logs`)에 올려준다.

**How to apply**: "운영 PC에서 재발했는지/무사고인지 확인해달라" 류 요청을 받으면, 로그 없이 판단하지 말고(규칙 1) 이 경로에 로그가 이미 와 있는지 먼저 확인하거나 사용자에게 복사를 요청한다. 파일명 패턴은 `YYYYMMDD_{ui,detection,watchdog}.txt` + `fault*.log` + `stderr_debug.txt`. HEALTH 스냅샷(10분 주기, RSS/threads/handles)이 각 프로세스 로그에 있으므로 재시작·재spawn·메모리 추세는 이 파일들만으로 대부분 실측 가능하다. [[project_black_recovery_telegram_missing]]과 같은 "관찰 중" 항목도 다음 재발 시 이 경로로 로그를 받아 판정한다.
