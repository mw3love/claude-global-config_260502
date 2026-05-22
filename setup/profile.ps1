# ~/.claude/setup/profile.ps1
# 각 PC의 $PROFILE이 이 파일을 dot-source.
# 매 새 PowerShell 세션 시작 시 자동 실행.

# 1) Bun PATH 보정 — VS Code/터미널이 stale env로 시작된 경우 대비
if (-not (Get-Command bun -ErrorAction SilentlyContinue)) {
    $bunBin = Join-Path $env:USERPROFILE '.bun\bin'
    if (Test-Path $bunBin) {
        $env:Path = "$bunBin;$env:Path"
    }
}

# 2) claude: 항상 로컬 모드. 텔레그램 폴링은 ctg에서만.
function claude {
    & claude.exe @args
}

# 3) ctg: 명시적 텔레그램 모드. lock으로 중복 활성 시 경고.
#    Telegram getUpdates는 토큰당 1 consumer만 허용 — 두 번째 ctg가
#    뜨면 첫 번째의 폴링을 SIGTERM으로 뺏어감. 경고로 알려줌.
function ctg {
    $lock = Join-Path $env:USERPROFILE '.claude\channels-bridge.pid'

    if (Test-Path $lock) {
        $existingPid = (Get-Content $lock -ErrorAction SilentlyContinue | Select-Object -First 1) -as [int]
        if ($existingPid -and (Get-Process -Id $existingPid -ErrorAction SilentlyContinue)) {
            Write-Host "[ctg] 경고: 다른 ctg 세션 활성 (PID $existingPid) · 이 세션이 폴링을 가져갑니다" -ForegroundColor Yellow
        } else {
            Remove-Item $lock -Force -ErrorAction SilentlyContinue
        }
    }

    $PID | Out-File $lock
    Write-Host "[ctg] 텔레그램 채널 활성 (PID $PID)" -ForegroundColor Green
    try {
        & claude.exe --channels plugin:telegram@claude-plugins-official @args
    } finally {
        Remove-Item $lock -Force -ErrorAction SilentlyContinue
    }
}
