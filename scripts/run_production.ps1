# Production supervisor for the AI Command Center API.
#
# - Reads JWT_SECRET from a local, ACL-restricted file (never
#   hardcoded, never committed).
# - Sets APP_ENV=production.
# - Restarts uvicorn automatically if it exits for any reason
#   (crash recovery), with a short backoff so a persistent failure
#   doesn't spin the CPU.
# - Leaves ./data/command_center.db untouched (SQLite persists on
#   disk regardless of process restarts).

$root = "D:\AI_COMMAND_CENTER"
$secretFile = Join-Path $root "secrets\jwt_secret.txt"
$logDir = Join-Path $root "logs"
$python = Join-Path $root ".venv\Scripts\python.exe"

if (-not (Test-Path $secretFile)) {
    throw "Missing $secretFile -- JWT_SECRET must be provisioned before starting."
}

if (-not (Test-Path $logDir)) {
    New-Item -ItemType Directory -Force -Path $logDir | Out-Null
}

$env:APP_ENV = "production"
$env:JWT_SECRET = (Get-Content $secretFile -Raw).Trim()

Set-Location $root

while ($true) {
    $timestamp = Get-Date -Format "yyyyMMdd-HHmmss"
    $logFile = Join-Path $logDir "uvicorn-$timestamp.log"

    Write-Output "[$timestamp] Starting uvicorn (logging to $logFile)"

    try {
        & $python -m uvicorn api.app:app --host 0.0.0.0 --port 8000 *>> $logFile
        $exitCode = $LASTEXITCODE
    } catch {
        $exitCode = "error: $_"
    }

    Write-Output "[$timestamp] uvicorn exited with code $exitCode -- restarting in 5s"

    Start-Sleep -Seconds 5
}
