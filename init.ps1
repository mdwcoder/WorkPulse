$ErrorActionPreference = "Stop"

$Root = $PSScriptRoot
$Venv = Join-Path $Root ".venv"
$Req = Join-Path $Root "requirements.txt"
$BinDir = Join-Path $env:LOCALAPPDATA "CoreUtils\bin"
$Launcher = Join-Path $BinDir "workpulse.cmd"

if (-not (Get-Command python -ErrorAction SilentlyContinue)) { throw "Python 3.11+ is required." }
python -c "import sys; raise SystemExit(0 if sys.version_info >= (3, 11) else 1)"
if ($LASTEXITCODE -ne 0) { throw "Python 3.11+ is required." }

if (-not (Test-Path (Join-Path $Venv "Scripts\python.exe"))) {
    python -m venv $Venv
}

$VenvPython = Join-Path $Venv "Scripts\python.exe"
& $VenvPython -m pip install --upgrade pip
& $VenvPython -m pip install -r $Req

New-Item -ItemType Directory -Force -Path $BinDir | Out-Null
@"
@echo off
cd /d "$Root"
"$VenvPython" main.py %*
"@ | Set-Content -Path $Launcher -Encoding ASCII

Write-Host "WorkPulse initialization complete."
Write-Host "Launcher installed at $Launcher"
