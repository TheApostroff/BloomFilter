Write-Host "Starting both backend and frontend in separate windows (PowerShell)"

# Start backend in a new PowerShell window using start-backend script
Start-Process powershell -ArgumentList '-NoExit', '-Command', 'cd backend; .\start-backend.ps1'

# Wait for backend health to be up
Write-Host "Waiting for backend health endpoint (http://localhost:8000/api/health)"
$ready = $false
for ($i = 0; $i -lt 30; $i++) {
	try {
		$r = Invoke-RestMethod -Uri 'http://localhost:8000/api/health' -Method Get -TimeoutSec 2
		if ($r -and $r.status -eq 'ok') { $ready = $true; break }
	} catch {}
	Write-Host "Backend not ready yet...($($i+1)/30)"; Start-Sleep -Seconds 1
}
if (-not $ready) { Write-Warning "Timeout waiting for backend; frontend will start but may fail to fetch." }

# Start frontend in new PowerShell window using start-frontend script
Start-Process powershell -ArgumentList '-NoExit', '-Command', 'cd frontend; .\start-frontend.ps1'

Write-Host "Started both. See the two new windows for logs."
