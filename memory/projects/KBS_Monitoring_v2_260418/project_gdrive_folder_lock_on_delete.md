---
name: project_gdrive_folder_lock_on_delete
description: "프로젝트가 Google Drive 동기화 폴더 — desktop.ini 잠금으로 폴더 rm -rf 실패, 빈 폴더는 사용자 수동 삭제"
metadata: 
  node_type: memory
  type: project
  originSessionId: b75f0611-379a-4c7e-9f90-4bcad1e7599b
---

이 프로젝트 루트(`G:\내 드라이브\...\260418 KBS_Monitoring_v2`)는 **Google Drive 데스크톱 동기화 폴더** 안에 있다. Drive 클라이언트가 각 폴더의 `desktop.ini`에 실시간 핸들을 유지해서, 디렉토리 삭제(`rm -rf`, `rmdir /s`, PowerShell `Remove-Item -Recurse`)가 `Access denied` / `Directory not empty`로 **부분 실패**한다 — 안의 파일은 지워지지만 **빈 폴더 껍데기가 남는다.**

**Why:** 이번 세션에서 Codex 산출물 `.agents/` 삭제 시 파일은 다 지워졌으나 빈 하위 폴더 2개(`skills`, `version`)가 Drive 잠금으로 안 지워졌다. 도구를 아무리 재시도해도 못 풀어서 결국 사용자가 탐색기에서 직접 삭제했다.

**How to apply:** 폴더 삭제가 필요하면 파일 삭제까지는 도구로 하되, **빈 폴더가 잠겨 안 지워지면 재시도로 시간 낭비하지 말고** 사용자에게 탐색기 수동 삭제 또는 Drive 동기화 일시중지를 요청한다. 콘솔 제약은 [[feedback_console_cp949_pythonioencoding]] 참조.
