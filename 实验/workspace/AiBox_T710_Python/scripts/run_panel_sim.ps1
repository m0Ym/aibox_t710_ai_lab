<#
Run the panel in simulation mode (Windows PowerShell)
Usage: Open PowerShell, activate the venv (.\venv\Scripts\Activate.ps1) then run this script.
#>
$env:PANEL_SIM = "1"
Write-Host "PANEL_SIM=1 set. Starting panel..."
# Ensure we run the venv python if present for reproducible environment
$venvPython = Join-Path $PSScriptRoot "..\venv\Scripts\python.exe"
# Move to repo root so relative paths inside the script work as expected
Set-Location (Join-Path $PSScriptRoot "..")
if (Test-Path $venvPython) {
    Write-Host "Using venv python: $venvPython"
    & $venvPython -u src\panel.py
} else {
    Write-Host "venv python not found, falling back to system 'python'"
    python -u src\panel.py
}
