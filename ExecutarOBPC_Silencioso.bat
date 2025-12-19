@echo off
:: Executar OBPC sem mostrar console
:: Para uso em produção ou como serviço

title Sistema OBPC - Modo Silencioso

:: Verificar se sistema está instalado
if not exist "instance\igreja.db" (
    echo Sistema nao instalado. Execute: InstalarOBPC.bat
    pause
    exit /b 1
)

:: Fechar qualquer instância anterior
taskkill /F /IM python.exe >nul 2>&1

:: Aguardar um momento
timeout /t 2 >nul

:: Iniciar em modo invisível (sem janela de console)
start /B pythonw iniciar_obpc_silencioso.py

:: Aguardar inicialização
timeout /t 5 >nul

:: Abrir navegador
start http://localhost:5000

:: Sair sem mostrar mensagem
exit