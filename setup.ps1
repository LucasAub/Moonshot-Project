# PDF to HTML Converter Setup Script
Write-Host "Setting up PDF to HTML Converter..." -ForegroundColor Green

# Check if Python is installed
try {
    $pythonVersion = python --version 2>&1
    Write-Host "Found Python: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "Python is not installed or not in PATH. Please install Python 3.8+ first." -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

# Create virtual environment if it doesn't exist
if (-not (Test-Path "venv")) {
    Write-Host "Creating virtual environment..." -ForegroundColor Yellow
    python -m venv venv
}

# Activate virtual environment
Write-Host "Activating virtual environment..." -ForegroundColor Yellow
& "venv\Scripts\Activate.ps1"

# Upgrade pip
Write-Host "Upgrading pip..." -ForegroundColor Yellow
python -m pip install --upgrade pip

# Install requirements
Write-Host "Installing requirements..." -ForegroundColor Yellow
pip install -r requirements.txt

Write-Host ""
Write-Host "Setup complete!" -ForegroundColor Green
Write-Host ""
Write-Host "To run the server:" -ForegroundColor Cyan
Write-Host "1. Activate virtual environment: venv\Scripts\Activate.ps1" -ForegroundColor White
Write-Host "2. Run server: python src\Backend\server.py" -ForegroundColor White
Write-Host ""
Write-Host "The server will be available at: http://localhost:8000" -ForegroundColor Yellow
Write-Host "Frontend should be at: http://localhost:5173" -ForegroundColor Yellow
Write-Host ""

# Check if Tesseract is installed
Write-Host "Checking for Tesseract OCR..." -ForegroundColor Cyan
$tesseractPaths = @(
    "C:\Program Files\Tesseract-OCR\tesseract.exe",
    "C:\Program Files (x86)\Tesseract-OCR\tesseract.exe"
)

$tesseractFound = $false
foreach ($path in $tesseractPaths) {
    if (Test-Path $path) {
        Write-Host "Found Tesseract at: $path" -ForegroundColor Green
        $tesseractFound = $true
        break
    }
}

if (-not $tesseractFound) {
    Write-Host "Tesseract OCR not found in common locations." -ForegroundColor Red
    Write-Host "Please install Tesseract OCR from: https://github.com/UB-Mannheim/tesseract/wiki" -ForegroundColor Yellow
    Write-Host "OCR functionality (image text extraction) will not work without Tesseract." -ForegroundColor Yellow
}

Read-Host "Press Enter to exit"
