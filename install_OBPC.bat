@echo off
title Instalador do Sistema OBPC - Igreja O Brasil para Cristo
color 1F
cls

echo ==========================================
echo  INSTALADOR AUTOMATICO - SISTEMA OBPC
echo  Igreja O Brasil para Cristo - Tiete/SP
echo ==========================================
echo.
echo Preparando instalacao automatica...
echo.

REM Verifica se Python está instalado
echo [1/6] Verificando Python...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo.
    echo ❌ ERRO: Python nao encontrado!
    echo.
    echo 📋 Para instalar o sistema OBPC, voce precisa:
    echo    1. Baixar Python 3.10 ou superior em: https://python.org
    echo    2. Durante a instalacao, marque "Add Python to PATH"
    echo    3. Execute este instalador novamente
    echo.
    pause
    exit /b 1
)
echo ✅ Python encontrado!

REM Verifica se já existe ambiente virtual
echo [2/6] Verificando ambiente virtual...
if exist "venv\" (
    echo ⚠️  Ambiente virtual ja existe. Removendo...
    rmdir /s /q venv
)

REM Cria ambiente virtual
echo [3/6] Criando ambiente virtual...
python -m venv venv
if %errorlevel% neq 0 (
    echo ❌ Erro ao criar ambiente virtual!
    pause
    exit /b 1
)
echo ✅ Ambiente virtual criado!

REM Ativa ambiente virtual
echo [4/6] Ativando ambiente virtual...
call venv\Scripts\activate
if %errorlevel% neq 0 (
    echo ❌ Erro ao ativar ambiente virtual!
    pause
    exit /b 1
)
echo ✅ Ambiente virtual ativado!

REM Atualiza pip
echo [5/6] Atualizando pip...
python -m pip install --upgrade pip --quiet

REM Instala dependências
echo [6/6] Instalando dependencias do Sistema OBPC...
echo      (Isso pode demorar alguns minutos...)
pip install -r requirements.txt --quiet
if %errorlevel% neq 0 (
    echo ❌ Erro ao instalar dependencias!
    echo.
    echo 🔧 Tentativas de solucao:
    echo    1. Verifique sua conexao com a internet
    echo    2. Execute como Administrador
    echo    3. Desative temporariamente o antivirus
    echo.
    pause
    exit /b 1
)

echo.
echo ==========================================
echo ✅ INSTALACAO CONCLUIDA COM SUCESSO!
echo ==========================================
echo.
echo 🎉 O Sistema OBPC foi instalado com sucesso!
echo.
echo 📂 Proximos passos:
echo    1. Execute 'run_OBPC.bat' para iniciar o sistema
echo    2. Ou execute 'build_EXE.bat' para gerar executavel
echo.
echo 🌐 O sistema sera aberto automaticamente no navegador
echo    em: http://127.0.0.1:5000
echo.
echo 🔐 Login inicial:
echo    Usuario: admin
echo    Senha: admin123
echo.
echo 📞 Suporte: Sistema desenvolvido para OBPC Tiete/SP
echo.
pause