@echo off
SETLOCAL EnableDelayedExpansion

:: Force consistent Docker Compose project name so image is always "phishhunter-analyzer"
SET COMPOSE_PROJECT_NAME=phishhunter

echo.
echo  =======================================================
echo   PhishHunter - Lanceur Global (Serveur + Environnement)
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

:: Ensure llava model is present (needed for CAPTCHA solving)
echo      - Verification du modele Vision "llava" ^(pour les CAPTCHAs^)...
ollama list | find "llava" >nul 2>&1
IF %ERRORLEVEL% NEQ 0 (
    echo [INFO] Telechargement du modele 'llava' ^(peut prendre du temps la 1ere fois^)...
    ollama pull llava
) ELSE (
    echo      - Modele 'llava' trouve.
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
    echo      Installation de Flask et autres bibliotheques manquantes...
    python -m pip install -r "%~dp0requirements.txt" >nul 2>&1
) ELSE (
    echo      - Flask et dependances OK.
)


:: 3. Construction de l'image Docker si necessaire
echo.
echo [3/5] Verification de l'image Docker PhishHunter...

:: Correct check: docker images -q returns empty string (not error) when image is absent
FOR /F "tokens=*" %%I IN ('docker images -q phishhunter-analyzer 2^>nul') DO SET DOCKER_IMAGE_ID=%%I
IF "!DOCKER_IMAGE_ID!"=="" (
    echo      - Image introuvable, lancement de la construction...
    echo      - (Cela peut prendre 5-10 minutes la premiere fois)
    cd "%~dp0"
    docker compose build analyzer
    IF %ERRORLEVEL% NEQ 0 (
        echo [ERREUR] La construction de l'image Docker a echoue.
        pause
        exit /b 1
    )
    echo      - Image construite avec succes.
) ELSE (
    echo      - Image Docker OK ^(!DOCKER_IMAGE_ID!^).
)


:: 4. Verification du port 5000
echo.
echo [4/5] Verification du port 5000...
netstat -an | find ":5000 " | find "LISTEN" >nul 2>&1
IF %ERRORLEVEL% EQU 0 (
    echo [ATTENTION] Le port 5000 est deja utilise.
    echo      Une instance de PhishHunter est peut-etre deja en cours d'execution.
    echo      Ouvrez http://localhost:5000 dans votre navigateur.
    echo.
    start "" "http://localhost:5000"
    pause
    exit /b 0
) ELSE (
    echo      - Port 5000 libre.
)


:: 5. Lancement de l'interface graphique
echo.
echo [5/5] Lancement du serveur Web PhishHunter...
echo.
echo  =======================================================
echo   Ouverture automatique de : http://localhost:5000
echo   Appuyez sur Ctrl+C dans cette fenetre pour tout arreter
echo  =======================================================
echo.

cd "%~dp0"

:: Open browser after a short delay (let Flask start first)
start /b cmd /c "timeout /t 2 >nul && start http://localhost:5000"

:: Start Flask server (blocks until Ctrl+C)
python "gui\app.py"

ENDLOCAL
