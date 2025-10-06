@echo off
title Sistema OBPC - Instalacao Rapida
color 0A

:: Configurar codificação para UTF-8
chcp 65001 >nul

cls
echo.
echo ========================================
echo    SISTEMA OBPC - INSTALACAO RAPIDA
echo ========================================
echo    O Brasil Para Cristo - Tiete/SP
echo ========================================
echo.

:: Verificar se Python está instalado
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python nao encontrado!
    echo.
    echo 📥 Por favor, instale Python 3.8+ antes de continuar:
    echo    https://www.python.org/downloads/
    echo.
    pause
    exit /b 1
)

echo ✅ Python encontrado
echo.

:: Verificar se é primeira execução
if not exist "instance\igreja.db" (
    echo 🚀 Primeira execucao detectada
    echo 📦 Iniciando instalacao automatica...
    echo.
) else (
    echo 🔄 Sistema ja configurado
    echo 🚀 Iniciando aplicacao...
    echo.
)

:: Executar instalador rápido
echo ⏳ Carregando interface...
python instalador_rapido.py

:: Se chegou até aqui, verificar se deu erro
if errorlevel 1 (
    echo.
    echo ❌ Erro durante a execucao
    echo 💡 Tente executar: python run.py
    echo.
    pause
)

:: Finalizar
echo.
echo ✅ Processo concluido
echo 🌐 Acesse: http://localhost:5000
echo.
echo Pressione qualquer tecla para sair...
pause >nul