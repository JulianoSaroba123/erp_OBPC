@echo off
title Gerador de Executavel - Sistema OBPC
color 0A
cls

echo ==========================================
echo  GERADOR DE EXECUTAVEL - SISTEMA OBPC
echo  Igreja O Brasil para Cristo - Tiete/SP
echo ==========================================
echo.

REM Verifica se o ambiente virtual existe
if not exist "venv\" (
    echo ❌ Ambiente virtual nao encontrado!
    echo.
    echo Execute primeiro o 'install_OBPC.bat' para instalar as dependencias.
    echo.
    pause
    exit /b 1
)

echo [1/5] Ativando ambiente virtual...
call venv\Scripts\activate
if %errorlevel% neq 0 (
    echo ❌ Erro ao ativar ambiente virtual!
    pause
    exit /b 1
)
echo ✅ Ambiente virtual ativado!

echo [2/5] Verificando PyInstaller...
python -c "import PyInstaller" >nul 2>&1
if %errorlevel% neq 0 (
    echo ⚠️  PyInstaller nao encontrado. Instalando...
    pip install pyinstaller --quiet
)
echo ✅ PyInstaller disponivel!

echo [3/5] Limpando builds anteriores...
if exist "dist\" rmdir /s /q dist
if exist "build\" rmdir /s /q build
if exist "__pycache__\" rmdir /s /q __pycache__
if exist "*.spec" del /q *.spec
echo ✅ Arquivos temporarios removidos!

echo [4/5] Gerando executavel...
echo      (Isso pode demorar alguns minutos...)

REM Verifica se existe ícone
set ICON_PARAM=
if exist "static\logo_obpc.ico" (
    set ICON_PARAM=--icon=static\logo_obpc.ico
    echo 🎨 Usando icone personalizado da OBPC
) else (
    echo ⚠️  Icone nao encontrado, usando icone padrao
)

REM Gera o executável
pyinstaller --noconfirm --onefile --windowed ^
%ICON_PARAM% ^
--name="Sistema_OBPC" ^
--add-data="app;app" ^
--add-data="static;static" ^
--add-data="instance;instance" ^
--hidden-import="flask" ^
--hidden-import="flask_login" ^
--hidden-import="flask_sqlalchemy" ^
--hidden-import="reportlab" ^
--distpath="dist" ^
run.py

if %errorlevel% neq 0 (
    echo ❌ Erro ao gerar executavel!
    echo.
    echo 🔧 Solucoes possiveis:
    echo    1. Verifique se todos os arquivos estao presentes
    echo    2. Execute como Administrador
    echo    3. Desative temporariamente o antivirus
    echo.
    pause
    exit /b 1
)

echo [5/5] Finalizando...
if exist "build\" rmdir /s /q build
if exist "*.spec" del /q *.spec
echo ✅ Arquivos temporarios limpos!

echo.
echo ==========================================
echo ✅ EXECUTAVEL GERADO COM SUCESSO!
echo ==========================================
echo.
echo 🎉 O Sistema OBPC foi compilado com sucesso!
echo.
echo 📂 Arquivo gerado:
echo    📁 dist\Sistema_OBPC.exe
echo.
echo 🚀 Como usar:
echo    1. Copie a pasta 'dist' para qualquer computador
echo    2. Execute 'Sistema_OBPC.exe' diretamente
echo    3. O sistema abrira automaticamente no navegador
echo.
echo 💡 Dicas:
echo    ✓ Nao precisa instalar Python no computador de destino
echo    ✓ O executavel ja contem todas as dependencias
echo    ✓ Ideal para distribuir nas igrejas
echo.
echo 🔐 Login:
echo    Usuario: admin
echo    Senha: admin123
echo.
echo 📞 Sistema desenvolvido para OBPC Tiete/SP
echo.

REM Abre a pasta dist se o executável foi gerado
if exist "dist\Sistema_OBPC.exe" (
    echo Abrindo pasta de destino...
    start explorer dist
)

pause