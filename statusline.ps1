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

function Get-GitPart($cwd) {
    # fetch 없이 @{upstream} 캐시로만 비교 + FETCH_HEAD mtime 으로 그 캐시가 언제 기준인지 라벨링
    # (참고: github.com/ykdojo/claude-code-tips Tip 0 context-bar.sh)
    if (-not $cwd -or -not (Test-Path $cwd)) { return $null }
    try {
        $branch = (& git -C $cwd branch --show-current 2>$null)
        if (-not $branch) { return $null }

        $statusOut = & git -C $cwd --no-optional-locks status --porcelain -uall 2>$null
        $lines = @($statusOut | Where-Object { $_ -and $_.Trim() -ne "" })
        $fileCount = $lines.Count

        $upstream = (& git -C $cwd rev-parse --abbrev-ref '@{upstream}' 2>$null)
        $ahead = 0; $behind = 0; $fetchAgo = ""
        if ($upstream) {
            $counts = (& git -C $cwd rev-list --left-right --count 'HEAD...@{upstream}' 2>$null)
            if ($counts) {
                $pieces = $counts -split '\s+' | Where-Object { $_ -ne "" }
                if ($pieces.Count -ge 2) { $ahead = [int]$pieces[0]; $behind = [int]$pieces[1] }
            }
            $fetchHead = Join-Path $cwd ".git\FETCH_HEAD"
            if (Test-Path $fetchHead) {
                $fetchTime = (Get-Item $fetchHead).LastWriteTimeUtc
                $diff = [int]([DateTimeOffset]::UtcNow - [DateTimeOffset]$fetchTime).TotalSeconds
                if ($diff -lt 60) { $fetchAgo = "<1m" }
                elseif ($diff -lt 3600) { $fetchAgo = "$([math]::Floor($diff/60))m" }
                elseif ($diff -lt 86400) { $fetchAgo = "$([math]::Floor($diff/3600))h" }
                else { $fetchAgo = "$([math]::Floor($diff/86400))d" }
            }
            if ($ahead -eq 0 -and $behind -eq 0) { $sync = "synced" }
            elseif ($ahead -gt 0 -and $behind -eq 0) { $sync = "$ahead ahead" }
            elseif ($behind -gt 0 -and $ahead -eq 0) { $sync = "$behind behind" }
            else { $sync = "$ahead ahead, $behind behind" }
            if ($fetchAgo) { $sync = "$sync (${fetchAgo} ago)" }
        } else {
            $sync = "no upstream"
        }

        if ($fileCount -eq 0) {
            $detail = "clean, $sync"
        } elseif ($fileCount -eq 1) {
            $fname = $lines[0].Substring([Math]::Min(3, $lines[0].Length)).Trim()
            $detail = "$fname uncommitted, $sync"
        } else {
            $detail = "$fileCount files uncommitted, $sync"
        }

        if ($behind -gt 0) { $col = $Red }
        elseif ($fileCount -gt 0 -or $ahead -gt 0) { $col = $Orange }
        else { $col = $Green }

        return "${col}${branch}${Reset} (${detail})"
    } catch {
        return $null
    }
}

$Sep = " | "

# Current folder name (leaf only)
$cwd = if ($data.workspace.current_dir) { $data.workspace.current_dir } else { $data.cwd }
$folderPart = ""
if ($cwd) {
    $leaf = Split-Path $cwd -Leaf
    if ($leaf) { $folderPart = "${Cyan}${leaf}${Reset}" }
}

# git 브랜치 + 미커밋 + 동기화 상태
$gitPart = Get-GitPart $cwd

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

$line1 = @()
if ($folderPart) { $line1 += $folderPart }
if ($gitPart)    { $line1 += $gitPart }

$line2 = @()
$line2 += $modelPart
if ($ctxPart)  { $line2 += $ctxPart }
if ($fivePart) { $line2 += $fivePart }
if ($weekPart) { $line2 += $weekPart }

[Console]::Write(($line1 -join $Sep) + "`n" + ($line2 -join $Sep))
