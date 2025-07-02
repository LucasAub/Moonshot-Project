# Run both Frontend and Backend servers
Write-Host "Starting Full-Stack PDF to HTML Converter..." -ForegroundColor Green

# Function to start backend in a new PowerShell window
function Start-Backend {
    Write-Host "Starting Backend Server..." -ForegroundColor Yellow
    
    # Check if virtual environment exists
    if (-not (Test-Path "venv")) {
        Write-Host "Virtual environment not found. Running setup first..." -ForegroundColor Red
        & ".\setup.ps1"
    }
    
    # Start backend in a new PowerShell window
    Start-Process powershell -ArgumentList "-NoExit", "-Command", "& '.\run_server.ps1'"
}

# Function to start frontend
function Start-Frontend {
    Write-Host "Starting Frontend Server..." -ForegroundColor Yellow
    
    # Navigate to frontend directory
    Set-Location -Path "src\Frontend\project"
    
    # Check if node_modules exists
    if (-not (Test-Path "node_modules")) {
        Write-Host "Installing frontend dependencies..." -ForegroundColor Yellow
        npm install
    }
    
    # Wait a moment for backend to start
    Start-Sleep -Seconds 3
    
    # Start frontend
    Write-Host "Starting Vite dev server..." -ForegroundColor Green
    npm run dev
}

# Start both servers
try {
    Start-Backend
    Start-Frontend
} catch {
    Write-Host "Error starting servers: $_" -ForegroundColor Red
    Read-Host "Press Enter to exit"
}
