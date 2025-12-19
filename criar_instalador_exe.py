#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para criar o executável do instalador OBPC
"""

import subprocess
import sys
import os
from pathlib import Path

def install_pyinstaller():
    """Instala PyInstaller se não estiver instalado"""
    try:
        import PyInstaller
        print("✅ PyInstaller já está instalado")
    except ImportError:
        print("📦 Instalando PyInstaller...")
        subprocess.run([sys.executable, "-m", "pip", "install", "pyinstaller"], check=True)
        print("✅ PyInstaller instalado com sucesso")

def create_installer_exe():
    """Cria o executável do instalador"""
    print("🔨 Criando executável do instalador...")
    
    # Comandos do PyInstaller
    cmd = [
        "pyinstaller",
        "--onefile",                    # Um único arquivo
        "--windowed",                   # Sem console
        "--name=InstaladorOBPC",        # Nome do executável
        "--icon=static/logo_obpc.ico",  # Ícone (se existir)
        "--add-data=app;app",           # Incluir pasta app
        "--add-data=static;static",     # Incluir pasta static
        "--add-data=run.py;.",          # Incluir arquivos principais
        "--add-data=requirements.txt;.",
        "--add-data=criar_admin.py;.",
        "--add-data=verificar_banco.py;.",
        "instalador_gui.py"
    ]
    
    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        print("✅ Executável criado com sucesso!")
        print(f"📁 Local: {Path.cwd() / 'dist' / 'InstaladorOBPC.exe'}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Erro ao criar executável: {e}")
        print(f"Saída: {e.stdout}")
        print(f"Erro: {e.stderr}")
        return False

def create_simple_installer():
    """Cria instalador simples sem dependências externas"""
    print("🔨 Criando instalador simples...")
    
    cmd = [
        "pyinstaller",
        "--onefile",
        "--console",  # Com console para debug
        "--name=InstaladorOBPC_Simple",
        "instalador_gui.py"
    ]
    
    try:
        subprocess.run(cmd, check=True)
        print("✅ Instalador simples criado!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Erro: {e}")
        return False

def create_portable_package():
    """Cria um pacote portável"""
    print("📦 Criando pacote portável...")
    
    import zipfile
    import shutil
    
    # Criar pasta temporária
    package_dir = Path("OBPC_Instalador_Portatil")
    if package_dir.exists():
        shutil.rmtree(package_dir)
    package_dir.mkdir()
    
    # Copiar arquivos essenciais
    files_to_copy = [
        "instalador_gui.py",
        "app/",
        "static/",
        "run.py",
        "requirements.txt",
        "criar_admin.py",
        "verificar_banco.py"
    ]
    
    for item in files_to_copy:
        source = Path(item)
        if source.exists():
            if source.is_file():
                shutil.copy2(source, package_dir / source.name)
            else:
                shutil.copytree(source, package_dir / source.name)
    
    # Criar script de execução
    run_script = f'''@echo off
echo ========================================
echo    Instalador OBPC - Sistema de Gestao
echo ========================================
echo.
echo Iniciando instalador...
echo.
python instalador_gui.py
if errorlevel 1 (
    echo.
    echo Erro: Python nao encontrado!
    echo Instale Python 3.8+ antes de continuar
    echo.
    pause
)
'''
    
    with open(package_dir / "Instalar.bat", 'w', encoding='utf-8') as f:
        f.write(run_script)
    
    # Criar README
    readme = '''SISTEMA OBPC - INSTALADOR
==========================

REQUISITOS:
- Python 3.8 ou superior
- Windows 7/10/11

INSTALAÇÃO:
1. Execute "Instalar.bat"
2. Siga as instruções na tela
3. Aguarde a conclusão

SUPORTE:
Igreja O Brasil Para Cristo - Tietê/SP
'''
    
    with open(package_dir / "LEIA-ME.txt", 'w', encoding='utf-8') as f:
        f.write(readme)
    
    # Criar ZIP
    zip_name = "OBPC_Instalador_Completo.zip"
    with zipfile.ZipFile(zip_name, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(package_dir):
            for file in files:
                file_path = Path(root) / file
                arc_path = file_path.relative_to(package_dir)
                zipf.write(file_path, arc_path)
    
    print(f"✅ Pacote portável criado: {zip_name}")
    return True

def main():
    """Função principal"""
    print("🚀 GERADOR DE INSTALADOR OBPC")
    print("=" * 40)
    
    print("\nEscolha uma opção:")
    print("1. Executável com PyInstaller (recomendado)")
    print("2. Executável simples")
    print("3. Pacote portável (ZIP)")
    print("4. Todos os tipos")
    
    choice = input("\nDigite sua escolha (1-4): ").strip()
    
    if choice == "1":
        install_pyinstaller()
        create_installer_exe()
    elif choice == "2":
        install_pyinstaller()
        create_simple_installer()
    elif choice == "3":
        create_portable_package()
    elif choice == "4":
        install_pyinstaller()
        create_installer_exe()
        create_simple_installer()
        create_portable_package()
    else:
        print("❌ Opção inválida!")
        return
    
    print("\n✅ Processo concluído!")
    print("\n📁 Verifique as pastas 'dist' e raiz do projeto")
    input("\nPressione Enter para sair...")

if __name__ == "__main__":
    main()