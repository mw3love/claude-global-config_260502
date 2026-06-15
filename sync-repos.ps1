#requires -Version 7
<#
.SYNOPSIS
  여러 PC에서 쓰는 git 프로젝트들을 한 번에 git pull(+빌드)한다.

.DESCRIPTION
  ~/.claude/repos.json 명단을 읽어 각 repo를 fast-forward pull 한다.
  경로는 홈 폴더(~) 기준 상대경로로 저장되므로 PC마다 사용자명이 달라도 동작한다.
  pull로 실제 변경이 생긴 repo만 build 명령을 실행한다.

.PARAMETER BuildAll
  변경이 없어도 build가 정의된 repo는 빌드한다.

.PARAMETER NoBuild
  빌드를 전부 건너뛰고 pull만 한다.

.EXAMPLE
  pwsh -File "$HOME\.claude\sync-repos.ps1"
  pwsh -File "$HOME\.claude\sync-repos.ps1" -BuildAll
#>
[CmdletBinding()]
param(
  [switch]$BuildAll,
  [switch]$NoBuild
)

$ErrorActionPreference = 'Stop'

$userHome     = $env:USERPROFILE
$manifestPath = Join-Path $userHome '.claude\repos.json'

if (-not (Test-Path $manifestPath)) {
  Write-Host "[X] 명단 파일 없음: $manifestPath" -ForegroundColor Red
  exit 1
}

try {
  $repos = Get-Content $manifestPath -Raw | ConvertFrom-Json
} catch {
  Write-Host "[X] repos.json 파싱 실패: $_" -ForegroundColor Red
  exit 1
}

Write-Host ""
Write-Host "=== sync-repos === ($($repos.Count)개 대상)" -ForegroundColor White
Write-Host ""

$results = @()

foreach ($r in $repos) {
  $rel  = $r.path
  $full = Join-Path $userHome $rel
  $name = if ($r.desc) { $r.desc } else { $rel }

  $entry = [pscustomobject]@{ name = $name; status = ''; detail = '' }

  # 이 PC에 클론돼 있나?
  if (-not (Test-Path (Join-Path $full '.git'))) {
    $entry.status = 'skip'
    $entry.detail = '이 PC에 없음(미클론)'
    $results += $entry
    Write-Host ("  [-] {0,-22} {1}" -f $name, $entry.detail) -ForegroundColor DarkGray
    continue
  }

  $dirty  = git -C $full status --porcelain
  $before = (git -C $full rev-parse HEAD 2>$null).Trim()

  # fast-forward 전용 pull — 디버전(분기)되면 자동 머지하지 않고 에러로 보고
  $pullOut = git -C $full pull --ff-only 2>&1
  if ($LASTEXITCODE -ne 0) {
    $entry.status = 'error'
    $entry.detail = "pull 실패 — " + (($pullOut | Select-Object -Last 1) -replace '\s+', ' ')
    $results += $entry
    Write-Host ("  [!] {0,-22} {1}" -f $name, $entry.detail) -ForegroundColor Red
    continue
  }

  $after   = (git -C $full rev-parse HEAD 2>$null).Trim()
  $changed = $before -ne $after

  $shouldBuild = $r.build -and -not $NoBuild -and ($changed -or $BuildAll)

  if (-not $changed -and -not $shouldBuild) {
    $entry.status = 'nochange'
    $entry.detail = if ($dirty) { '변경없음 (로컬 미커밋 있음)' } else { '변경없음' }
    $results += $entry
    Write-Host ("  [=] {0,-22} {1}" -f $name, $entry.detail) -ForegroundColor DarkGray
    continue
  }

  if ($shouldBuild) {
    Write-Host ("  [~] {0,-22} 빌드 중: {1}" -f $name, $r.build) -ForegroundColor Cyan
    Push-Location $full
    try {
      Invoke-Expression $r.build
      if ($LASTEXITCODE -ne 0) {
        $entry.status = 'builderror'
        $entry.detail = '업데이트됨, 빌드 실패'
      } else {
        $entry.status = 'built'
        $entry.detail = if ($changed) { '업데이트 + 빌드 완료' } else { '빌드 완료(강제)' }
      }
    } catch {
      $entry.status = 'builderror'
      $entry.detail = "업데이트됨, 빌드 예외: $_"
    } finally {
      Pop-Location
    }
  } else {
    $entry.status = 'updated'
    $entry.detail = '업데이트됨(빌드 없음)'
  }

  $results += $entry
  $color = if ($entry.status -eq 'builderror') { 'Red' } else { 'Green' }
  Write-Host ("  [v] {0,-22} {1}" -f $name, $entry.detail) -ForegroundColor $color
}

# ---- 요약 ----
Write-Host ""
$ok    = ($results | Where-Object { $_.status -in @('built','updated') }).Count
$noch  = ($results | Where-Object { $_.status -eq 'nochange' }).Count
$skip  = ($results | Where-Object { $_.status -eq 'skip' }).Count
$bad   = ($results | Where-Object { $_.status -in @('error','builderror') })

Write-Host ("요약: 업데이트 {0} / 변경없음 {1} / 미클론 {2} / 문제 {3}" -f $ok, $noch, $skip, $bad.Count) -ForegroundColor White

if ($bad.Count -gt 0) {
  Write-Host ""
  Write-Host "확인 필요:" -ForegroundColor Yellow
  foreach ($b in $bad) {
    Write-Host ("  - {0}: {1}" -f $b.name, $b.detail) -ForegroundColor Yellow
  }
  exit 2
}

exit 0
