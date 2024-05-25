@echo off
echo.
echo ============================================
echo   Building V.I.X.E.V.I.A
echo ============================================
echo.

call .venv\Scripts\activate

if errorlevel 1 (
    echo Error activate virtual environment.
    pause
    exit /b
)

if exist "build\" (
    rmdir /s /q "build"
)

if exist "dist\" (
    rmdir /s /q "dist"
)

pyinstaller --noconfirm --collect-all so_vits_svc_fork main.py --add-data Chatbot.py;.

if errorlevel 1 (
    echo Error PyInstaller.
    pause
    deactivate
    exit /b
)

del /s /q *.spec
pause

deactivate

echo.
echo ============================================
echo   DONE!
echo ============================================
echo.
pause
