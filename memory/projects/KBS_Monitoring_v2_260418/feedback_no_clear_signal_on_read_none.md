---
name: SharedFramePoller에서 read_frame None 시 clear_signal 호출 금지
description: 깜빡임 버그 확인 완료 — Poller가 read_frame() None 반환 시 clear_signal()을 부르면 NO SIGNAL 화면이 깜빡임
type: feedback
originSessionId: 133b0efd-db6b-410e-becb-c5f97789c0d7
---
`SharedFramePoller._poll()`에서 `read_frame()`이 `None`을 반환할 때 `clear_signal()`을 호출하지 말 것. 이전 프레임을 그대로 유지해야 함.

**Why:** `read_frame()`의 None은 "신호 없음"이 아니라 "일시적 tearing/쓰기 중" (Lamport seq 레이스). clear_signal()을 호출하면 `_current_frame=None`이 되어 NO SIGNAL 화면이 렌더되고, 다음 poll에서 다시 정상 프레임이 오면 영상이 깜빡이는 것처럼 보임. 2026-04-23 웹캠 테스트로 확인.

**How to apply:**
- `_last_seq` 갱신도 read 성공 시에만 할 것 (실패 시 다음 poll에서 재시도)
- 진짜 "신호 없음"은 `VideoCaptureWorker`가 발행하는 `StreamError` 메시지로 UI 측에서 처리
- 이전 세션(260419)에서도 같은 수정을 시도했다가 원복됨 — 테스트 영상 환경에서는 증상이 안 보여서 "효과 없음"으로 잘못 판단한 것. 실제 웹캠에서만 재현됨.
