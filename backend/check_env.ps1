Write-Host "Checking backend environment..."
. .venv\Scripts\Activate.ps1
python -V
python -m pip show pydantic | Out-Host
python -m pip show pydantic-core | Out-Host
try {
    python -c "import pydantic_core; print('pydantic_core OK: ', pydantic_core.__file__)"
} catch {
    Write-Warning "pydantic_core import failed"
}
