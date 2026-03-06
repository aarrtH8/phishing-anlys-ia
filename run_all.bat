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
    echo [ATTENTION] Docker ne semble pas etre lance ou installe.
    echo Assurez-vous d'avoir ouvert Docker Desktop.
    echo.
    set /p "WAIT=Appuyez sur Entree pour continuer quand meme..."
) ELSE (
    echo      - Docker detecte.
)

:: Check Ollama
netstat -an | find ":11434" >nul 2>&1
IF %ERRORLEVEL% NEQ 0 (
    echo [ATTENTION] Ollama ne tourne pas sur le port 11434.
    echo Lancement d'Ollama en arriere-plan...
    start /min cmd /c "ollama serve"
    timeout /t 3 >nul
) ELSE (
    echo      - Ollama detecte.
)

:: Check Python
python --version >nul 2>&1
IF %ERRORLEVEL% NEQ 0 (
    echo [ERREUR] Python n'est pas installe ou pas dans le PATH.
    pause
    exit /b 1
) ELSE (
    echo      - Python detecte.
)


:: 2. Installation des dependances Python si manquantes
echo.
echo [2/5] Verification des dependances Python...
python -m pip show flask >nul 2>&1
IF %ERRORLEVEL% NEQ 0 (
    echo      Installation des bibliotheques manquantes...
    python -m pip install -r "%~dp0requirements.txt" >nul 2>&1
) ELSE (
    echo      - Dependances Python OK.
)


:: 3. Construction de l'image Docker si necessaire
echo.
echo [3/5] Verification de l'image Docker PhishHunter...
docker images -q phish-hunter-visual >nul 2>&1
docker compose -f "%~dp0docker-compose.yml" images -q analyzer 2>nul | findstr /r "." >nul
IF %ERRORLEVEL% NEQ 0 (
    echo      - Construction de l'image Docker ^(premiere fois, peut prendre quelques minutes^)...
    cd "%~dp0"
    docker compose build analyzer
    IF %ERRORLEVEL% NEQ 0 (
        echo [ERREUR] Echec de la construction Docker.
        pause
        exit /b 1
    )
) ELSE (
    echo      - Image Docker OK.
)


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
echo      - Interface VNC: http://localhost:6080/
echo      - Pour voir le navigateur en temps reel, ouvrez l'URL ci-dessus.


:: 5. Lancement de l'interface graphique Web
echo.
echo [5/5] Lancement du serveur Web PhishHunter...
echo.
echo  =======================================================
echo   Interface GUI : http://localhost:5000
echo   Interface VNC : http://localhost:6080/
echo   Appuyez sur Ctrl+C pour arreter le serveur GUI.
echo   Pour arreter le conteneur: docker compose down
echo  =======================================================
echo.

cd "%~dp0"
python "gui\app.py"

ENDLOCAL
