# Claude Code 전역 환경 설치 스크립트
# 새 PC에서 한 번만 실행:
#   git clone https://github.com/mw3love/claude-global-config_260502.git ~/.claude
#   powershell.exe -ExecutionPolicy Bypass -File ~/.claude/setup.ps1

Write-Host ""
Write-Host "Claude Code 전역 환경 설치" -ForegroundColor Cyan
Write-Host "================================" -ForegroundColor Cyan

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path

# 쉘 bypass 별명 설치 (PowerShell / CMD / Git Bash)
& powershell.exe -ExecutionPolicy Bypass -File "$scriptDir\setup\install.ps1"

# 알림 테스트
Write-Host ""
Write-Host "토스트 알림 테스트 중..." -ForegroundColor Cyan
powershell.exe -NoProfile -Sta -ExecutionPolicy Bypass -File "$scriptDir\toast.ps1"

Write-Host ""
Write-Host "================================" -ForegroundColor Cyan
Write-Host "설치 완료!" -ForegroundColor Cyan
Write-Host "  1. claude 명령 → bypass 모드 자동 진입" -ForegroundColor White
Write-Host "  2. /draft 스킬 → KBS 기안문 작성" -ForegroundColor White
Write-Host "  3. 답변 완료 시 Windows toast 알림" -ForegroundColor White
Write-Host ""
