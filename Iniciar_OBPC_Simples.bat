@echo off
title Sistema OBPC - Igreja O Brasil Para Cristo
color 0A

cls
echo.
echo ==========================================
echo     SISTEMA OBPC - EXECUTAR APLICACAO
echo ==========================================
echo     O Brasil Para Cristo - Tietê/SP
echo     Versão 2025 - Sistema em Produção
echo ==========================================
echo.

:: Ir para o diretório do script
cd /d "%~dp0"

:: Verificar se run.py existe
if not exist "run.py" (
    echo ❌ Arquivo run.py não encontrado!
    echo Certifique-se de estar na pasta correta do sistema.
    pause
    exit /b 1
)

echo 🚀 Iniciando Sistema OBPC...
echo.
echo ⚠️ As mensagens sobre WeasyPrint são normais e não afetam o funcionamento.
echo.

:: Executar o sistema
"C:\Users\user\AppData\Local\Programs\Python\Python314\python.exe" run.py

:: Se chegou aqui, o sistema foi fechado
echo.
echo 🔄 Sistema encerrado.
pause