@echo off
SETLOCAL EnableDelayedExpansion
echo.
echo  =======================================================
echo   PhishHunter - Lanceur Global (Serveur + Environnement)
echo  =======================================================
echo.

:: 1. Verification des dependances globales
echo [1/4] Verification de l'environnement systeme...

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

:: Ensure llava model is present
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


:: 2. Installation des dependances Python s'il en manque
echo.
echo [2/4] Verification des dependances Python...
python -m pip show flask >nul 2>&1
IF %ERRORLEVEL% NEQ 0 (
    echo      Installation de Flask et autres bibliotheques manquantes...
    python -m pip install -r "%~dp0requirements.txt" >nul 2>&1
) ELSE (
    echo      - Flask et dependances OK.
)


:: 3. Construction de l'image Docker si necessaire
echo.
echo [3/4] Verification de l'image Docker PhishHunter...
docker images -q projet_mace-analyzer >nul 2>&1
IF %ERRORLEVEL% NEQ 0 (
    echo      - L'image n'existe pas encore.
    echo      - Lancement de la construction de l'image ^(cela peut prendre du temps^)...
    cd "%~dp0"
    docker compose build analyzer
) ELSE (
    echo      - Image Docker OK.
)


:: 4. Lancement de l'interface graphique
echo.
echo [4/4] Lancement du serveur Web PhishHunter...
echo.
echo  =======================================================
echo   Ouvrez votre navigateur : http://localhost:5000
echo   Appuyez sur Ctrl+C dans cette fenetre pour tout arreter
echo  =======================================================
echo.

cd "%~dp0"
python "gui\app.py"

ENDLOCAL
