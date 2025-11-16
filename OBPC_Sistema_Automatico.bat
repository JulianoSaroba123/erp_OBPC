@echo off
title Sistema OBPC - Iniciando...
cd /d "%~dp0"

rem Verificar se Python está instalado
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python nao encontrado! Instale o Python primeiro.
    pause
    exit /b 1
)

rem Iniciar sistema automaticamente
python iniciar_obpc_automatico.py

rem Fechar janela automaticamente após sucesso
exit