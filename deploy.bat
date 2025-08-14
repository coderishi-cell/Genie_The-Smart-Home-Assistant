@echo off
echo.
echo ============================================
echo   Genie Smart Home Face Recognition App
echo            Deployment Script
echo ============================================
echo.

:: Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python is not installed or not in PATH
    echo Please install Python 3.8+ from https://python.org
    pause
    exit /b 1
)

:: Check if Node.js is installed
node --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Node.js is not installed or not in PATH
    echo Please install Node.js from https://nodejs.org
    pause
    exit /b 1
)

:: Check if npm is installed
npm --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] npm is not installed or not in PATH
    pause
    exit /b 1
)

echo [INFO] Prerequisites check passed!
echo.

:: Kill any existing processes on ports 8000 and 5173
echo [INFO] Stopping any existing services...
taskkill /F /IM python.exe 2>nul
taskkill /F /IM node.exe 2>nul
timeout /t 2 >nul

:: Setup Backend
echo [INFO] Setting up Backend...
cd genie-ai-vibe

if not exist requirements.txt (
    echo [ERROR] requirements.txt not found in project directory
    pause
    exit /b 1
)

echo [INFO] Installing Python dependencies...
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
if errorlevel 1 (
    echo [ERROR] Failed to install backend dependencies
    pause
    exit /b 1
)

:: Create known_faces directory in backend if it doesn't exist
cd backend
if not exist known_faces (
    mkdir known_faces
    echo [INFO] Created known_faces directory
)
cd ..

:: Setup Frontend
echo [INFO] Setting up Frontend...
cd frontend

if not exist package.json (
    echo [ERROR] package.json not found in frontend directory
    pause
    exit /b 1
)

echo [INFO] Installing Node.js dependencies...
npm install
if errorlevel 1 (
    echo [ERROR] Failed to install frontend dependencies
    pause
    exit /b 1
)

:: Go back to root directory
cd ..\..

echo.
echo ============================================
echo           Starting Services...
echo ============================================
echo.

:: Start Backend Server in a new window
echo [INFO] Starting Backend Server (Python FastAPI)...
start "Genie Backend Server" cmd /k "cd genie-ai-vibe\backend && python main.py"

:: Wait for backend to start
timeout /t 5 >nul

:: Start Frontend Server in a new window
echo [INFO] Starting Frontend Server (React + Vite)...
start "Genie Frontend Server" cmd /k "cd genie-ai-vibe\frontend && npm run dev"

:: Wait for frontend to start
timeout /t 8 >nul

echo.
echo ============================================
echo          Deployment Complete!
echo ============================================
echo.
echo Application URLs:
echo   Frontend: http://localhost:5173
echo   Backend:  http://localhost:8000
echo   API Docs: http://localhost:8000/docs
echo.
echo Available Features:
echo   - Smart Home Controls
echo   - Face Recognition System
echo   - Smart Doorbell with Auto-Open
echo   - Device Control and Automation
echo   - AI Assistant Integration
echo.
echo The application is now running in separate windows.
echo Close the terminal windows to stop the services.
echo.

:: Ask if user wants to open browser
set /p openBrowser="Would you like to open the application in your browser? (y/n): "
if /i "%openBrowser%"=="y" (
    echo Opening application in browser...
    timeout /t 2 >nul
    start http://localhost:5173
)

echo.
echo Press any key to exit this deployment script...
echo The application will continue running in the background windows.
pause >nul 