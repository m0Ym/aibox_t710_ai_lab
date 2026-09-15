<#
Create a Python venv and install requirements on Windows (PowerShell).
Usage: Open PowerShell, cd to repo root and run: .\scripts\setup_venv.ps1
#>
$venvPath = "venv"
if (-not (Test-Path $venvPath)) {
    python -m venv $venvPath
}
$activate = Join-Path $venvPath "Scripts\Activate.ps1"
if (Test-Path $activate) {
    Write-Host "Activating venv..."
    & $activate
    python -m pip install --upgrade pip
    if (Test-Path "requirements.txt") {
        python -m pip install -r requirements.txt
    }
    Write-Host "Setup complete. To run with simulators: .\scripts\run_panel_sim.ps1"
} else {
    Write-Host "Cannot find Activate.ps1 in $venvPath/Scripts. venv creation may have failed."
}
