param(
    [string] $DataDirectory,
    [switch] $CheckOnly,
    [switch] $Offline,
    [switch] $OpenBrowser
)

$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
$pythonPath = Join-Path $projectRoot '.venv\Scripts\python.exe'
if (-not (Test-Path -LiteralPath $pythonPath)) { throw 'Create .venv and install backend/requirements.txt first. See docs/SETUP.md.' }
$npmPath = (Get-Command npm.cmd -ErrorAction Stop).Source
$backendPath = Join-Path $projectRoot 'backend'
$frontendPath = Join-Path $projectRoot 'frontend'
if (-not (Test-Path -LiteralPath (Join-Path $frontendPath 'node_modules'))) { throw 'Run npm.cmd ci inside frontend first.' }
$dataPath = if ($DataDirectory) { $ExecutionContext.SessionState.Path.GetUnresolvedProviderPathFromPSPath($DataDirectory) } else { Join-Path $backendPath '.data' }
if (Test-Path -LiteralPath $dataPath -PathType Leaf) { throw 'DataDirectory must be a directory, not a file.' }

function Test-LocalPort([int] $Port) {
    $connection = [Net.Sockets.TcpClient]::new()
    try {
        $attempt = $connection.ConnectAsync('127.0.0.1', $Port)
        try { $null = $attempt.Wait(300) } catch { return $false }
        return $connection.Connected
    } finally { $connection.Dispose() }
}

foreach ($port in @(8000, 5173)) {
    if (Test-LocalPort $port) { throw "Port $port is already in use. Close the earlier local test server before starting another; no process was stopped." }
}
Write-Host "Local workspace: $dataPath"
Write-Host 'Frontend: http://127.0.0.1:5173/ (loopback only)'
if ($CheckOnly) { Write-Host 'Local prerequisites and ports are ready. No server started.'; return }

$previousLocation = Get-Location
$previousMode = $env:GRANTTHREAD_MODE
$previousData = $env:GRANTTHREAD_DATA_DIR
$previousPort = $env:GRANTTHREAD_PORT
$previousModel = $env:BEDROCK_MODEL_ID
$localFrontend = @{
    VITE_API_URL = '/api'
    VITE_BASE_PATH = '/'
    GRANTTHREAD_LOCAL_FRONTEND = '1'
}
$previousFrontend = @{}
foreach ($name in $localFrontend.Keys) { $previousFrontend[$name] = [Environment]::GetEnvironmentVariable($name, 'Process') }
$apiProcess = $null
$logDirectory = Join-Path $projectRoot 'artifacts\local-logs'
New-Item -ItemType Directory -Path $logDirectory -Force | Out-Null
$logPrefix = Join-Path $logDirectory ('api-' + [guid]::NewGuid().ToString('N'))
try {
    $env:GRANTTHREAD_MODE = 'local'
    $env:GRANTTHREAD_DATA_DIR = $dataPath
    $env:GRANTTHREAD_PORT = '8000'
    foreach ($name in $localFrontend.Keys) { [Environment]::SetEnvironmentVariable($name, $localFrontend[$name], 'Process') }
    if ($Offline) { $env:BEDROCK_MODEL_ID = ''; Write-Host 'Offline testing: Bedrock calls are disabled for this run.' }
    $apiProcess = Start-Process -FilePath $pythonPath -ArgumentList @('-m', 'grantthread.local_server') -WorkingDirectory $backendPath -WindowStyle Hidden -PassThru -RedirectStandardOutput "$logPrefix.out.log" -RedirectStandardError "$logPrefix.err.log"
    $ready = $false
    for ($attempt = 0; $attempt -lt 30; $attempt++) {
        if ($apiProcess.HasExited) { throw "Local API stopped during startup. Read $logPrefix.err.log" }
        try {
            $health = Invoke-RestMethod -Uri 'http://127.0.0.1:8000/api/health' -TimeoutSec 1
            if ($health.status -eq 'ok' -and $health.mode -eq 'local') { $ready = $true; break }
        } catch { }
        Start-Sleep -Milliseconds 200
    }
    if (-not $ready) { throw "Local API did not become ready. Read $logPrefix.err.log" }
    Set-Location -LiteralPath $frontendPath
    if ($OpenBrowser) { & $npmPath run dev -- --open } else { & $npmPath run dev }
} finally {
    try {
        if ($apiProcess -and -not $apiProcess.HasExited) { Stop-Process -Id $apiProcess.Id -ErrorAction SilentlyContinue }
    } finally {
        Set-Location -LiteralPath $previousLocation.Path
        $env:GRANTTHREAD_MODE = $previousMode
        $env:GRANTTHREAD_DATA_DIR = $previousData
        $env:GRANTTHREAD_PORT = $previousPort
        $env:BEDROCK_MODEL_ID = $previousModel
        foreach ($name in $previousFrontend.Keys) { [Environment]::SetEnvironmentVariable($name, $previousFrontend[$name], 'Process') }
    }
}
