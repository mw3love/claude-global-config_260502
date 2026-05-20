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

# 2) claude 함수: lock 파일로 "한 번에 하나만 채널 활성" 보장
#    - 첫 세션이 bridge가 되어 봇 폴링 독점
#    - 추가 세션은 자동으로 로컬 모드 (give-up 영구 종료 회피)
#    - bridge 종료되면 lock 해제 → 다음 신규 세션이 자동 인계
function claude {
    $lock = Join-Path $env:USERPROFILE '.claude\channels-bridge.pid'
    $useChannels = $true

    if (Test-Path $lock) {
        $existingPid = (Get-Content $lock -ErrorAction SilentlyContinue | Select-Object -First 1) -as [int]
        if ($existingPid -and (Get-Process -Id $existingPid -ErrorAction SilentlyContinue)) {
            $useChannels = $false
            Write-Host "[claude] 텔레그램 채널 활성: 다른 터미널 PID $existingPid · 이 세션은 로컬" -ForegroundColor DarkGray
        } else {
            Remove-Item $lock -Force -ErrorAction SilentlyContinue
        }
    }

    if ($useChannels) {
        $PID | Out-File $lock
        Write-Host "[claude] 텔레그램 채널 활성 (이 세션, PID $PID)" -ForegroundColor Green
        try {
            & claude.exe --channels plugin:telegram@claude-plugins-official @args
        } finally {
            Remove-Item $lock -Force -ErrorAction SilentlyContinue
        }
    } else {
        & claude.exe @args
    }
}
