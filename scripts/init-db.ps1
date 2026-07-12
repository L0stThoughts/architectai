$ErrorActionPreference = "Stop"

# Use 'localhost' if running natively on Windows, 'db' if in Docker
$DbHost = "localhost" 
$DbUser = "architectai"

Write-Host "Waiting for Postgres at $DbHost..." -ForegroundColor Cyan

while ($true) {
    # Check if pg_isready exists. If not, we'll just try the migration.
    if (Get-Command pg_isready -ErrorAction SilentlyContinue) {
        & pg_isready -h $DbHost -U $DbUser | Out-Null
        if ($LASTEXITCODE -eq 0) { break }
        Write-Host "Postgres is unavailable - sleeping..." -ForegroundColor Gray
        Start-Sleep -Seconds 1
    } else {
        Write-Warning "pg_isready not found in PATH. Skipping check and trying migration..."
        break
    }
}

Write-Host "Running alembic migrations..." -ForegroundColor Yellow
Push-Location ../backend
# Calling via 'python -m' is safer than calling 'alembic' directly
python -m alembic -c "alembic.ini" upgrade head
Pop-Location

Write-Host "Database initialization complete." -ForegroundColor Green