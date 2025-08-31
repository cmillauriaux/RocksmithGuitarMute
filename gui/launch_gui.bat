@echo off
REM Script de lancement pour Windows - RockSmith Guitar Mute GUI

echo ========================================
echo   RockSmith Guitar Mute - Interface
echo ========================================
echo.

REM Vérifier si Python est installé
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python n'est pas installé ou pas dans le PATH
    echo Veuillez installer Python 3.8+ depuis https://python.org
    echo.
    pause
    exit /b 1
)

echo ✅ Python détecté
python --version

REM Nettoyer les fichiers temporaires si nécessaire
if exist "__pycache__" (
    echo 🧹 Nettoyage des fichiers temporaires...
    rmdir /s /q "__pycache__" 2>nul
)

REM Lancer l'interface graphique
echo.
python launch_gui.py

REM Si l'interface se ferme normalement, pas de pause
REM Si erreur, le script launch_gui.py gère déjà la pause
