@echo off
:: Executar Sistema OBPC sem mostrar console
cd /d "%~dp0"

:: Verificar se está na pasta correta
if not exist "run.py" (
    echo Sistema nao encontrado!
    pause
    exit
)

:: Iniciar o sistema em background sem console
start /min "" python run.py

:: Aguardar um pouco para o servidor iniciar
timeout /t 3 /nobreak >nul

:: Abrir navegador automaticamente
start "" "http://127.0.0.1:5000"

:: Sair sem mostrar console
exit