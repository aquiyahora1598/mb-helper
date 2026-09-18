@echo off
title MB Helper (100%% Legal Steam)
cd /d "%~dp0"
echo ===================================================
echo                  MB HELPER
echo     Lector Optico y de Memoria 100%% Legal en Steam
echo ===================================================
echo.
echo Iniciando interfaz grafica...
python phantom_gui.py
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo Ocurrio un error al iniciar. Presiona cualquier tecla para salir...
    pause >nul
)
