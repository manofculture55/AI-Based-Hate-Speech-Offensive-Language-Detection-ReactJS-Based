@echo off
setlocal ENABLEDELAYEDEXPANSION

REM =====================================================
REM  Hate Speech Detection - one-time setup
REM
REM  Run this ONCE. Afterwards use run.bat to start the app.
REM
REM  This script does not delete or rewrite itself when it
REM  finishes. It records a marker file (.setup-complete)
REM  instead, and refuses to redo the work unless you ask.
REM  Keeping it means you can still repair a broken venv or
REM  pick up new dependencies later:
REM
REM      install.bat /repair    re-run setup from scratch
REM
REM =====================================================

cd /d "%~dp0"

set "MARKER=.setup-complete"

echo.
echo  Hate Speech Detection - Setup
echo  =============================
echo.

REM -------------------------------
REM Already installed?
REM -------------------------------
if exist "%MARKER%" (
    if /i not "%~1"=="/repair" (
        echo  [INFO] Setup has already been completed on this machine.
        echo.
        echo         To start the app:      run.bat
        echo         To redo setup:         install.bat /repair
        echo.
        set /p "LAUNCH=Start the app now? [Y/n] "
        if /i "!LAUNCH!"=="n" goto :eof
        call run.bat
        goto :eof
    )
    echo  [INFO] /repair requested - running full setup again.
    echo.
)

REM -------------------------------
REM 0. Prerequisites
REM -------------------------------
where node >nul 2>nul
if errorlevel 1 (
    echo  [ERROR] Node.js is not installed or not on PATH.
    echo          Install it from https://nodejs.org and re-run this script.
    pause
    exit /b 1
)

where python >nul 2>nul
if errorlevel 1 (
    echo  [ERROR] Python is not installed or not on PATH.
    echo          Install Python 3.10+ and re-run this script.
    pause
    exit /b 1
)

REM npm reads its global prefix from here; npx fails with ENOENT if it is absent.
if not exist "%APPDATA%\npm" mkdir "%APPDATA%\npm"

echo  [1/7] Prerequisites OK.

REM -------------------------------
REM 1. Python virtual environment
REM -------------------------------
if not exist "venv" (
    echo  [2/7] Creating virtual environment...
    python -m venv venv
    if errorlevel 1 (
        echo  [ERROR] Failed to create the virtual environment.
        pause
        exit /b 1
    )
) else (
    echo  [2/7] Virtual environment already exists.
)

call venv\Scripts\activate

REM -------------------------------
REM 2. Python dependencies
REM -------------------------------
echo  [3/7] Installing Python dependencies (this takes a few minutes)...
python -m pip install --upgrade pip >nul
pip install -r requirements.txt
if errorlevel 1 (
    echo  [ERROR] Dependency installation failed.
    pause
    exit /b 1
)

REM -------------------------------
REM 3. Configuration
REM -------------------------------
if not exist ".env" (
    echo  [4/7] Creating .env from .env.example...
    copy /y ".env.example" ".env" >nul
    echo         NOTE: .env ships with placeholder API and admin keys.
    echo               Change them before exposing this app to anyone else.
) else (
    echo  [4/7] .env already exists - leaving it untouched.
)

if not exist "frontend\.env" (
    if exist "frontend\.env.example" (
        copy /y "frontend\.env.example" "frontend\.env" >nul
    )
)

REM -------------------------------
REM 4. Database
REM -------------------------------
if not exist "backend\data" mkdir backend\data
if not exist "backend\models" mkdir backend\models
if not exist "backend\reports" mkdir backend\reports

REM Safe to repeat: creates missing tables and applies additive migrations
REM without touching stored rows.
echo  [5/7] Initializing / migrating the database...
python -m backend.src.utils.db
if errorlevel 1 (
    echo  [ERROR] Database initialization failed.
    pause
    exit /b 1
)

REM -------------------------------
REM 5. Dataset + models
REM -------------------------------
if not exist "backend\data\clean_data.csv" (
    echo  [6/7] Normalizing datasets...
    python -m backend.src.data.normalize
) else (
    echo  [6/7] Normalized dataset already present - skipping.
)

if not exist "backend\models\deep\bilstm_model.h5" (
    echo        Training models (this can take a while)...
    python -m backend.src.training.train
) else (
    echo        Trained models already present - skipping training.
)

REM -------------------------------
REM 6. Frontend
REM -------------------------------
REM Only scaffolded when genuinely absent. An earlier version of this script
REM deleted frontend\ and re-ran create-react-app on every single run, copying
REM src to a temp folder and back; any failure in between left the source
REM stranded in that temp folder with the project gone.
echo  [7/7] Setting up frontend...

if not exist "frontend\package.json" (
    echo        No frontend found - creating a new React app...
    call npx create-react-app frontend
    if errorlevel 1 (
        echo  [ERROR] create-react-app failed.
        pause
        exit /b 1
    )
    if exist "frontend\.git" rmdir /s /q frontend\.git
) else (
    echo        Frontend already exists - keeping your source files.
)

pushd frontend
call npm install
if errorlevel 1 (
    echo  [ERROR] npm install failed.
    popd
    pause
    exit /b 1
)
popd

REM -------------------------------
REM Done
REM -------------------------------
> "%MARKER%" echo Setup completed on %DATE% %TIME%
>>"%MARKER%" echo Delete this file (or run "install.bat /repair") to force a full re-install.

echo.
echo  =============================================
echo   Setup complete.
echo.
echo   From now on, start the app with:  run.bat
echo  =============================================
echo.

set /p "LAUNCH=Start the app now? [Y/n] "
if /i "%LAUNCH%"=="n" goto :eof

call run.bat
