param(
  [string]$HostName = "127.0.0.1",
  [int]$BackendPort = 8000,
  [int]$FrontendPort = 3000,
  [switch]$StopExisting
)

$ErrorActionPreference = "Stop"

$repoRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
$frontendRoot = Join-Path $repoRoot "frontend"
$python = Join-Path $repoRoot ".venv\Scripts\python.exe"
$frontendPackageJson = Join-Path $frontendRoot "package.json"
$nextCli = Join-Path $frontendRoot "node_modules\next\dist\bin\next"
$backendUrl = "http://${HostName}:${BackendPort}"
$frontendUrl = "http://${HostName}:${FrontendPort}"
$logRoot = Join-Path $repoRoot "output\local_site"
$timestamp = Get-Date -Format "yyyyMMddTHHmmss"
$backendLog = Join-Path $logRoot "fastapi-${BackendPort}-${timestamp}.log"
$frontendLog = Join-Path $logRoot "next-${FrontendPort}-${timestamp}.log"

function Stop-PortProcess {
  param([int]$Port)
  $connections = Get-NetTCPConnection -LocalPort $Port -ErrorAction SilentlyContinue
  foreach ($connection in $connections) {
    if ($connection.OwningProcess) {
      Stop-Process -Id $connection.OwningProcess -Force -ErrorAction SilentlyContinue
    }
  }
}

function Wait-HttpOk {
  param(
    [string]$Url,
    [int]$Seconds = 45
  )
  for ($i = 0; $i -lt $Seconds; $i++) {
    try {
      $response = Invoke-WebRequest -Uri $Url -UseBasicParsing -TimeoutSec 2
      if ($response.StatusCode -ge 200 -and $response.StatusCode -lt 500) {
        return $true
      }
    } catch {
      Start-Sleep -Seconds 1
    }
  }
  return $false
}

if (-not (Test-Path $python)) {
  throw "Project virtual environment was not found at $python. Create it and install requirements before starting the local site."
}

if (-not (Test-Path $frontendRoot)) {
  throw "Frontend directory was not found at $frontendRoot."
}

if (-not (Get-Command "npm.cmd" -ErrorAction SilentlyContinue)) {
  throw "npm.cmd was not found on PATH. Install Node.js/npm before starting the local site."
}

if (-not (Test-Path $frontendPackageJson)) {
  throw "Frontend package.json was not found at $frontendPackageJson."
}

if (-not (Test-Path $nextCli)) {
  throw "Next CLI was not found at $nextCli. Run 'cd frontend; npm install' before starting the local site."
}

New-Item -ItemType Directory -Force -Path $logRoot | Out-Null

if ($StopExisting) {
  Stop-PortProcess -Port $BackendPort
  Stop-PortProcess -Port $FrontendPort
  Start-Sleep -Seconds 1
}

$backendCmd = "cd /d `"$repoRoot`" && `"$python`" -m uvicorn src.api.app:app --host $HostName --port $BackendPort > `"$backendLog`" 2>&1"
$frontendCmd = "cd /d `"$frontendRoot`" && set `"PMRI_FASTAPI_BASE_URL=$backendUrl`" && set `"FASTAPI_BASE_URL=$backendUrl`" && npm.cmd run dev:next -- --hostname $HostName --port $FrontendPort > `"$frontendLog`" 2>&1"

Start-Process -FilePath "cmd.exe" -ArgumentList "/c", $backendCmd -WindowStyle Hidden
Start-Sleep -Seconds 2
Start-Process -FilePath "cmd.exe" -ArgumentList "/c", $frontendCmd -WindowStyle Hidden

$backendReady = Wait-HttpOk -Url "$backendUrl/api/v1/health"
$frontendReady = Wait-HttpOk -Url $frontendUrl

Write-Output "backend_ready=$backendReady"
Write-Output "frontend_ready=$frontendReady"
Write-Output "backend_url=$backendUrl"
Write-Output "frontend_url=$frontendUrl"
Write-Output "backend_log=$backendLog"
Write-Output "frontend_log=$frontendLog"

if (-not $backendReady -or -not $frontendReady) {
  throw "Local site did not become ready. Inspect the log paths printed above."
}
