$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
$pythonPath = Join-Path $projectRoot '.venv\Scripts\python.exe'
if (-not (Test-Path -LiteralPath $pythonPath)) { throw 'Create .venv and install backend/requirements.txt first. See docs/SETUP.md.' }
$npmPath = (Get-Command npm.cmd -ErrorAction Stop).Source
$backendPath = Join-Path $projectRoot 'backend'
$frontendPath = Join-Path $projectRoot 'frontend'
if (-not (Test-Path -LiteralPath (Join-Path $frontendPath 'node_modules'))) { throw 'Run npm.cmd ci inside frontend first.' }
$apiProcess = Start-Process -FilePath $pythonPath -ArgumentList @('-m', 'grantthread.local_server') -WorkingDirectory $backendPath -WindowStyle Hidden -PassThru
try {
    Set-Location -LiteralPath $frontendPath
    & $npmPath run dev
} finally {
    if (-not $apiProcess.HasExited) { Stop-Process -Id $apiProcess.Id }
}
