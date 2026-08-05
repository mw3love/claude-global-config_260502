---
name: project-embedded-audio-unmute-on-restart
description: "임베디드 오디오(패스스루) 음소거가 저절로 풀려 소리가 나는 버그 — 관찰 중, 미수정"
metadata: 
  node_type: memory
  type: project
  originSessionId: 2ff4edb4-b3f8-4a21-9078-a0fa3478f93a
---

운영자 보고(2026-06-15): 상단바 EMBEDDED AUDIO 볼륨아이콘으로 **음소거(패스스루 소리 끔)** 해뒀는데 가끔 저절로 소리가 남. ("알림음 켜짐/MUTE" 아님 — 스피커로 나가는 임베디드 오디오 소리.) 운영자는 **수동 재시작 안 함, 예약재시작도 당시 꺼져 있었음, 완전히 idle 상태**에서 소리가 났다고 함.

**근본 원인 (코드로 입증):** `ipc/shared_state.py` `_init_header()`가 앱 시작 시 mute를 **항상 0(해제)으로 하드코딩**, 저장된 `ui_state.embed_muted`를 안 읽음. main도 spawn 전 config의 mute를 shared_state에 안 넣음(main.py:232). → Detection이 기동 시 `shared_state.get_mute()`(=False)를 읽어 audio_worker를 **음소거 해제로 시작**(detection_process.py:471) → 패스스루 소리 남 → UI가 뒤늦게 DetectionReady 수신 후 `SetMute(embed_muted)` 재주입(main_window.py:405)으로 다시 끔. **그 사이에 소리 새는 창(window) 존재.**

**진단 좁힘:** Detection 재spawn *만* 으로는 음소거 안 풀림(shared_state가 main 소유라 값 유지). 소리가 나려면 **앱 전체 재시작**이 필요 → 운영자가 idle인데 났다면 **백그라운드 PC 재부팅(윈도우 자동업데이트 등) → `자동시작 등록`이 앱 재가동** 경로가 유력. (미확정 — 다른 운영자 증언으로 트리거 굳히는 중.)

**상태: 관찰 중, 코드 미수정 (긴급도 낮음).** 다음 발생 시 `logs/YYYYMMDD_ui.txt`에서 소리 난 시각 근처 `SYSTEM - ... 시작` 줄 유무로 앱 재시작 여부 확인 → 있으면 위 가설 확정. 이번에 넣은 HEALTH 로그/excepthook 보강이 역추적에 도움.

**제안 수정(승인 대기) 1+2+3:** ① main이 spawn 전 config embed_muted를 `shared_state.set_mute()`로 씨앗 주입(근본) ② audio_worker 기본값 `_muted=True`(안전망 — 방송모니터는 "실수로 조용"이 안전) ③ mute 토글 시 즉시 config 저장(현재는 종료 시에만 저장→크래시로 유실 가능).

관련: heartbeat 재spawn 폭풍 수정(2026-06-15 커밋 511198f)이 빈도는 줄이나 근본 해결 아님.
