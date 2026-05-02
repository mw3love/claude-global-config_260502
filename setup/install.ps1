$ErrorActionPreference = "Stop"
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path

Write-Host "=== Claude Code 환경 설치 시작 ===" -ForegroundColor Cyan

# 1. claude.cmd -> %USERPROFILE%\.local\bin\
$binPath = "$env:USERPROFILE\.local\bin"
if (-not (Test-Path $binPath)) { New-Item -ItemType Directory -Path $binPath -Force | Out-Null }
Copy-Item "$scriptDir\claude.cmd" "$binPath\claude.cmd" -Force
Write-Host "[OK] CMD bypass 설정 완료" -ForegroundColor Green

# 2. PowerShell 프로필 설정
$psProfileDir = Split-Path $PROFILE
if (-not (Test-Path $psProfileDir)) { New-Item -ItemType Directory -Path $psProfileDir -Force | Out-Null }
Copy-Item "$scriptDir\profile.ps1" $PROFILE -Force
Write-Host "[OK] PowerShell bypass 설정 완료" -ForegroundColor Green

# 3. PowerShell 실행 정책
Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned -Force
Write-Host "[OK] PowerShell 실행 정책 설정 완료" -ForegroundColor Green

# 4. CMD AutoRun 레지스트리
$cmdKey = "HKCU:\Software\Microsoft\Command Processor"
if (-not (Test-Path $cmdKey)) { New-Item -Path $cmdKey -Force | Out-Null }
Set-ItemProperty -Path $cmdKey -Name "AutoRun" -Value "doskey claude=`"$env:USERPROFILE\.local\bin\claude.exe`" --dangerously-skip-permissions `$*" -Type String
Write-Host "[OK] CMD AutoRun 설정 완료" -ForegroundColor Green

# 5. Windows 알림 활성화
$pushKey = "HKCU:\SOFTWARE\Microsoft\Windows\CurrentVersion\PushNotifications"
if (-not (Test-Path $pushKey)) { New-Item -Path $pushKey -Force | Out-Null }
Set-ItemProperty $pushKey -Name "ToastEnabled" -Value 1 -Type DWord
Write-Host "[OK] Windows 알림 활성화 완료" -ForegroundColor Green

# 6. Git Bash .bashrc 설정
$bashrc = "$env:USERPROFILE\.bashrc"
if (-not (Test-Path $bashrc)) { New-Item -ItemType File -Path $bashrc -Force | Out-Null }
$bashrcContent = Get-Content $bashrc -Raw -ErrorAction SilentlyContinue
if ($bashrcContent -notlike "*dangerously-skip-permissions*") {
    $snippet = Get-Content "$scriptDir\bashrc_snippet.sh" -Raw
    Add-Content $bashrc "`n$snippet"
    Write-Host "[OK] Git Bash bypass 설정 완료" -ForegroundColor Green
} else {
    Write-Host "[SKIP] Git Bash bypass 이미 설정됨" -ForegroundColor Yellow
}

# 7. post-commit 훅 설치
$hooksDir = "$env:USERPROFILE\.claude\.git\hooks"
if (Test-Path $hooksDir) {
    Copy-Item "$scriptDir\hooks\post-commit" "$hooksDir\post-commit" -Force
    git -C "$env:USERPROFILE\.claude" update-index --chmod=+x "setup/hooks/post-commit" 2>$null
    Write-Host "[OK] post-commit 훅 설치 완료" -ForegroundColor Green
}

Write-Host "`n=== 설치 완료! 새 터미널을 열어주세요 ===" -ForegroundColor Cyan
