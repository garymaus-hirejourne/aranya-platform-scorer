Param(
  [int]$Port = 8080,
  [string]$PythonScript = "-m uvicorn src.app:app --host 0.0.0.0 --port 8080",
  [int]$NgrokApiPort = 4040
)

$ErrorActionPreference = "Stop"

function Write-Log {
  param([string]$Message)
  $ts = (Get-Date).ToString("yyyy-MM-dd HH:mm:ss")
  $line = "[$ts] $Message"
  Write-Host $line
  try {
    if ($script:LauncherLog -and (Test-Path $script:LauncherLog)) {
      Add-Content -Path $script:LauncherLog -Value $line
    }
  } catch {
  }
}

function Get-NgrokPublicUrl {
  param([int]$ApiPort)

  $uri = "http://127.0.0.1:$ApiPort/api/tunnels"
  try {
    $resp = Invoke-RestMethod -Uri $uri -Method GET -TimeoutSec 2
  } catch {
    return $null
  }

  if (-not $resp.tunnels) { return $null }

  $httpsTunnel = $resp.tunnels | Where-Object { $_.proto -eq "https" } | Select-Object -First 1
  if ($httpsTunnel -and $httpsTunnel.public_url) { return $httpsTunnel.public_url }

  $anyTunnel = $resp.tunnels | Select-Object -First 1
  if ($anyTunnel -and $anyTunnel.public_url) { return $anyTunnel.public_url }

  return $null
}

function Get-NgrokTunnelUrls {
  param([int]$ApiPort)

  $uri = "http://127.0.0.1:$ApiPort/api/tunnels"
  try {
    $resp = Invoke-RestMethod -Uri $uri -Method GET -TimeoutSec 2
  } catch {
    return @{ https = $null; http = $null }
  }

  $httpsTunnel = $null
  $httpTunnel = $null
  if ($resp.tunnels) {
    $httpsTunnel = $resp.tunnels | Where-Object { $_.proto -eq "https" } | Select-Object -First 1
    $httpTunnel = $resp.tunnels | Where-Object { $_.proto -eq "http" } | Select-Object -First 1
  }

  $httpsUrl = $null
  $httpUrl = $null
  if ($httpsTunnel -and $httpsTunnel.public_url) { $httpsUrl = $httpsTunnel.public_url }
  if ($httpTunnel -and $httpTunnel.public_url) { $httpUrl = $httpTunnel.public_url }

  # Some ngrok setups only report https. Best-effort derive http for browser testing.
  if (-not $httpUrl -and $httpsUrl -and $httpsUrl.StartsWith("https://")) {
    $httpUrl = "http://" + $httpsUrl.Substring(8)
  }

  return @{
    https = $httpsUrl
    http  = $httpUrl
  }
}

function Assert-CommandExists {
  param([string]$Name)
  if (-not (Get-Command $Name -ErrorAction SilentlyContinue)) {
    throw "Required command not found on PATH: $Name"
  }
}

function Wait-HttpOk {
  param(
    [string]$Url,
    [int]$Retries = 60,
    [int]$DelayMs = 500
  )
  for ($i = 0; $i -lt $Retries; $i++) {
    try {
      # Use Invoke-RestMethod to avoid HTML parsing / security prompts.
      $null = Invoke-RestMethod -Uri $Url -Method GET -TimeoutSec 2
      return $true
    } catch {
    }
    Start-Sleep -Milliseconds $DelayMs
  }
  return $false
}

$here = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $here

$logsDir = Join-Path $here "logs"
New-Item -ItemType Directory -Path $logsDir -Force | Out-Null
$launcherLog = Join-Path $logsDir ("launcher_{0}.log" -f (Get-Date).ToString("yyyyMMdd_HHmmss"))
$script:LauncherLog = $launcherLog
"launcher start" | Out-File -FilePath $launcherLog -Encoding utf8

