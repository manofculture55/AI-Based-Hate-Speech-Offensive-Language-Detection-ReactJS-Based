@echo off
setlocal ENABLEDELAYEDEXPANSION

REM =====================================================
REM  Hate Speech Detection - start the application
REM
REM  Everyday entry point. Run install.bat once first.
REM
REM  Usage:
REM    run.bat              start backend + frontend (development)
REM    run.bat backend      start the API only
REM    run.bat frontend     start the React dev server only
REM    run.bat prod         serve the API with waitress instead of
REM                         the Flask development server
REM =====================================================

cd /d "%~dp0"

set "MODE=%~1"
if "%MODE%"=="" set "MODE=all"

REM -------------------------------
REM Preflight
REM -------------------------------
if not exist "venv\Scripts\activate.bat" (
    echo  [ERROR] No virtual environment found.
    echo          Run install.bat first.
    pause
    exit /b 1
)

if not exist "backend\models\deep\bilstm_model.h5" (
    echo  [WARN] No trained model found at backend\models\deep\bilstm_model.h5
    echo         The API will start, but prediction endpoints will return
    echo         503 until you train. Run install.bat /repair to train.
    echo.
)

if /i not "%MODE%"=="backend" (
    if not exist "frontend\node_modules" (
        echo  [ERROR] Frontend dependencies are not installed.
        echo          Run install.bat first.
        pause
        exit /b 1
    )
)

REM -------------------------------
REM Launch
REM -------------------------------
if /i "%MODE%"=="backend" goto :backend
if /i "%MODE%"=="prod"    goto :prod
if /i "%MODE%"=="frontend" goto :frontend
if /i "%MODE%"=="all"     goto :all

echo  [ERROR] Unknown option "%MODE%".
echo          Use: run.bat [backend^|frontend^|prod]
pause
exit /b 1

:backend
echo  [INFO] Starting the API (development server)...
call venv\Scripts\activate
python -m backend.app
goto :eof

:prod
echo  [INFO] Starting the API (waitress)...
call venv\Scripts\activate
python -m backend.wsgi
goto :eof

:frontend
echo  [INFO] Starting the React dev server...
pushd frontend
call npm start
popd
goto :eof

:all
echo.
echo  Starting Hate Speech Detection
echo  =============================
echo.
echo  [INFO] Starting backend...
start "Backend" cmd /k "cd /d "%~dp0" && venv\Scripts\activate && python -m backend.app"

echo  [INFO] Starting frontend...
start "Frontend" cmd /k "cd /d "%~dp0frontend" && npm start"

echo.
echo   Web app:    http://localhost:3000
echo   API index:  http://127.0.0.1:5000/api/v1
echo   Health:     http://127.0.0.1:5000/api/v1/health
echo.
echo   Two new windows have opened. Close them to stop the app.
echo.
timeout /t 8 >nul
goto :eof
