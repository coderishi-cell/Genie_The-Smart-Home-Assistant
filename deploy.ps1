#!/usr/bin/env pwsh

# Genie Smart Home Face Recognition App - Deployment Script
# This script sets up and runs both backend and frontend services

Write-Host "🏠 Genie Smart Home Face Recognition App Deployment" -ForegroundColor Cyan
Write-Host "=================================================" -ForegroundColor Cyan
Write-Host ""

# Function to check if a command exists
function Test-Command($cmdname) {
    return [bool](Get-Command -Name $cmdname -ErrorAction SilentlyContinue)
}

# Function to kill processes on specific ports
function Stop-ProcessOnPort($port) {
    Write-Host "🔍 Checking for processes on port $port..." -ForegroundColor Yellow
    try {
        $processes = Get-NetTCPConnection -LocalPort $port -ErrorAction SilentlyContinue | Select-Object -ExpandProperty OwningProcess
        foreach ($pid in $processes) {
            Write-Host "⚠️  Stopping process $pid on port $port..." -ForegroundColor Yellow
            Stop-Process -Id $pid -Force -ErrorAction SilentlyContinue
        }
        Start-Sleep -Seconds 2
    }
    catch {
        Write-Host "✅ Port $port is available" -ForegroundColor Green
    }
}

# Check prerequisites
Write-Host "🔧 Checking prerequisites..." -ForegroundColor Yellow

if (-not (Test-Command python)) {
    Write-Host "❌ Python is not installed or not in PATH" -ForegroundColor Red
    Write-Host "Please install Python 3.8+ from https://python.org" -ForegroundColor Red
    exit 1
}

if (-not (Test-Command node)) {
    Write-Host "❌ Node.js is not installed or not in PATH" -ForegroundColor Red
    Write-Host "Please install Node.js from https://nodejs.org" -ForegroundColor Red
    exit 1
}

if (-not (Test-Command npm)) {
    Write-Host "❌ npm is not installed or not in PATH" -ForegroundColor Red
    exit 1
}

Write-Host "✅ Python: $(python --version)" -ForegroundColor Green
Write-Host "✅ Node.js: $(node --version)" -ForegroundColor Green
Write-Host "✅ npm: $(npm --version)" -ForegroundColor Green
Write-Host ""

# Stop any existing processes on ports 8000 and 3000
Stop-ProcessOnPort 8000
Stop-ProcessOnPort 3000

# Setup Backend
Write-Host "🔧 Setting up Backend..." -ForegroundColor Yellow
Set-Location "genie-ai-vibe"

if (-not (Test-Path "requirements.txt")) {
    Write-Host "❌ requirements.txt not found in backend directory" -ForegroundColor Red
    exit 1
}

Write-Host "📦 Installing Python dependencies..." -ForegroundColor Yellow
try {
    python -m pip install --upgrade pip
    python -m pip install -r requirements.txt
    Write-Host "✅ Backend dependencies installed successfully" -ForegroundColor Green
}
catch {
    Write-Host "❌ Failed to install backend dependencies" -ForegroundColor Red
    exit 1
}

# Create known_faces directory if it doesn't exist
if (-not (Test-Path "known_faces")) {
    New-Item -ItemType Directory -Name "known_faces" | Out-Null
    Write-Host "✅ Created known_faces directory" -ForegroundColor Green
}

# Setup Frontend
Write-Host "🔧 Setting up Frontend..." -ForegroundColor Yellow
Set-Location "frontend"

if (-not (Test-Path "package.json")) {
    Write-Host "❌ package.json not found in frontend directory" -ForegroundColor Red
    exit 1
}

Write-Host "📦 Installing Node.js dependencies..." -ForegroundColor Yellow
try {
    npm install
    Write-Host "✅ Frontend dependencies installed successfully" -ForegroundColor Green
}
catch {
    Write-Host "❌ Failed to install frontend dependencies" -ForegroundColor Red
    exit 1
}

# Go back to root directory
Set-Location ".."

Write-Host ""
Write-Host "🚀 Starting Services..." -ForegroundColor Cyan
Write-Host "======================" -ForegroundColor Cyan

# Start Backend Server
Write-Host "🔥 Starting Backend Server (Python FastAPI)..." -ForegroundColor Yellow
$backendJob = Start-Job -ScriptBlock {
    Set-Location $using:PWD
    Set-Location "genie-ai-vibe"
    python main.py
}

# Wait a moment for backend to start
Start-Sleep -Seconds 3

# Check if backend started successfully
try {
    $response = Invoke-RestMethod -Uri "http://localhost:8000/api/status" -Method GET -TimeoutSec 5
    Write-Host "✅ Backend server started successfully on http://localhost:8000" -ForegroundColor Green
}
catch {
    Write-Host "⚠️  Backend server starting... (may take a moment)" -ForegroundColor Yellow
}

