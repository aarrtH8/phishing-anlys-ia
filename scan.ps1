# PhishHunter Robust Scan Script
param([string]$url, [string]$regions = "FR")

Write-Host "🔍 PhishHunter Agentic Analysis Launcher" -ForegroundColor Cyan
Write-Host "----------------------------------------"

# 1. Check Docker
Write-Host " [1/4] Checking Docker..." -NoNewline
try {
    docker info 2>&1 | Out-Null
    if ($LASTEXITCODE -ne 0) { throw "Docker error" }
    Write-Host " OK" -ForegroundColor Green
} catch {
    Write-Host " FAILED" -ForegroundColor Red
    Write-Host "❌ Docker is not running. Please start Docker Desktop." -ForegroundColor Yellow
    exit 1
}

# 2. Check Ollama
Write-Host " [2/4] Checking Ollama (AI)..." -NoNewline
try {
    $response = Invoke-WebRequest -Uri "http://localhost:11434/api/tags" -Method Get -TimeoutSec 3 -UseBasicParsing -ErrorAction Stop
    Write-Host " OK" -ForegroundColor Green
} catch {
    Write-Host " FAILED" -ForegroundColor Red
    Write-Host "❌ Ollama is not accessible on localhost:11434." -ForegroundColor Yellow
    Write-Host "   Please run 'ollama serve' in a separate terminal." -ForegroundColor Yellow
    exit 1
}

# 3. Check Arguments
if (-not $url) {
    Write-Host "❌ Usage: .\scan.ps1 <URL> [Regions]" -ForegroundColor Red
    exit 1
}

# 4. Run Analysis
Write-Host " [3/4] Launching Container for: $url" -ForegroundColor Cyan
Write-Host "       (Output will be saved to .\output)" -ForegroundColor Gray

# Use docker compose run
# We map current folder keys if needed, but for now just run
docker compose run --rm phishhunter $url --regions $regions

if ($LASTEXITCODE -eq 0) {
    Write-Host " [4/4] Analysis Complete." -ForegroundColor Green
    
    # Try to find the latest folder in output to show user
    $latest = Get-ChildItem -Path ".\output" -Directory | Sort-Object LastWriteTime -Descending | Select-Object -First 1
    if ($latest) {
        Write-Host "✨ Results available in: " -NoNewline
        Write-Host $latest.FullName -ForegroundColor Cyan
        # Open the folder
        Invoke-Item $latest.FullName
    }
} else {
    Write-Host "❌ Analysis exited with error code $LASTEXITCODE" -ForegroundColor Red
}
