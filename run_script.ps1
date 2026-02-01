# PowerShell script to install Python and run the card extractor

Write-Host "=== Telegram Card Extractor Setup ===" -ForegroundColor Cyan

# Check if Python is installed
$pythonInstalled = $false
try {
    $pythonVersion = python --version 2>&1
    if ($pythonVersion -notmatch "was not found") {
        Write-Host "✓ Python found: $pythonVersion" -ForegroundColor Green
        $pythonInstalled = $true
    }
} catch {
    Write-Host "✗ Python not found" -ForegroundColor Red
}

# If Python not installed, try to install
if (-not $pythonInstalled) {
    Write-Host "`nPython installation required..." -ForegroundColor Yellow
    Write-Host "Please install Python from: https://www.python.org/downloads/" -ForegroundColor Yellow
    Write-Host "Make sure to check 'Add Python to PATH' during installation." -ForegroundColor Yellow
    Write-Host "`nAfter installation, run this script again." -ForegroundColor Yellow
    
    # Try to open Python download page
    Start-Process "https://www.python.org/downloads/"
    exit 1
}

# Check if dependencies are installed
Write-Host "`nChecking dependencies..." -ForegroundColor Cyan
$depsInstalled = $true

try {
    python -c "import pyrogram" 2>$null
    if ($LASTEXITCODE -ne 0) { $depsInstalled = $false }
} catch {
    $depsInstalled = $false
}

if (-not $depsInstalled) {
    Write-Host "Installing dependencies..." -ForegroundColor Yellow
    python -m pip install -r requirements.txt
    if ($LASTEXITCODE -ne 0) {
        Write-Host "✗ Failed to install dependencies" -ForegroundColor Red
        exit 1
    }
    Write-Host "✓ Dependencies installed" -ForegroundColor Green
} else {
    Write-Host "✓ Dependencies already installed" -ForegroundColor Green
}

# Run the script
Write-Host "`n=== Starting Card Extractor ===" -ForegroundColor Cyan
python main.py
