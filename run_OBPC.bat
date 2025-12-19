@echo off
title Sistema OBPC - Igreja O Brasil para Cristo
color 0B
cls

echo ==========================================
echo  SISTEMA OBPC - O BRASIL PARA CRISTO
echo  Tiete/SP - Sistema Administrativo
echo ==========================================
echo.

REM Verifica se o ambiente virtual existe
if not exist "venv\" (
    echo ❌ Sistema nao instalado!
    echo.
    echo Execute primeiro o 'install_OBPC.bat' para instalar.
    echo.
    pause
    exit /b 1
)

echo 🚀 Iniciando Sistema OBPC...
echo.

REM Ativa ambiente virtual
call venv\Scripts\activate

REM Inicia o sistema
python run.py

pause