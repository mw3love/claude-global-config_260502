# Claude Code 전역 환경 설치 스크립트
# 새 PC / 기존 PC 구분 없이 아래 한 줄로 실행:
#   irm https://raw.githubusercontent.com/mw3love/claude-global-config_260502/main/setup.ps1 | iex

$claudeDir  = "$env:USERPROFILE\.claude"
$configRepo = "https://github.com/mw3love/claude-global-config_260502.git"

Write-Host ""
Write-Host "Claude Code 전역 환경 설치" -ForegroundColor Cyan
Write-Host "================================" -ForegroundColor Cyan

# 1. ~/.claude git 동기화 (clone 또는 pull)
if (-not (Test-Path "$claudeDir\.git")) {
    if (Test-Path $claudeDir) {
        Write-Host "기존 ~/.claude 발견 → git 초기화 후 병합..." -ForegroundColor Yellow
        git -C $claudeDir init
        git -C $claudeDir remote add origin $configRepo
        git -C $claudeDir fetch origin main
        git -C $claudeDir checkout -b main --track origin/main 2>$null
    } else {
        Write-Host "~/.claude 없음 → clone 중..." -ForegroundColor Yellow
        git clone $configRepo $claudeDir
    }
    Write-Host "[OK] ~/.claude 동기화 완료" -ForegroundColor Green
} else {
    Write-Host "git 저장소 발견 → pull 중..." -ForegroundColor Yellow
    git -C $claudeDir pull origin main
    Write-Host "[OK] ~/.claude 최신화 완료" -ForegroundColor Green
}

# 2. 쉘 bypass 별명 설치 (PowerShell / CMD / Git Bash)
& powershell.exe -ExecutionPolicy Bypass -File "$claudeDir\setup\install.ps1"

# 3. 알림 테스트
Write-Host ""
Write-Host "토스트 알림 테스트 중..." -ForegroundColor Cyan
powershell.exe -NoProfile -Sta -ExecutionPolicy Bypass -File "$claudeDir\toast.ps1"

Write-Host ""
Write-Host "================================" -ForegroundColor Cyan
Write-Host "설치 완료!" -ForegroundColor Cyan
Write-Host "  1. claude 명령 → bypass 모드 자동 진입" -ForegroundColor White
Write-Host "  2. /draft 스킬 → KBS 기안문 작성" -ForegroundColor White
Write-Host "  3. 답변 완료 시 Windows toast 알림" -ForegroundColor White
Write-Host ""
