@echo off
title Sistema OBPC - Inicializacao Silenciosa
color 0B
chcp 65001 >nul

cls
echo.
echo ==========================================
echo    SISTEMA OBPC - MODO SILENCIOSO
echo ==========================================
echo     O Brasil Para Cristo - Tietê/SP
echo     Executando sem console visível...
echo ==========================================
echo.

:: Verificar se Python está instalado
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python não encontrado!
    echo.
    echo 💡 Instale o Python e tente novamente
    pause
    exit /b 1
)

:: Verificar se o executável existe
if not exist "executavel_profissional.py" (
    echo ❌ Executável profissional não encontrado!
    pause
    exit /b 1
)

echo ✅ Iniciando sistema em modo silencioso...
echo ⏳ Tela de carregamento será exibida
echo 🌐 Sistema abrirá automaticamente no navegador
echo.
echo 📋 Para encerrar: Feche o navegador e pressione Ctrl+C
echo.

:: Executar usando pythonw (sem console)
start /min "" pythonw executavel_profissional.py

:: Aguardar um pouco e sair
timeout /t 3 >nul
echo ✅ Sistema iniciado!
echo.
echo 🔍 Se não abrir automaticamente, acesse:
echo    http://127.0.0.1:5000
echo.
pause
