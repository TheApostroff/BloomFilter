param(
    [switch]$Reinstall
)

Write-Host "Starting backend (PowerShell) - ensure .venv and dependencies are installed"
if (!(Test-Path .venv)) {
    python -m venv .venv
}
. .venv\Scripts\Activate.ps1
python -m pip install -U pip
if ($Reinstall) { python -m pip install --upgrade --force-reinstall -r requirements.txt } else { python -m pip install -r requirements.txt }

Write-Host "Launching uvicorn..."
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
