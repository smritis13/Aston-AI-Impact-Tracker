# PowerShell script to start Docker development environment
# Usage: .\start-docker.ps1

Write-Host "Starting Aston AI Research Tool with Docker..." -ForegroundColor Green

# Check if .env file exists
if (-Not (Test-Path "backend\.env")) {
    Write-Host "Creating .env file from .env.example..." -ForegroundColor Yellow
    Copy-Item "backend\.env.example" "backend\.env"
    Write-Host "Please edit backend\.env and add your API keys before continuing!" -ForegroundColor Red
    Write-Host "Press any key to continue after editing .env file..."
    $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
}

# Start Docker Compose
Write-Host "Starting Docker containers..." -ForegroundColor Green
docker-compose up --build
