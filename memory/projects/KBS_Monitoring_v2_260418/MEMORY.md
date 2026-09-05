# Memory Index

- [작업 폴더 Drive → 로컬 이전](project_moved_from_gdrive_to_local.md) — 2026-07-13 이후 작업 경로는 C:\Users\minwoo\Dev\KBS_Monitoring_v2_260418. 구 Drive 폴더는 백업으로만 잔존.
- [SharedFramePoller clear_signal 금지](feedback_no_clear_signal_on_read_none.md) — read_frame() None 시 clear_signal() 호출 금지. 깜빡임 버그 원인. 실제 웹캠에서만 재현.
- [SysMonitorWidget 레이블 2줄 유지](feedback_sysmonitor_label_format.md) — CPU/RAM/GPU 레이블은 "CPU\n45%" 2줄 형식. 단일행 변경 시도 후 사용자 복원 요청.
- [Google Drive 폴더 삭제 잠금](project_gdrive_folder_lock_on_delete.md) — Drive 동기화 폴더라 rm -rf가 빈 폴더 잠금으로 부분 실패. 재시도 말고 사용자 수동 삭제 요청.
- [임베디드 오디오 음소거 저절로 풀림](project_embedded_audio_unmute_on_restart.md) — 앱 재시작 시 shared_state mute=0 하드코딩 → 패스스루 소리 새는 창. 관찰 중, 미수정. 다음 발생 시 ui로그 "시작" 줄 확인.
- [블랙 복구 텔레그램 누락](project_black_recovery_telegram_missing.md) — 진입 알림은 나가는데 복구 알림 누락(확정·미해결). 다음 재발 관측 대기, 진단 로깅 선행. fix/260720 문서.
- [운영 PC 로그 회수 경로](reference_operating_pc_log_retrieval.md) — 사용자가 H:\내 드라이브\logs로 감시PC 로그를 복사해 전달. 재발/무사고 판정엔 이 로그부터 요청.
