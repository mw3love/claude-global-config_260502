param([string]$Message = 'Response complete')

# 활성 모니터(포커스 창이 있는 화면) 정중앙에 뜨는 알림 팝업.
#   - 기존 WinRT 우하단 토스트(toast.ps1)를 대체하지 않고 '함께' 뜬다.
#   - 포커스를 뺏지 않음(ShowWindow=SW_SHOWNOACTIVATE + SetWindowPos=SWP_NOACTIVATE)
#     → 사용자가 타이핑 중이어도 방해하지 않는다.
#   - 자동 2.5초 후 소멸, 클릭 시 즉시 닫힘.
# toast.ps1 의 Windows 경로에서 `& center-toast.ps1 -Message $Message` 로 호출된다.

try {
    Add-Type -AssemblyName System.Windows.Forms
    Add-Type -AssemblyName System.Drawing

    Add-Type -Namespace Native -Name Win -MemberDefinition @'
[System.Runtime.InteropServices.DllImport("user32.dll")]
public static extern System.IntPtr GetForegroundWindow();
[System.Runtime.InteropServices.DllImport("user32.dll")]
public static extern bool ShowWindow(System.IntPtr hWnd, int nCmdShow);
[System.Runtime.InteropServices.DllImport("user32.dll")]
public static extern bool SetWindowPos(System.IntPtr hWnd, System.IntPtr hWndInsertAfter, int X, int Y, int cx, int cy, uint uFlags);
'@

    # 활성 모니터 선택 (포커스 창 기준, 실패 시 주모니터로 폴백)
    $screen = [System.Windows.Forms.Screen]::PrimaryScreen
    try {
        $hwnd = [Native.Win]::GetForegroundWindow()
        if ($hwnd -ne [System.IntPtr]::Zero) {
            $screen = [System.Windows.Forms.Screen]::FromHandle($hwnd)
        }
    } catch {}

    $form = New-Object System.Windows.Forms.Form
    # 다크모드에서도 확 띄도록: 밝은 코랄 테두리 + 어두운 내부 + 강한 대비
    $accent = [System.Drawing.Color]::FromArgb(217, 119, 87)   # Claude 코랄 (테두리/제목)
    $dark   = [System.Drawing.Color]::FromArgb(28, 28, 32)     # 내부 배경

    $form.FormBorderStyle = 'None'
    $form.StartPosition   = 'Manual'
    $form.ShowInTaskbar   = $false
    $form.TopMost         = $true
    $form.BackColor       = $accent                            # 바깥 = 코랄 테두리 색
    $form.Padding         = New-Object System.Windows.Forms.Padding(4)  # 4px 테두리 두께
    $form.Opacity         = 0.97
    $form.Size            = New-Object System.Drawing.Size(520, 160)

    $b = $screen.Bounds
    $form.Location = New-Object System.Drawing.Point(
        ($b.X + [int](($b.Width  - $form.Width ) / 2)),
        ($b.Y + [int](($b.Height - $form.Height) / 2))
    )

    # 내부 어두운 패널 (form.Padding 만큼 코랄 테두리가 드러남)
    $panel = New-Object System.Windows.Forms.Panel
    $panel.Dock      = 'Fill'
    $panel.BackColor = $dark
    $form.Controls.Add($panel)

    $title = New-Object System.Windows.Forms.Label
    $title.Dock      = 'Top'
    $title.Height    = 52
    $title.TextAlign = 'MiddleCenter'
    $title.ForeColor = $accent
    $title.Font      = New-Object System.Drawing.Font('Segoe UI', 15, [System.Drawing.FontStyle]::Bold)
    $title.Text      = 'Claude Code'

    $msg = New-Object System.Windows.Forms.Label
    $msg.Dock      = 'Fill'
    $msg.TextAlign = 'MiddleCenter'
    $msg.ForeColor = [System.Drawing.Color]::White
    $msg.Font      = New-Object System.Drawing.Font('Segoe UI', 20, [System.Drawing.FontStyle]::Bold)
    $msg.Text      = $Message

    # Fill 먼저, Top 나중에 추가해야 제목이 위·본문이 아래로 배치됨
    $panel.Controls.Add($msg)
    $panel.Controls.Add($title)

    # 클릭 시 즉시 닫기 (어디를 눌러도)
    $onClick = { if (-not $form.IsDisposed) { $form.Close() } }
    $form.Add_MouseClick($onClick)
    $panel.Add_MouseClick($onClick)
    $title.Add_MouseClick($onClick)
    $msg.Add_MouseClick($onClick)

    # 핸들만 생성(창은 아직 안 보임) 후, 활성화 없이 표시 + 최상위 고정
    $h = $form.Handle
    $SW_SHOWNOACTIVATE = 4
    $HWND_TOPMOST      = [System.IntPtr](-1)
    $SWP_NOACTIVATE    = 0x0013   # NOSIZE(0x1)|NOMOVE(0x2)|NOACTIVATE(0x10)
    [Native.Win]::ShowWindow($h, $SW_SHOWNOACTIVATE) | Out-Null
    [Native.Win]::SetWindowPos($h, $HWND_TOPMOST, 0, 0, 0, 0, $SWP_NOACTIVATE) | Out-Null

    # 수동 펌프: 자동 2.5초 / 클릭 중 먼저 오는 쪽에서 종료
    # Visible 은 P/Invoke 표시라 WinForms 내부 플래그와 어긋남 → 시간+IsDisposed 로만 유지
    $sw = [System.Diagnostics.Stopwatch]::StartNew()
    while (-not $form.IsDisposed -and $sw.ElapsedMilliseconds -lt 2500) {
        [System.Windows.Forms.Application]::DoEvents()
        Start-Sleep -Milliseconds 25
    }
    if (-not $form.IsDisposed) { $form.Close() }
    $form.Dispose()
} catch {
    # 팝업 실패가 훅 전체를 깨뜨리지 않도록 조용히 무시
}
