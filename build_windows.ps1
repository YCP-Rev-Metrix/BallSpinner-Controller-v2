$ErrorActionPreference = 'Stop'

$repoRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $repoRoot

$venvPath = Join-Path $repoRoot '.build-venv'
$pythonExe = Join-Path $venvPath 'Scripts\python.exe'

function Test-PythonVersion {
    param([string[]]$Args)
    try {
        & py @Args '--version' *> $null
        return $true
    }
    catch {
        return $false
    }
}

if (-not (Test-PythonVersion -Args @('-3.13'))) {
    throw 'Python 3.13 was not found via py launcher. Install Python 3.13, then re-run this script.'
}

if (-not (Test-Path $pythonExe)) {
    Write-Host 'Creating local build virtual environment (.build-venv) with Python 3.13...'
    & py -3.13 -m venv $venvPath
}

Write-Host 'Installing build dependencies...'
& $pythonExe -m pip install --upgrade pip
& $pythonExe -m pip install -r requirements.txt pyinstaller

Write-Host 'Building Windows application with PyInstaller...'
& $pythonExe -m PyInstaller --clean -y main.spec

Write-Host ''
Write-Host 'Build complete.'
Write-Host 'Output:'
Write-Host '  dist\BallSpinnerController\BallSpinnerController.exe'
