<#
새 세션 핸드오프: 프롬프트를 클립보드에 그대로(파싱 없이) 심고,
같은 Windows Terminal 창에 새 탭을 열어 claude를 인자 없이 대기시켜 놓는다.
사용자는 새 탭에서 Ctrl+V -> Enter만 하면 된다.
wt.exe가 없으면(다른 PC 등) 새 탭 오픈은 건너뛰고 클립보드 복사까지만 한다 -
호출자(Claude)는 이 경우 기존 [프롬프트] 코드블록 방식으로 폴백해야 한다.
#>
param(
    [Parameter(Mandatory = $true)][string]$PromptFile,
    [string]$Cwd = (Get-Location).Path
)

if (-not (Test-Path $PromptFile)) {
    Write-Error "PromptFile not found: $PromptFile"
    exit 1
}

$promptText = Get-Content -Raw -Encoding UTF8 $PromptFile
Set-Clipboard -Value $promptText

$wt = Get-Command wt.exe -ErrorAction SilentlyContinue
if ($wt) {
    Start-Process wt.exe -ArgumentList @('-w', '0', 'new-tab', '-d', $Cwd, 'claude')
    Write-Output "HANDOFF_OK: clipboard set, new tab opened (wt.exe)"
} else {
    Write-Output "HANDOFF_PARTIAL: clipboard set, wt.exe not found - no tab opened"
}
