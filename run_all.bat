@echo off
SETLOCAL EnableDelayedExpansion
echo.
echo  =======================================================
echo   PhishHunter - Lanceur Global
echo  =======================================================
echo.

:: 1. Verification des dependances globales
echo [1/5] Verification de l'environnement systeme...

:: Check Docker
docker info >nul 2>&1
IF %ERRORLEVEL% NEQ 0 (
    echo [ERREUR] Docker n'est pas lance ou installe.
    echo Ouvrez Docker Desktop puis relancez ce script.
    pause
    exit /b 1
) ELSE (
    echo      - Docker OK.
)

:: Check Ollama
netstat -an | find ":11434" >nul 2>&1
IF %ERRORLEVEL% NEQ 0 (
    echo      - Ollama absent, lancement en arriere-plan...
    start /min cmd /c "ollama serve"
    timeout /t 3 >nul
) ELSE (
    echo      - Ollama OK.
)

:: Check Python
python --version >nul 2>&1
IF %ERRORLEVEL% NEQ 0 (
    echo [ERREUR] Python n'est pas installe ou pas dans le PATH.
    pause
    exit /b 1
) ELSE (
    echo      - Python OK.
)


:: 2. Installation des dependances Python si manquantes
echo.
echo [2/5] Verification des dependances Python...
python -m pip show flask >nul 2>&1
IF %ERRORLEVEL% NEQ 0 (
    echo      Installation des dependances...
    python -m pip install -r "%~dp0requirements.txt" >nul 2>&1
) ELSE (
    echo      - Dependances Python OK.
)


:: 3. Rebuild de l'image Docker (toujours, pour integrer les derniers changements)
echo.
echo [3/5] Rebuild de l'image Docker PhishHunter...
echo      ^(inclut les derniers changements de code^)
cd "%~dp0"
docker compose build analyzer
IF %ERRORLEVEL% NEQ 0 (
    echo [ERREUR] Echec du build Docker.
    pause
    exit /b 1
)
echo      - Image Docker a jour.


:: 4. Demarrage du conteneur Docker (VNC + NoVNC)
echo.
echo [4/5] Demarrage du conteneur PhishHunter ^(VNC + analyseur^)...
cd "%~dp0"
docker compose up -d analyzer
IF %ERRORLEVEL% NEQ 0 (
    echo [ERREUR] Impossible de demarrer le conteneur Docker.
    pause
    exit /b 1
)
echo      - Conteneur demarre.
echo      - NoVNC : http://localhost:6080/
echo      - Attendez quelques secondes que VNC soit pret...
timeout /t 4 >nul


:: 5. Lancement de l'interface graphique Web
echo.
echo [5/5] Lancement du serveur Web PhishHunter...
echo.
echo  =======================================================
echo   Interface GUI : http://localhost:5000
echo   Interface VNC : http://localhost:6080/
echo   Ctrl+C pour arreter le serveur GUI.
echo   Arreter le conteneur : docker compose down
echo  =======================================================
echo.

cd "%~dp0"
python "gui\app.py"

ENDLOCAL
