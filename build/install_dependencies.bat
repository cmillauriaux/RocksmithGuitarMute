@echo off
REM Script d'installation des dépendances - RockSmith Guitar Mute

echo ==========================================
echo   Installation des dépendances
echo   RockSmith Guitar Mute
echo ==========================================
echo.

REM Vérifier si Python est installé
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python n'est pas installé ou pas dans le PATH
    echo Veuillez installer Python 3.8+ depuis https://python.org
    pause
    exit /b 1
)

echo ✅ Python détecté
python --version
echo.

REM Mettre à jour pip
echo 📦 Mise à jour de pip...
python -m pip install --upgrade pip
echo.

REM Installer les dépendances de base
echo 📦 Installation des dépendances de base...
pip install -r requirements.txt
echo.

REM Vérifier si CUDA est disponible
echo 🔍 Vérification du support CUDA...
python -c "import torch; print('CUDA disponible:', torch.cuda.is_available()); print('Nombre de GPUs:', torch.cuda.device_count() if torch.cuda.is_available() else 0)"
echo.

REM Proposer l'installation de CUDA si pas détecté
python -c "import torch; exit(0 if torch.cuda.is_available() else 1)" >nul 2>&1
if errorlevel 1 (
    echo ⚠️  CUDA non détecté. Le traitement utilisera le CPU.
    echo Pour accélérer le traitement avec un GPU NVIDIA:
    echo 1. Installez CUDA Toolkit depuis https://developer.nvidia.com/cuda-toolkit
    echo 2. Réinstallez PyTorch avec: pip install torch torchaudio --index-url https://download.pytorch.org/whl/cu118
    echo.
) else (
    echo ✅ Support CUDA détecté! Le GPU sera utilisé pour accélérer le traitement.
    echo.
)

echo ✅ Installation terminée!
echo.
echo 💡 Pour lancer l'interface graphique:
echo    - Double-cliquez sur launch_gui.bat
echo    - Ou exécutez: python launch_gui.py
echo.
echo 💡 Pour compiler un exécutable standalone:
echo    - Exécutez: python build_windows.py
echo.
pause
