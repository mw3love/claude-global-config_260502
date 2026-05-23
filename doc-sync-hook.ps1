# PostToolUse hook: Bash 도구로 `git push`가 성공하면 doc-sync 스킬 호출을 지시한다.
# - PostToolUse는 성공한 tool 호출에만 발화하므로 success 체크 불필요
# - tool result 필드 키 이름이 공식 문서에 미명시이므로 raw stdin 텍스트에서 push 결과 패턴을 추출
# - 푸쉬된 범위에 비-문서 코드 변경이 있을 때만 스킬 호출 지시 (사용자 요구)

$ErrorActionPreference = 'Stop'

# UTF-8 강제 (Windows 한글 환경에서 EUC-KR로 동작하는 것 방지)
[Console]::OutputEncoding = [System.Text.UTF8Encoding]::new($false)
[Console]::InputEncoding  = [System.Text.UTF8Encoding]::new($false)
$OutputEncoding           = [System.Text.UTF8Encoding]::new($false)

function Exit-Silent { exit 0 }

# 비 ASCII 문자를 \uXXXX로 escape — PS 5.1 콘솔 인코딩 변환 우회
function ConvertTo-AsciiSafeJson($obj) {
    $j = $obj | ConvertTo-Json -Depth 10 -Compress
    $sb = New-Object System.Text.StringBuilder
    foreach ($c in $j.ToCharArray()) {
        $code = [int]$c
        if ($code -lt 0x20 -or $code -gt 0x7E) {
            [void]$sb.AppendFormat('\u{0:x4}', $code)
        } else {
            [void]$sb.Append($c)
        }
    }
    return $sb.ToString()
}

try {
    $raw = [Console]::In.ReadToEnd()
    if ([string]::IsNullOrWhiteSpace($raw)) { Exit-Silent }

    # ConvertFrom-Json의 -Depth는 PS 5.1에서 미지원이라 옵션 생략 (기본 깊이로 충분)
    $payload = $raw | ConvertFrom-Json

    if ($payload.tool_name -ne 'Bash') { Exit-Silent }

    $cmd = [string]$payload.tool_input.command
    if ([string]::IsNullOrWhiteSpace($cmd)) { Exit-Silent }

    # git push 토큰 매칭. `git pusher`, `git push-mirror`, `echo "git push"` 등은 제외하려 노력하되
    # 따옴표 안의 문자열까지 완벽 분리는 어려움 (수용 — false positive면 후속 검증에서 걸러짐).
    $pushRegex = '\bgit(\s+--?[^\s=]+(=\S+)?)*\s+push(?=\s|$|[;|&\)])'
    if ($cmd -notmatch $pushRegex) { Exit-Silent }
    if ($cmd -match '\bgit\s+push\b.*(--help|\s-h(\s|$))') { Exit-Silent }
    # 자기-트리거 방지: hook 스크립트 자신을 호출하는 명령은 스킵
    if ($cmd -match 'doc-sync-hook\.ps1') { Exit-Silent }

    # 푸쉬 결과 패턴 추출. raw 텍스트는 JSON 이스케이프된 \n 또는 실제 개행을 포함할 수 있음.
    $newBranch = $false
    $forced    = $false
    $ranges    = New-Object System.Collections.Generic.List[string]

    $lines = $raw -split '\\r\\n|\\n|\r?\n'
    foreach ($ln in $lines) {
        if ($ln -match '\s([0-9a-f]{7,40}\.\.[0-9a-f]{7,40})\s+\S+\s+->\s+(\S+)') {
            [void]$ranges.Add($matches[1])
        }
        elseif ($ln -match '\*\s+\[new branch\]\s+\S+\s+->\s+(\S+)') {
            $newBranch = $true
            [void]$ranges.Add("__NEWBRANCH__:$($matches[1])")
        }
        elseif ($ln -match '\+\s+([0-9a-f]{7,40}\.\.\.[0-9a-f]{7,40})\s+\S+\s+->\s+(\S+)') {
            $forced = $true
            [void]$ranges.Add("__FORCED__:$($matches[1])")
        }
    }

    if ($ranges.Count -eq 0) { Exit-Silent }  # up-to-date 등 변경 없음

    $cwd = [string]$payload.cwd
    if ([string]::IsNullOrWhiteSpace($cwd) -or -not (Test-Path $cwd)) {
        $cwd = (Get-Location).Path
    }

    # 푸쉬된 범위의 변경 파일 수집. 재진입 가드로 hook 내부 git 호출은 재발화 없음 (공식).
    $changedFiles = New-Object System.Collections.Generic.List[string]
    foreach ($r in $ranges) {
        $diffRange = $null
        if ($r -like '__NEWBRANCH__:*') {
            # 새 브랜치 — base가 불명. 최근 50개 커밋의 파일을 후보로.
            $out = & git -C $cwd log -50 --name-only --pretty=format: HEAD 2>$null
            if ($LASTEXITCODE -eq 0 -and $out) { $out | ForEach-Object { if ($_) { [void]$changedFiles.Add($_) } } }
            continue
        }
        elseif ($r -like '__FORCED__:*') {
            $diffRange = ($r -replace '^__FORCED__:', '') -replace '\.\.\.', '..'
        }
        else {
            $diffRange = $r
        }
        $out = & git -C $cwd diff --name-only $diffRange 2>$null
        if ($LASTEXITCODE -eq 0 -and $out) { $out | ForEach-Object { if ($_) { [void]$changedFiles.Add($_) } } }
    }

    $unique = $changedFiles | Where-Object { $_ -and $_.Trim() } | Select-Object -Unique
    if ($unique.Count -eq 0) { Exit-Silent }

    # 비-문서 코드 변경이 1개라도 있어야 발화 (사용자 요구: 코드 변경 있을 때만)
    $nonDoc = $unique | Where-Object {
        $_ -notmatch '\.(md|markdown|txt|rst)$' -and
        $_ -notmatch '(^|/)LICENSE$' -and
        $_ -notmatch '(^|/)CHANGELOG(\.md)?$'  # CHANGELOG는 문서로 분류 — 이걸 트리거로 잡지 않음
    }
    if ($nonDoc.Count -eq 0) { Exit-Silent }

    $rangeSummary = ($ranges | ForEach-Object {
        if ($_ -like '__NEWBRANCH__:*') { "[new branch] $($_ -replace '^__NEWBRANCH__:', '')" }
        elseif ($_ -like '__FORCED__:*') { "[forced] $($_ -replace '^__FORCED__:', '')" }
        else { $_ }
    }) -join ', '
    $fileSample = ($unique | Select-Object -First 30) -join "`n  - "

    $context = @"
[doc-sync hook] ``git push``가 방금 성공했습니다. doc-sync 스킬을 즉시 호출해 푸쉬된 변경사항이 핵심 문서(CLAUDE.md, 계획/설계/스펙 문서 등)에 반영되었는지 검토하세요.

푸쉬 정보
- 작업 폴더: $cwd
- 푸쉬 범위: $rangeSummary
- 새 브랜치: $newBranch / force: $forced
- 변경 파일($($unique.Count)개):
  - $fileSample

호출 방법: Skill 도구로 'doc-sync' 스킬을 인수 없이 호출하세요.
"@

    $output = ConvertTo-AsciiSafeJson @{
        suppressOutput     = $true
        hookSpecificOutput = @{
            hookEventName     = 'PostToolUse'
            additionalContext = $context
        }
    }

    [Console]::Out.WriteLine($output)
    exit 0
}
catch {
    [Console]::Error.WriteLine("[doc-sync-hook] error: $($_.Exception.Message)")
    exit 0
}
