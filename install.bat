@echo off
setlocal ENABLEDELAYEDEXPANSION

REM ALWAYS run from project root
cd /d "%~dp0"

echo [INFO] KRIXION Full Setup Script
echo ==================================

REM -------------------------------
REM 0. Safety check
REM -------------------------------
where node >nul 2>nul
if errorlevel 1 (
    echo [ERROR] Node.js is not installed. Please install Node.js first.
    pause
    exit /b
)

REM -------------------------------
REM 1. Create Python venv
REM -------------------------------
if not exist "venv" (
    echo [INFO] Creating virtual environment...
    python -m venv venv
) else (
    echo [INFO] Virtual environment already exists.
)

call venv\Scripts\activate

REM -------------------------------
REM 2. Install Python dependencies
REM -------------------------------
echo [INFO] Installing Python dependencies...
python -m pip install --upgrade pip
pip install -r requirements.txt

REM -------------------------------
REM 3. Ensure backend directories
REM -------------------------------
if not exist "backend\data" mkdir backend\data
if not exist "backend\models" mkdir backend\models
if not exist "backend\reports" mkdir backend\reports


REM -------------------------------
REM 4. Initialize database (once)
REM -------------------------------
if not exist "backend\data\app.db" (
    echo [INFO] Initializing SQLite database...
    python -m backend.src.utils.db
) else (
    echo [INFO] Database already initialized.
)

REM -------------------------------
REM 5. Normalize datasets (run once)
REM -------------------------------
if not exist "backend\data\clean_data.csv" (
    echo [INFO] Normalizing datasets...
    python -m backend.src.data.normalize
) else (
    echo [INFO] Normalized dataset already exists. Skipping normalization.
)


REM -------------------------------
REM 6. Train models (if missing)
REM -------------------------------
if not exist "backend\models\deep\bilstm_model.h5" (
    echo [INFO] Training models...
    python -m backend.src.training.train
) else (
    echo [INFO] Models already trained. Skipping training.
)

REM =====================================================
REM 7. FRONTEND: REBUILD FROM SCRATCH (SIMPLE & SAFE)
REM =====================================================

echo.
echo [INFO] Rebuilding frontend from scratch...
echo ------------------------------------------

REM Backup frontend/src to ROOT folder
if exist "frontend\src" (
    echo [INFO] Backing up frontend/src to src_backup...
    if exist "src_backup" rmdir /s /q src_backup
    robocopy frontend\src src_backup /E >nul
)

REM Remove old frontend completely
if exist "frontend" (
    echo [INFO] Removing old frontend folder...
    rmdir /s /q frontend
)

REM Create fresh React app
echo [INFO] Creating fresh React app...
call npx create-react-app frontend

REM Remove CRA git repo if created
if exist "frontend\.git" rmdir /s /q frontend\.git

REM Remove default CRA src
if exist "frontend\src" rmdir /s /q frontend\src

REM Restore backed-up src (if exists)
if exist "src_backup" (
    echo [INFO] Restoring src from backup...
    mkdir frontend\src
    robocopy src_backup frontend\src /E >nul
    rmdir /s /q src_backup
)


REM -------------------------------
REM 7.5 Install frontend dependencies
REM -------------------------------
echo [INFO] Installing frontend dependencies...
cd frontend
npm install react-router-dom recharts
cd ..





REM -------------------------------
REM 8. Start backend & frontend
REM -------------------------------
echo.
echo [INFO] Starting backend...
start cmd /k "cd /d %~dp0 && venv\Scripts\activate && python -m backend.app"

echo [INFO] Starting frontend...
start cmd /k "cd /d %~dp0\frontend && npm start"

echo.
echo [SUCCESS] KRIXION setup complete!
pause