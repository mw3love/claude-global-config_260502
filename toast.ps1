param([string]$Message = 'Response complete', [switch]$Persist)

# 2026-07-22: 우하단 WinRT 토스트는 기본 제거, 중앙 팝업(center-toast.ps1)으로 화면 알림
# 단일화(응답완료 알림은 하루 수십 번 뜨므로 중복의 피로 비용이 큼). 단 -Persist 플래그를
# 주면 우하단 토스트도 같이 띄운다 — 알림센터(종 아이콘)에 남아 놓쳐도 나중에 확인 가능한
# 게 핵심 차이. 사람이 안 지켜보는 자동화(sync-repos 등, 로그온 1회처럼 저빈도)는 놓치면
# 대안이 없어 이 지속성이 필요하고, 고빈도인 일반 응답완료는 -Persist 없이 호출한다.
# 알림음은 유지(비동기 재생이라 아래 팝업을 안 막음).
try { [System.Media.SystemSounds]::Asterisk.Play() } catch { }

# 활성 모니터 정중앙 팝업 — 메인 시각 알림. 텔레그램보다 먼저 호출해야 함(아래 참고).
try {
    $centerScript = Join-Path $env:USERPROFILE '.claude\center-toast.ps1'
    if (Test-Path $centerScript) { & $centerScript -Message $Message }
} catch { }

# [-Persist] 우하단 토스트 — 알림센터에 남기는 용도라 audio는 안 실음(위에서 이미 재생).
if ($Persist) {
    try {
        [Windows.UI.Notifications.ToastNotificationManager, Windows.UI.Notifications, ContentType = WindowsRuntime] | Out-Null
        [Windows.Data.Xml.Dom.XmlDocument, Windows.Data.Xml.Dom.XmlDocument, ContentType = WindowsRuntime] | Out-Null
        $APP_ID = '{1AC14E77-02E7-4E5D-B744-2EB1AE5198B7}\WindowsPowerShell\v1.0\powershell.exe'
        $escaped = [System.Security.SecurityElement]::Escape($Message)
        $xml = New-Object Windows.Data.Xml.Dom.XmlDocument
        $xml.LoadXml("<toast><visual><binding template=`"ToastGeneric`"><text>Claude Code</text><text>$escaped</text></binding></visual></toast>")
        $toast = [Windows.UI.Notifications.ToastNotification]::new($xml)
        [Windows.UI.Notifications.ToastNotificationManager]::CreateToastNotifier($APP_ID).Show($toast)
    } catch { }
}

# Telegram (옵션) — telegram.json 있으면 같이 전송, 없으면 무시.
# ⚠ 반드시 위 중앙 팝업 다음에 둘 것: Invoke-RestMethod가 동기 호출이라 네트워크 왕복
# (실측 2~3초) 동안 뒤 코드를 막는다 — 팝업보다 먼저 두면 팝업이 그만큼 늦게 뜬다(2026-07-22
# 실측 발견). 이 스크립트 자체가 호출부(toast.sh/sync-repos)에서 이미 비동기 실행되므로
# 텔레그램이 몇 초 늦게 끝나도 아무도 기다리지 않아 별도 백그라운드 처리 없이 순서만으로 충분.
$tgConfig = Join-Path $env:USERPROFILE '.claude\telegram.json'
if (Test-Path $tgConfig) {
    try {
        $tg = Get-Content $tgConfig -Raw | ConvertFrom-Json
        $pcName = $env:COMPUTERNAME
        $body = @{ chat_id = $tg.chat_id; text = "[$pcName] Claude Code: $Message" }
        Invoke-RestMethod -Method Post `
            -Uri "https://api.telegram.org/bot$($tg.bot_token)/sendMessage" `
            -Body $body -TimeoutSec 5 | Out-Null
    } catch { }
}
