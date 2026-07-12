$raw = [Console]::In.ReadToEnd()
try {
    $data = $raw | ConvertFrom-Json
} catch {
    [Console]::Write("Claude")
    exit
}

$ESC    = [char]27
$Reset  = "${ESC}[0m"
$Green  = "${ESC}[32m"
$Orange = "${ESC}[38;5;208m"
$Red    = "${ESC}[31m"
$Cyan   = "${ESC}[36m"

function Get-Color($pct) {
    if ($pct -lt 50) { return $Green }
    elseif ($pct -le 80) { return $Orange }
    else { return $Red }
}

function Format-Remaining($resetsAt) {
    if (-not $resetsAt) { return "" }
    $now = [DateTimeOffset]::UtcNow.ToUnixTimeSeconds()
    $sec = $resetsAt - $now
    if ($sec -le 0) { return "" }
    $h = [math]::Floor($sec / 3600)
    $m = [math]::Floor(($sec % 3600) / 60)
    if ($h -ge 24) {
        $d = [math]::Floor($h / 24)
        $rh = $h % 24
        return "(${d}d ${rh}h)"
    } elseif ($h -gt 0) {
        return "(${h}h ${m}m)"
    } else {
        return "(${m}m)"
    }
}

function Format-CtxSize($tokens) {
    if (-not $tokens) { return "" }
    if ($tokens -ge 1000000) {
        $v = [math]::Round($tokens / 1000000, 1)
        $s = if ($v -eq [math]::Floor($v)) { "$([int]$v)M" } else { "${v}M" }
        return " ($s)"
    } elseif ($tokens -ge 1000) {
        $v = [math]::Round($tokens / 1000)
        return " (${v}K)"
    }
    return ""
}

$Sep = " | "

# Current folder name (leaf only)
$cwd = if ($data.workspace.current_dir) { $data.workspace.current_dir } else { $data.cwd }
$folderPart = ""
if ($cwd) {
    $leaf = Split-Path $cwd -Leaf
    if ($leaf) { $folderPart = "${Cyan}${leaf}${Reset}" }
}

# Model + context window size
$model = if ($data.model.display_name) { $data.model.display_name }
         elseif ($data.model.id) { $data.model.id }
         else { "Claude" }
$short = $model -replace '^Claude\s*', '' -replace '\s', ''
if (-not $short) { $short = "Claude" }
$ctxSize = Format-CtxSize $data.context_window.context_window_size

# settings.json 의 "model" 필드(opusplan 등 별칭) — stdin JSON엔 해석된 모델만 오므로 별도 확인
$tag = ""
try {
    $settingsPath = Join-Path $env:USERPROFILE ".claude\settings.json"
    $modelSetting = (Get-Content $settingsPath -Raw | ConvertFrom-Json).model
    if ($modelSetting -like "opusplan*") { $tag = " [opusplan]" }
} catch {}

$modelPart = "${short}${tag}${ctxSize}"

# Context usage
$used = $data.context_window.used_percentage
$ctxPart = ""
if ($null -ne $used) {
    $pct = [math]::Round($used)
    $col = Get-Color $pct
    $ctxPart = "C: ${col}${pct}%${Reset}"
}

# 5-hour rate limit
$fivePct = $data.rate_limits.five_hour.used_percentage
$fivePart = ""
if ($null -ne $fivePct) {
    $f = [math]::Round($fivePct)
    $col = Get-Color $f
    $rem = Format-Remaining $data.rate_limits.five_hour.resets_at
    $fivePart = "5h: ${col}${f}%${Reset} $rem".TrimEnd()
}

# 7-day rate limit
$weekPct = $data.rate_limits.seven_day.used_percentage
$weekPart = ""
if ($null -ne $weekPct) {
    $w = [math]::Round($weekPct)
    $col = Get-Color $w
    $rem = Format-Remaining $data.rate_limits.seven_day.resets_at
    $weekPart = "7d: ${col}${w}%${Reset} $rem".TrimEnd()
}

$parts = @()
if ($folderPart) { $parts += $folderPart }
$parts += $modelPart
if ($ctxPart)  { $parts += $ctxPart }
if ($fivePart) { $parts += $fivePart }
if ($weekPart) { $parts += $weekPart }

[Console]::Write($parts -join $Sep)
