@echo off
:: Instalador OBPC sem console visível
title Sistema OBPC - Instalacao

:: Verificar se Python está instalado
python --version >nul 2>&1
if errorlevel 1 (
    echo Python nao encontrado! Instalando...
    :: Baixar e instalar Python silenciosamente
    powershell -Command "Invoke-WebRequest -Uri 'https://www.python.org/ftp/python/3.11.0/python-3.11.0-amd64.exe' -OutFile 'python_installer.exe'"
    python_installer.exe /quiet InstallAllUsers=1 PrependPath=1
    del python_installer.exe
)

:: Instalar o sistema
python instalador_gui.py

:: Fechar automaticamente
exit