<#
  KAIROS 게이트웨이로 클로드코드를 띄운다 (이 창에서만).
  전역 settings.json 을 건드리지 않으므로 구독 세션과 동시에 띄울 수 있다.

    .\kairos-claude.ps1                      # kairos / sonnet
    .\kairos-claude.ps1 -Account jbnu
    .\kairos-claude.ps1 -Model claude-opus-5
    .\kairos-claude.ps1 -p "질문"            # 나머지 인자는 claude 로 그대로 전달

  주의: 이 창의 모든 요청은 구독이 아니라 크레딧에서 차감된다.
#>
# param 에 특성([ValidateSet]·[Parameter])을 하나라도 달면 고급 함수가 되어
# 공통 파라미터가 생기고, claude 로 넘길 -p 가 -PipelineVariable 로 먼저
# 붙잡힌다(실측: ParameterArgumentValidationError). 그래서 특성을 쓰지 않고
# 나머지 인자는 자동 변수 $args 로 받는다. 계정 검증은 아래에서 직접 한다.
param(
  [string]$Account = 'kairos',
  [string]$Model = 'claude-sonnet-5'
)

$ErrorActionPreference = 'Stop'
[Console]::OutputEncoding = [Text.Encoding]::UTF8

if ($Account -notin @('kairos','jbnu')) {
  Write-Host "[중단] 알 수 없는 계정: $Account  (가능: kairos / jbnu)" -ForegroundColor Red
  exit 1
}

$gw = @{
  kairos = @{ base = 'https://factchat.mindlogic-kr-api.com/v1/gateway/claude'; key = 'kairos-gateway.key' }
  jbnu   = @{ base = 'https://factchat-cloud.mindlogic.ai/v1/gateway/claude';   key = 'jbnu-gateway.key'   }
}[$Account]

$keyFile = Join-Path $HOME ".claude\.secrets\$($gw.key)"
if (-not (Test-Path $keyFile)) {
  Write-Host "[중단] 키 파일 없음: $keyFile" -ForegroundColor Red
  exit 1
}
# 키는 변수로만 다룬다 - 화면에도 로그에도 찍지 않는다.
$key = (Get-Content -Raw $keyFile).Trim()
if ([string]::IsNullOrWhiteSpace($key)) {
  Write-Host "[중단] 키 파일이 비어 있음: $keyFile" -ForegroundColor Red
  exit 1
}

$host.UI.RawUI.WindowTitle = "KAIROS gateway - $Account / $Model"
Write-Host ("=" * 62) -ForegroundColor DarkYellow
Write-Host " KAIROS 게이트웨이 세션  (계정 $Account / 모델 $Model)" -ForegroundColor Yellow
Write-Host " 이 창의 요청은 구독이 아니라 크레딧에서 차감됩니다." -ForegroundColor Yellow
$balance = Join-Path $HOME '.claude\scripts\kairos-balance.py'
if (Test-Path $balance) { Write-Host (" " + (& python $balance $Account 2>$null)) -ForegroundColor Yellow }
Write-Host " 커넥터 / Remote Control / 음성입력은 이 창에서 비활성입니다." -ForegroundColor DarkGray
Write-Host ("=" * 62) -ForegroundColor DarkYellow

$env:ANTHROPIC_BASE_URL = $gw.base
$env:ANTHROPIC_AUTH_TOKEN = $key
$env:CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC = '1'

if ($args.Count) { & claude --model $Model @args } else { & claude --model $Model }
exit $LASTEXITCODE
