param([string]$Message = 'Response complete')

[Windows.UI.Notifications.ToastNotificationManager, Windows.UI.Notifications, ContentType = WindowsRuntime] | Out-Null
[Windows.Data.Xml.Dom.XmlDocument, Windows.Data.Xml.Dom.XmlDocument, ContentType = WindowsRuntime] | Out-Null

$APP_ID = '{1AC14E77-02E7-4E5D-B744-2EB1AE5198B7}\WindowsPowerShell\v1.0\powershell.exe'

$escaped = [System.Security.SecurityElement]::Escape($Message)
$xml = New-Object Windows.Data.Xml.Dom.XmlDocument
$xml.LoadXml("<toast><audio src=`"ms-winsoundevent:Notification.Default`"/><visual><binding template=`"ToastGeneric`"><text>Claude Code</text><text>$escaped</text></binding></visual></toast>")
$toast = [Windows.UI.Notifications.ToastNotification]::new($xml)
[Windows.UI.Notifications.ToastNotificationManager]::CreateToastNotifier($APP_ID).Show($toast)

# Telegram (옵션) — telegram.json 있으면 같이 전송, 없으면 무시
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
