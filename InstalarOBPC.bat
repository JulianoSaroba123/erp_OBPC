@echo off
title Sistema OBPC - Instalador Completo
color 0A

:: Configurar codificação para UTF-8
chcp 65001 >nul

cls
echo.
echo ==========================================
echo    SISTEMA OBPC - INSTALADOR COMPLETO
echo ==========================================
echo    O Brasil Para Cristo - Tietê/SP
echo    Versão 2025 - Instalação Automática
echo ==========================================
echo.

:: Verificar se Python está instalado
echo 🔍 Verificando dependências...
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python não encontrado!
    echo.
    echo 📥 INSTALAÇÃO NECESSÁRIA:
    echo    1. Baixe Python 3.8+ em: https://www.python.org/downloads/
    echo    2. Durante instalação, marque "Add Python to PATH"
    echo    3. Execute este instalador novamente
    echo.
    echo 🌐 Abrindo página de download...
    start https://www.python.org/downloads/
    pause
    exit /b 1
)

echo ✅ Python encontrado
echo.

:: Verificar se é primeira execução ou precisa reinstalar
if not exist "instance\igreja.db" (
    echo 🚀 PRIMEIRA INSTALAÇÃO DETECTADA
    echo 📦 Iniciando configuração completa do sistema...
    echo.
    echo ⏳ Iniciando instalador profissional...
    python instalador_profissional.py
) else (
    echo 🔄 Sistema já instalado anteriormente
    echo �️ Verificando atualizações e dependências...
    echo.
    echo ⏳ Executando verificação...
    python instalador_gui.py
)

:: Verificar resultado da instalação
if errorlevel 1 (
    echo.
    echo ❌ Erro durante a instalação
    echo 💡 SOLUÇÕES:
    echo    1. Execute como Administrador
    echo    2. Verifique conexão com internet
    echo    3. Tente: python run.py
    echo.
    echo 📋 Para suporte: github.com/obpc-tietê
    pause
    exit /b 1
)

:: Finalizar com sucesso
echo.
echo ✅ INSTALAÇÃO CONCLUÍDA COM SUCESSO!
echo.
echo 🌐 Para usar o sistema:
echo    • Execute: ExecutarOBPC.bat
echo    • Ou acesse: http://localhost:5000
echo.
echo 🔑 Login padrão:
echo    Email: admin@obpc.com
echo    Senha: 123456
echo.
echo Pressione qualquer tecla para finalizar...
pause >nul