# PowerShell script to run unit tests for the server_enhanced.py module

Write-Host "Running unit tests for server_enhanced.py..." -ForegroundColor Green

# Check if pytest is installed
try {
    python -m pytest --version | Out-Null
    Write-Host "pytest found" -ForegroundColor Green
} catch {
    Write-Host "pytest not found. Installing testing dependencies..." -ForegroundColor Yellow
    python -m pip install -r requirements.txt
}

# Run the tests
Write-Host "Executing tests..." -ForegroundColor Blue
python -m pytest src/Backend/test_server_enhanced.py -v --tb=short

if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ All tests passed!" -ForegroundColor Green
} else {
    Write-Host "❌ Some tests failed!" -ForegroundColor Red
}

# Keep window open if run directly
if ($MyInvocation.InvocationName -ne ".") {
    Write-Host "Press any key to continue..."
    $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
}
