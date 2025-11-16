@echo off
title Sistema OBPC - Executar Aplicacao
color 0A

:: Configurar codificação para UTF-8
chcp 65001 >nul

cls
echo.
echo ==========================================
echo     SISTEMA OBPC - EXECUTAR APLICACAO
echo ==========================================
echo     O Brasil Para Cristo - Tietê/SP
echo     Versão 2025 - Sistema em Produção
echo ==========================================
echo.

:: Verificar se Python está instalado
echo 🔍 Verificando dependências...
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python não encontrado!
    echo.
    echo 💡 Execute primeiro: InstalarOBPC.bat
    echo.
    pause
    exit /b 1
)

echo ✅ Python encontrado
echo.

:: Verificar se sistema está instalado
if not exist "instance\igreja.db" (
    echo ⚠️  SISTEMA NÃO INSTALADO
    echo.
    echo 📦 Para instalar o sistema:
    echo    Execute: InstalarOBPC.bat
    echo.
    echo 🔄 Executando instalador agora...
    call InstalarOBPC.bat
    exit /b 0
)

echo ✅ Sistema instalado e configurado
echo.

:: Verificar se há servidor rodando
echo 🌐 Verificando se servidor já está ativo...
curl -s http://localhost:5000 >nul 2>&1
if not errorlevel 1 (
    echo ✅ Servidor já está rodando!
    echo.
    echo 🌐 Abrindo sistema no navegador...
    start http://localhost:5000
    echo.
    echo 📋 LOGIN PADRÃO:
    echo    Email: admin@obpc.com
    echo    Senha: 123456
    echo.
    echo ❓ Deseja reiniciar o servidor? (S/N)
    set /p restart="Resposta: "
    if /i "%restart%"=="S" (
        echo.
        echo 🔄 Reiniciando servidor...
        taskkill /F /IM python.exe >nul 2>&1
        timeout /t 2 >nul
    ) else (
        echo.
        echo 📌 Servidor continua em execução
        echo ✨ Sistema disponível em: http://localhost:5000
        pause
        exit /b 0
    )
)

:: Iniciar o servidor
echo 🚀 Iniciando servidor OBPC...
echo.
echo ⏳ Por favor, aguarde...
echo    • Carregando módulos...
echo    • Configurando banco de dados...
echo    • Preparando interface web...
echo.

:: Usar o arquivo de inicialização silenciosa se existir
if exist "iniciar_obpc_silencioso.py" (
    echo 🔇 Modo silencioso detectado
    python iniciar_obpc_silencioso.py
) else (
    echo 📢 Iniciando em modo padrão
    python run.py
)

:: Verificar se iniciou corretamente
if errorlevel 1 (
    echo.
    echo ❌ ERRO AO INICIAR SERVIDOR
    echo.
    echo 💡 SOLUÇÕES POSSÍVEIS:
    echo    1. Porta 5000 pode estar ocupada
    echo    2. Execute como Administrador
    echo    3. Reinstale com: InstalarOBPC.bat
    echo.
    echo 🔧 Tentando iniciar em porta alternativa...
    set FLASK_RUN_PORT=5001
    python run.py
)

:: Se chegou até aqui sem erro
echo.
echo ✅ SERVIDOR INICIADO COM SUCESSO!
echo.
echo 🌐 Sistema disponível em:
echo    • http://localhost:5000
echo    • http://127.0.0.1:5000
echo.
echo 🔑 LOGIN PADRÃO:
echo    Email: admin@obpc.com
echo    Senha: 123456
echo.
echo ⚠️  IMPORTANTE:
echo    • Mantenha esta janela aberta
echo    • Para parar: Ctrl+C ou feche a janela
echo    • Para acessar: Use qualquer navegador
echo.
echo 🌟 Sistema OBPC em execução...
echo.

:: Abrir automaticamente no navegador
timeout /t 3 >nul
start http://localhost:5000

:: Manter janela aberta mostrando status
:status_loop
echo.
echo ═══════════════════════════════════════════
echo 📊 STATUS DO SERVIDOR - %date% %time%
echo ═══════════════════════════════════════════
echo ✅ Sistema OBPC ativo
echo 🌐 URL: http://localhost:5000
echo 💻 Pressione Ctrl+C para parar
echo ═══════════════════════════════════════════
timeout /t 30 >nul
goto status_loop