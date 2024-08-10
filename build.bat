@echo off
echo.
echo ============================================
echo Building V.I.X.E.V.I.A
echo ============================================
echo.

cd /d %~dp0

call .\venv\Scripts\activate
if errorlevel 1 (
    echo Error activating virtual environment.
    pause
    exit /b
)

if exist "build" (
    rmdir /s /q "build"
)

if exist "dist" (
    rmdir /s /q "dist"
)

PyInstaller src/main.py --noconfirm --noconsole --collect-all so_vits_svc_fork --icon=src/app/assets/app.ico --add-data src/Chatbot.py;.

if errorlevel 1 (
    echo Error running PyInstaller.
    pause
    deactivate
    exit /b
)

del /s /q *.spec
deactivate

echo.
echo ============================================
echo DONE!
echo ============================================
echo.
pause
