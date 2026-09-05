---
name: reference-gdrive-folder-lock-on-delete
description: Google Drive 동기화 폴더 안 디렉토리 삭제 시 desktop.ini 잠금으로 빈 폴더 껍데기가 남는 Windows 동작 — rm -rf/rmdir 재시도로 안 풀림
metadata: 
  node_type: memory
  type: reference
  originSessionId: b5fac949-8681-4bc8-ac9f-20d984667269
  modified: 2026-09-05T12:34:48.390Z
---

Google Drive 데스크톱 동기화 폴더 안에 있는 프로젝트에서 디렉토리를 삭제(`rm -rf`,
`rmdir /s`, PowerShell `Remove-Item -Recurse`)하면, Drive 클라이언트가 각 폴더의
`desktop.ini`에 실시간 핸들을 유지해서 `Access denied` / `Directory not empty`로
**부분 실패**한다 — 안의 파일은 지워지지만 **빈 폴더 껍데기가 남는다.**

**Why:** KBS_Monitoring_v2 프로젝트가 아직 `G:\내 드라이브\...`에 있던 시절(2026-07-13
로컬 이전 전) 실제로 겪음 — Codex 산출물 `.agents/` 삭제 시 파일은 다 지워졌으나 빈
하위 폴더 2개(`skills`, `version`)가 Drive 잠금으로 안 지워짐. 도구를 아무리 재시도해도
못 풀어서 결국 사용자가 탐색기에서 직접 삭제.

**How to apply:** 지금 여는 프로젝트가 Drive 동기화 폴더 안에 있는지 먼저 확인
([[reference_google_drive_accounts]] 참조 — mw-lenovo 기준 G:=개인/H:=회사공유 둘 다
동기화 대상). 그 안에서 폴더 삭제가 필요하면 파일 삭제까지는 도구로 하되, **빈 폴더가
잠겨 안 지워지면 재시도로 시간 낭비하지 말고** 사용자에게 탐색기 수동 삭제 또는 Drive
동기화 일시중지를 요청한다.
