# Memory Index

- [작업 폴더 Drive → 로컬 이전](project_moved_from_gdrive_to_local.md) — 2026-07-13 이후 작업 경로는 C:\Users\minwoo\Dev\KBS_Monitoring_v2_260418. 구 Drive 폴더는 백업으로만 잔존.
- [SharedFramePoller clear_signal 금지](feedback_no_clear_signal_on_read_none.md) — read_frame() None 시 clear_signal() 호출 금지. 깜빡임 버그 원인. 실제 웹캠에서만 재현.
- [SysMonitorWidget 레이블 2줄 유지](feedback_sysmonitor_label_format.md) — CPU/RAM/GPU 레이블은 "CPU\n45%" 2줄 형식. 단일행 변경 시도 후 사용자 복원 요청.
- [토론 → 결정 → 실행 분리](feedback_discuss_before_implement.md) — 안전망·추상화 제안 시 코드 수정 보류. 단순 해결책 우선. 새 실패 모드 도입 위험 명시적 비교.
- [콘솔 cp949 → PYTHONIOENCODING=utf-8](feedback_console_cp949_pythonioencoding.md) — 한글/유니코드 출력 Python 실행 시 인코딩 지정 필수. 출력 크래시를 코드 버그로 오진 말 것.
- [Google Drive 폴더 삭제 잠금](project_gdrive_folder_lock_on_delete.md) — Drive 동기화 폴더라 rm -rf가 빈 폴더 잠금으로 부분 실패. 재시도 말고 사용자 수동 삭제 요청.
- [임베디드 오디오 음소거 저절로 풀림](project_embedded_audio_unmute_on_restart.md) — 앱 재시작 시 shared_state mute=0 하드코딩 → 패스스루 소리 새는 창. 관찰 중, 미수정. 다음 발생 시 ui로그 "시작" 줄 확인.
- [블랙 복구 텔레그램 누락](project_black_recovery_telegram_missing.md) — 진입 알림은 나가는데 복구 알림 누락(확정·미해결). 다음 재발 관측 대기, 진단 로깅 선행. fix/260720 문서.
