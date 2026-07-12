$ErrorActionPreference = "Stop"

Write-Host "--- Bootstrapping dev environment ---" -ForegroundColor Cyan

# 1. Frontend
Write-Host "Installing frontend deps..." -ForegroundColor Yellow
if (Test-Path "../frontend") {
    Push-Location ../frontend
    npm install
    Pop-Location
}

# 2. Backend Dependencies
Write-Host "Installing Python dependencies..." -ForegroundColor Yellow
if (Test-Path "../backend") {
    Push-Location ../backend
    # Install requirements (including playwright and alembic)
    python -m pip install -r requirements.txt
    
    Write-Host "Installing Playwright browsers..." -ForegroundColor Yellow
    python -m playwright install --with-deps
    
    if ($LASTEXITCODE -ne 0) {
        Write-Warning "Playwright install had issues, but continuing..."
    }
    Pop-Location
}

Write-Host "Done!" -ForegroundColor Green