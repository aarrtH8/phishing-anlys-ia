@echo off
SETLOCAL
echo.
echo  ===================================
echo   PhishHunter - Interface Graphique
echo  ===================================
echo.

:: Check Python
python --version >nul 2>&1
IF %ERRORLEVEL% NEQ 0 (
    echo [ERREUR] Python n'est pas installe ou pas dans le PATH.
    pause
    exit /b 1
)

:: Install Flask if needed
echo [1/2] Verification des dependances...
pip show flask >nul 2>&1
IF %ERRORLEVEL% NEQ 0 (
    echo      Installation de Flask...
    pip install flask
)

:: Launch GUI
echo [2/2] Lancement de l'interface...
echo.
echo  Ouvrez votre navigateur : http://localhost:5000
echo  (Ctrl+C pour arreter)
echo.

python "%~dp0gui\app.py"

ENDLOCAL
