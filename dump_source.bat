@echo off
set OUTPUT=project_source_dump.txt

if exist "%OUTPUT%" del "%OUTPUT%"

echo KRIXION SOURCE DUMP > "%OUTPUT%"
echo Generated on %DATE% %TIME% >> "%OUTPUT%"
echo. >> "%OUTPUT%"

REM ===== ROOT FILES =====
echo ============================== >> "%OUTPUT%"
echo FILE: .gitignore >> "%OUTPUT%"
echo ============================== >> "%OUTPUT%"
type ".gitignore" >> "%OUTPUT%"
echo. >> "%OUTPUT%"

echo ============================== >> "%OUTPUT%"
echo FILE: requirements.txt >> "%OUTPUT%"
echo ============================== >> "%OUTPUT%"
type "requirements.txt" >> "%OUTPUT%"
echo. >> "%OUTPUT%"

echo ============================== >> "%OUTPUT%"
echo FILE: install.bat >> "%OUTPUT%"
echo ============================== >> "%OUTPUT%"
type "install.bat" >> "%OUTPUT%"
echo. >> "%OUTPUT%"

REM ===== BACKEND =====
echo ============================== >> "%OUTPUT%"
echo FILE: backend\app.py >> "%OUTPUT%"
echo ============================== >> "%OUTPUT%"
type "backend\app.py" >> "%OUTPUT%"
echo. >> "%OUTPUT%"

for %%F in (
    backend\src\models\baseline.py
    backend\src\models\bilstm.py
    backend\src\models\transformer.py
    backend\src\data\preprocess.py
    backend\src\data\langid.py
    backend\src\data\normalize.py
    backend\src\training\train.py
    backend\src\training\evaluate.py
    backend\src\utils\db.py
) do (
    echo ============================== >> "%OUTPUT%"
    echo FILE: %%F >> "%OUTPUT%"
    echo ============================== >> "%OUTPUT%"
    type "%%F" >> "%OUTPUT%"
    echo. >> "%OUTPUT%"
)

REM ===== FRONTEND =====
echo ============================== >> "%OUTPUT%"
echo FILE: frontend\public\index.html >> "%OUTPUT%"
echo ============================== >> "%OUTPUT%"
type "frontend\public\index.html" >> "%OUTPUT%"
echo. >> "%OUTPUT%"

echo ============================== >> "%OUTPUT%"
echo FILE: frontend\src\App.js >> "%OUTPUT%"
echo ============================== >> "%OUTPUT%"
type "frontend\src\App.js" >> "%OUTPUT%"
echo. >> "%OUTPUT%"

echo ============================== >> "%OUTPUT%"
echo FILE: frontend\src\index.js >> "%OUTPUT%"
echo ============================== >> "%OUTPUT%"
type "frontend\src\index.js" >> "%OUTPUT%"
echo. >> "%OUTPUT%"

echo ============================== >> "%OUTPUT%"
echo FILE: frontend\src\index.css >> "%OUTPUT%"
echo ============================== >> "%OUTPUT%"
type "frontend\src\index.css" >> "%OUTPUT%"
echo. >> "%OUTPUT%"

echo ============================== >> "%OUTPUT%"
echo FILE: frontend\src\App.css >> "%OUTPUT%"
echo ============================== >> "%OUTPUT%"
type "frontend\src\App.css" >> "%OUTPUT%"
echo. >> "%OUTPUT%"

echo ============================== >> "%OUTPUT%"
echo FILE: frontend\src\reportWebVitals.js >> "%OUTPUT%"
echo ============================== >> "%OUTPUT%"
type "frontend\src\reportWebVitals.js" >> "%OUTPUT%"
echo. >> "%OUTPUT%"

for %%F in (
    frontend\src\pages\Home.js
    frontend\src\pages\History.js
    frontend\src\pages\Analytics.js
    frontend\src\pages\Admin.js
    frontend\src\components\Navbar.js
    frontend\src\components\ThemeContext.js
) do (
    echo ============================== >> "%OUTPUT%"
    echo FILE: %%F >> "%OUTPUT%"
    echo ============================== >> "%OUTPUT%"
    type "%%F" >> "%OUTPUT%"
    echo. >> "%OUTPUT%"
)

echo DONE. Source dumped to %OUTPUT%
pause
