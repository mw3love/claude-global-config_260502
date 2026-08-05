---
name: project-moved-from-gdrive-to-local
description: 2026-07-13 프로젝트 작업 폴더를 Google Drive에서 로컬 C:\Users\minwoo\Dev\로 이전. 구 Drive 폴더는 백업으로 잔존.
metadata:
  type: project
---

2026-07-13, KBS Monitoring v2의 작업 폴더를 Google Drive 동기화 폴더에서 로컬로 이전했다.

- **현재 작업 경로 (여기서 작업할 것):** `C:\Users\minwoo\Dev\KBS_Monitoring_v2_260418`
- **구 경로 (백업용 잔존, 작업 금지):** `G:\내 드라이브\A1. 개인 자료\A1. AI 연습\260418 KBS_Monitoring_v2`
- 원격: `https://github.com/mw3love/KBS_Monitoring_v2_260418.git`

**Why:** Drive 동기화 폴더는 파일 잠금·부분 실패로 안정성이 떨어졌다([[project-gdrive-folder-lock-on-delete]] 참조). git clone으로 로컬에 새로 받아 이전했다.

**How to apply:** 이전 시 git이 가져오지 않은 것은 셋뿐이었다 — `config/kbs_config.json`(gitignore됨), `.claude/`(프로젝트 스킬), 그리고 Claude 프로젝트 메모리(경로 슬러그가 바뀌어 자동 승계 안 됨). 세 가지 모두 수동 복사했고, 새 폴더에서 테스트 76개 통과를 확인했다. 구 폴더에는 `logs/`(1.3MB)·`fix/`(10MB, 과거 사고 분석 자료 + 재현 mp4)·`images/`·`presentation/`이 남아 있으니 필요하면 거기서 꺼내온다.