try {
  Write-Log "Starting HireJourne control panel (local)"
  Write-Log "logs directory: $logsDir"
  Write-Log "launcher log: $launcherLog"

  Assert-CommandExists -Name "python"
  Assert-CommandExists -Name "ngrok"

  try {
    $py = (Get-Command python -ErrorAction SilentlyContinue)
    if ($py) { Write-Log "python: $($py.Source)" }
  } catch {
  }
  try {
    $ng = (Get-Command ngrok -ErrorAction SilentlyContinue)
    if ($ng) { Write-Log "ngrok: $($ng.Source)" }
  } catch {
  }

# Start ngrok first so we can inject the tunnel URL into the server env.
Write-Log "Launching ngrok: ngrok http $Port"
$ngrokProc = Start-Process -FilePath "ngrok" -ArgumentList @("http", "$Port") -WorkingDirectory $here -PassThru -WindowStyle Minimized -NoNewWindow:$false
try {
  Write-Log "ngrok process started (pid=$($ngrokProc.Id))"
} catch {
}

# Wait for ngrok tunnel to appear
$publicUrl = $null
$publicHttpUrl = $null
for ($i = 0; $i -lt 30; $i++) {
  $urls = Get-NgrokTunnelUrls -ApiPort $NgrokApiPort
  $publicUrl = $urls.https
  $publicHttpUrl = $urls.http
  if ($publicUrl -or $publicHttpUrl) { break }
  Start-Sleep -Milliseconds 500
}

if (-not $publicUrl -and -not $publicHttpUrl) {
  Write-Log "WARNING: Could not read ngrok public URL from local API. Visit http://127.0.0.1:$NgrokApiPort to debug."
} else {
  if ($publicUrl) { Write-Log "ngrok public URL (https): $publicUrl" }
  if ($publicHttpUrl) { Write-Log "ngrok public URL (http): $publicHttpUrl" }
  Write-Log "NOTE: For callback-based flows, set PUBLIC_BASE_URL / WEBHOOK_BASE_URL to this URL in your cloud config later."
}

# Start the local server with env vars set for this session.
$webhookBase = $publicUrl
if (-not $webhookBase) {
  # Fallback if https tunnel isn't present yet.
  $webhookBase = $publicHttpUrl
}
Write-Log "Launching server: python $PythonScript (port $Port)"
if ($webhookBase) {
  Write-Log "Injecting env: WEBHOOK_BASE_URL=$webhookBase"
  Write-Log "Injecting env: PUBLIC_BASE_URL=$webhookBase"
}

# Use cmd.exe chaining for compatibility (Start-Process -Environment is not available in Windows PowerShell 5).
$serverLog = Join-Path $logsDir ("server_{0}.log" -f (Get-Date).ToString("yyyyMMdd_HHmmss"))
$serverErrLog = Join-Path $logsDir ("server_{0}.err.log" -f (Get-Date).ToString("yyyyMMdd_HHmmss"))

# Set per-run environment variables (child inherits these). We'll restore afterwards.
$prev = @{
  PORT = $env:PORT
  WEBHOOK_BASE_URL = $env:WEBHOOK_BASE_URL
  PUBLIC_BASE_URL = $env:PUBLIC_BASE_URL
  NGROK_URL = $env:NGROK_URL
  PYTHONUNBUFFERED = $env:PYTHONUNBUFFERED
  LOG_LEVEL = $env:LOG_LEVEL
}

$env:PORT = "$Port"
if ($webhookBase) {
  $env:WEBHOOK_BASE_URL = $webhookBase
  $env:PUBLIC_BASE_URL = $webhookBase
  $env:NGROK_URL = $webhookBase
}
$env:PYTHONUNBUFFERED = "1"
$env:LOG_LEVEL = "INFO"

$serverProc = Start-Process `
  -FilePath "python" `
  -ArgumentList @($PythonScript) `
  -WorkingDirectory $here `
  -PassThru `
  -WindowStyle Normal `
  -RedirectStandardOutput $serverLog `
  -RedirectStandardError $serverErrLog

# Restore parent env (best-effort)
foreach ($k in $prev.Keys) {
  if ($null -eq $prev[$k]) {
    Remove-Item "env:$k" -ErrorAction SilentlyContinue
  } else {
    Set-Item -Path "env:$k" -Value $prev[$k] -ErrorAction SilentlyContinue
  }
}
try {
  Write-Log "server process started (pid=$($serverProc.Id))"
} catch {
}
Write-Log "server log: $serverLog"
Write-Log "server err log: $serverErrLog"

Start-Sleep -Seconds 1

$healthUrl = "http://127.0.0.1:$Port/health"
Write-Log "Waiting for server readiness: $healthUrl"
$ready = Wait-HttpOk -Url $healthUrl -Retries 60 -DelayMs 500
if ($ready) {
  Write-Log "Server ready: $healthUrl"
} else {
  Write-Log "WARNING: Server did not become ready within timeout. Check the server window for errors."
  Write-Log "Opening server log: $serverLog"
  try {
    Start-Process $serverLog | Out-Null
  } catch {
  }
}

# Open local dashboard (if route exists)
try {
  $dash = "http://127.0.0.1:$Port/"
  if ($ready) {
    Write-Log "Opening: $dash"
    Start-Process $dash | Out-Null
  } else {
    Write-Log "Skipping dashboard open (server not ready): $dash"
  }
} catch {
}

if ($ready -and ($publicHttpUrl -or $publicUrl)) {
  $shownUrl = $publicHttpUrl
  if (-not $shownUrl) { $shownUrl = $publicUrl }
  Write-Log "ngrok URL (manual open if needed): $shownUrl"
}

Write-Log "Done. Close the server/ngrok windows to stop."

} catch {
  Write-Log "FATAL: launcher failed"
  try {
    Write-Log ("error: " + $_.Exception.Message)
  } catch {
  }
  try {
    Add-Content -Path $launcherLog -Value ($_.ScriptStackTrace | Out-String)
  } catch {
  }
  throw
}
