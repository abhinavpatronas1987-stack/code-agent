# PowerShell script to run E2E tests
Write-Host "Starting End-to-End Tests..." -ForegroundColor Cyan
Write-Host ""

Set-Location D:\code-agent
.\.venv\Scripts\Activate.ps1

# Check if Ollama is running
Write-Host "Checking Ollama..." -ForegroundColor Yellow
try {
    $response = Invoke-WebRequest -Uri "http://localhost:11434/api/tags" -TimeoutSec 5 -ErrorAction Stop
    Write-Host "Ollama is running!" -ForegroundColor Green
} catch {
    Write-Host "ERROR: Ollama is not running!" -ForegroundColor Red
    Write-Host "Please start Ollama first with: ollama serve" -ForegroundColor Yellow
    exit 1
}

Write-Host ""
Write-Host "Running E2E tests..." -ForegroundColor Cyan
python scripts\test_e2e.py
