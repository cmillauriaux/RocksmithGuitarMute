@echo off
REM Script de nettoyage - RockSmith Guitar Mute

echo ========================================
echo   Nettoyage des fichiers temporaires
echo   RockSmith Guitar Mute
echo ========================================
echo.

echo 🧹 Suppression des fichiers temporaires...

REM Supprimer les dossiers de cache Python
if exist "__pycache__" (
    rmdir /s /q "__pycache__"
    echo   ✓ __pycache__ supprimé
)

REM Supprimer les fichiers .pyc
for /r %%i in (*.pyc) do (
    del "%%i" 2>nul
)
echo   ✓ Fichiers .pyc supprimés

REM Supprimer les dossiers de build
if exist "build" (
    rmdir /s /q "build"
    echo   ✓ Dossier build supprimé
)

if exist "dist" (
    rmdir /s /q "dist"
    echo   ✓ Dossier dist supprimé
)

REM Supprimer les fichiers .spec
del *.spec 2>nul
echo   ✓ Fichiers .spec supprimés

echo.
echo ✅ Nettoyage terminé!
echo.
echo 💡 Vous pouvez maintenant:
echo   - Lancer l'interface: launch_gui.bat
echo   - Recompiler: python build_windows.py
echo.
pause