# Start Frontend Server
Write-Host "🔥 Starting Frontend Server (React)..." -ForegroundColor Yellow
$env:BROWSER = "none"  # Prevent auto-opening browser
$frontendJob = Start-Job -ScriptBlock {
    Set-Location $using:PWD
    Set-Location "genie-ai-vibe/frontend"
    npm start
}

# Wait for frontend to start
Start-Sleep -Seconds 5

Write-Host ""
Write-Host "🎉 Deployment Complete!" -ForegroundColor Green
Write-Host "======================" -ForegroundColor Green
Write-Host ""
Write-Host "🌐 Application URLs:" -ForegroundColor Cyan
Write-Host "   Frontend: http://localhost:3000" -ForegroundColor White
Write-Host "   Backend:  http://localhost:8000" -ForegroundColor White
Write-Host "   API Docs: http://localhost:8000/docs" -ForegroundColor White
Write-Host ""
Write-Host "📋 Available Features:" -ForegroundColor Cyan
Write-Host "   🏠 Smart Home Controls" -ForegroundColor White
Write-Host "   🔍 Face Recognition System" -ForegroundColor White
Write-Host "   🚪 Smart Doorbell with Auto-Open" -ForegroundColor White
Write-Host "   💡 Device Control & Automation" -ForegroundColor White
Write-Host "   🤖 AI Assistant Integration" -ForegroundColor White
Write-Host ""
Write-Host "⚙️  System Status:" -ForegroundColor Cyan
Write-Host "   Backend Job ID: $($backendJob.Id)" -ForegroundColor White
Write-Host "   Frontend Job ID: $($frontendJob.Id)" -ForegroundColor White
Write-Host ""
Write-Host "🔧 Management Commands:" -ForegroundColor Cyan
Write-Host "   To stop backend:  Stop-Job $($backendJob.Id)" -ForegroundColor White
Write-Host "   To stop frontend: Stop-Job $($frontendJob.Id)" -ForegroundColor White
Write-Host "   To stop all:      Stop-Job $($backendJob.Id), $($frontendJob.Id)" -ForegroundColor White
Write-Host ""

# Function to open browser
function Open-Browser {
    Start-Process "http://localhost:3000"
}

# Ask user if they want to open browser
Write-Host "Would you like to open the application in your browser? (y/n): " -ForegroundColor Yellow -NoNewline
$openBrowser = Read-Host

if ($openBrowser -eq "y" -or $openBrowser -eq "Y" -or $openBrowser -eq "yes") {
    Write-Host "🌐 Opening application in browser..." -ForegroundColor Green
    Start-Sleep -Seconds 2
    Open-Browser
}

Write-Host ""
Write-Host "⏹️  Press Ctrl+C to stop all services" -ForegroundColor Yellow
Write-Host "📱 The application is now running and ready to use!" -ForegroundColor Green
Write-Host ""

# Keep script running and monitor jobs
try {
    while ($true) {
        # Check if jobs are still running
        $backendRunning = (Get-Job -Id $backendJob.Id).State -eq "Running"
        $frontendRunning = (Get-Job -Id $frontendJob.Id).State -eq "Running"
        
        if (-not $backendRunning) {
            Write-Host "⚠️  Backend server stopped unexpectedly" -ForegroundColor Red
            Receive-Job -Id $backendJob.Id
        }
        
        if (-not $frontendRunning) {
            Write-Host "⚠️  Frontend server stopped unexpectedly" -ForegroundColor Red
            Receive-Job -Id $frontendJob.Id
        }
        
        if (-not $backendRunning -and -not $frontendRunning) {
            Write-Host "❌ Both services stopped. Exiting..." -ForegroundColor Red
            break
        }
        
        Start-Sleep -Seconds 5
    }
}
catch {
    Write-Host ""
    Write-Host "🛑 Shutting down services..." -ForegroundColor Yellow
}
finally {
    # Cleanup
    Write-Host "🧹 Cleaning up..." -ForegroundColor Yellow
    Stop-Job $backendJob.Id, $frontendJob.Id -ErrorAction SilentlyContinue
    Remove-Job $backendJob.Id, $frontendJob.Id -Force -ErrorAction SilentlyContinue
    
    # Try to stop processes on ports
    Stop-ProcessOnPort 8000
    Stop-ProcessOnPort 3000
    
    Write-Host "✅ Services stopped successfully" -ForegroundColor Green
    Write-Host "👋 Thank you for using Genie Smart Home!" -ForegroundColor Cyan
} 