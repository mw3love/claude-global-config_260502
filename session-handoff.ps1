<#
새 세션 핸드오프: 프롬프트를 클립보드에 그대로(파싱 없이) 심는다.
새 탭/새 창을 어디에 열지는 사용자가 직접 고른다 - 여러 터미널 창을
동시에 쓰는 워크플로우에서 자동으로 창을 골라 여는 건 예측 불가능하고
방해가 된다는 게 실측(2026-08-07)으로 확인됨(`wt.exe -w 0`이 지금 이 세션의
창이 아니라 다른 창으로 감).
#>
param(
    [Parameter(Mandatory = $true)][string]$PromptFile
)

if (-not (Test-Path $PromptFile)) {
    Write-Error "PromptFile not found: $PromptFile"
    exit 1
}

$promptText = Get-Content -Raw -Encoding UTF8 $PromptFile
Set-Clipboard -Value $promptText
Write-Output "HANDOFF_OK: clipboard set"
