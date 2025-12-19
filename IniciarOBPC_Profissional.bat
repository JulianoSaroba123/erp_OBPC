@echo off
title Sistema OBPC - Executavel Profissional
color 0B
chcp 65001 >nul

cls
echo.
echo ==========================================
echo    SISTEMA OBPC - EXECUTAVEL PROFISSIONAL
echo ==========================================
echo     O Brasil Para Cristo - Tietê/SP
echo     Versão 2025 - Executável Avançado
echo ==========================================
echo.

:: Verificar se Python está instalado
echo 🔍 Verificando Python...
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python não encontrado!
    echo.
    echo 💡 Instale o Python 3.7+ e execute:
    echo    InstalarOBPC.bat
    echo.
    pause
    exit /b 1
)

echo ✅ Python encontrado
echo.

:: Verificar se o executável profissional existe
if not exist "executavel_profissional.py" (
    echo ❌ Executável profissional não encontrado!
    echo.
    echo 💡 Arquivos necessários:
    echo    • executavel_profissional.py
    echo    • tela_carregamento.py
    echo    • utils_sistema.py
    echo.
    pause
    exit /b 1
)

echo ✅ Executável profissional encontrado
echo.

:: Verificar dependências básicas
echo 🔍 Verificando dependências...
python -c "import tkinter; import threading; import subprocess" >nul 2>&1
if errorlevel 1 (
    echo ❌ Dependências básicas não encontradas!
    echo.
    echo 💡 Execute: InstalarOBPC.bat
    pause
    exit /b 1
)

echo ✅ Dependências básicas OK
echo.

:: Iniciar o executável profissional
echo 🚀 Iniciando Sistema OBPC Profissional...
echo.
echo ⏳ Aguarde...
echo    • Tela de carregamento será exibida
echo    • Verificações automáticas serão executadas
echo    • Sistema abrirá no navegador automaticamente
echo.

:: Executar o sistema profissional
python executavel_profissional.py

:: Verificar se houve erro
if errorlevel 1 (
    echo.
    echo ❌ ERRO AO EXECUTAR SISTEMA PROFISSIONAL
    echo.
    echo 💡 SOLUÇÕES POSSÍVEIS:
    echo    1. Execute como Administrador
    echo    2. Reinstale com: InstalarOBPC.bat
    echo    3. Verifique se a porta 5000 está livre
    echo.
    echo 🔧 Tentando modo de compatibilidade...
    echo.
    
    :: Tentar com ExecutarOBPC.bat como fallback
    if exist "ExecutarOBPC.bat" (
        echo 🔄 Executando modo de compatibilidade...
        call ExecutarOBPC.bat
    ) else (
        echo ❌ Modo de compatibilidade não disponível
        echo.
        echo 📞 SUPORTE TÉCNICO:
        echo    • Verifique a instalação do Python
        echo    • Execute: InstalarOBPC.bat
        echo    • Contate o suporte se o problema persistir
    )
)

echo.
echo 📋 SISTEMA EXECUTADO
echo.
echo ✨ Obrigado por usar o Sistema OBPC!
echo 🌐 O Brasil Para Cristo - Tietê/SP
echo.
pause
