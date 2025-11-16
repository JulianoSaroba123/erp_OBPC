#!/usr/bin/env python3
"""
Criador de atalho na área de trabalho para o Sistema OBPC
"""

import os
import sys
from pathlib import Path
import winshell
from win32com.client import Dispatch

def criar_atalho_desktop():
    """Cria atalho na área de trabalho"""
    try:
        # Caminho do sistema
        sistema_dir = Path(__file__).parent.absolute()
        executar_bat = sistema_dir / "ExecutarOBPC.bat"
        
        # Verificar se arquivo existe
        if not executar_bat.exists():
            print(f"❌ Arquivo não encontrado: {executar_bat}")
            return False
        
        # Área de trabalho
        desktop = winshell.desktop()
        
        # Criar atalho
        shell = Dispatch('WScript.Shell')
        atalho_path = os.path.join(desktop, "Sistema OBPC.lnk")
        atalho = shell.CreateShortCut(atalho_path)
        
        # Configurar atalho para executar o arquivo .bat
        atalho.Targetpath = str(executar_bat)
        atalho.Arguments = ""
        atalho.WorkingDirectory = str(sistema_dir)
        atalho.IconLocation = str(sistema_dir / "static" / "logo_obpc.ico") if (sistema_dir / "static" / "logo_obpc.ico").exists() else ""
        atalho.Description = "Sistema OBPC - Igreja O Brasil Para Cristo - Executar Aplicação"
        
        # Salvar atalho
        atalho.save()
        
        print("✅ Atalho criado na área de trabalho!")
        print(f"📂 Local: {atalho_path}")
        print("🎯 Nome: Sistema OBPC.lnk")
        print("🚀 Executa: ExecutarOBPC.bat")
        
        return True
        
    except ImportError:
        print("❌ Bibliotecas necessárias não encontradas!")
        print("💡 Execute: pip install winshell pywin32")
        return False
    except Exception as e:
        print(f"❌ Erro ao criar atalho: {str(e)}")
        return False

def criar_atalho_alternativo():
    """Cria atalho usando arquivo .bat (alternativa)"""
    try:
        # Caminho do sistema
        sistema_dir = Path(__file__).parent.absolute()
        
        # Área de trabalho
        desktop = Path.home() / "Desktop"
        if not desktop.exists():
            desktop = Path.home() / "Área de Trabalho"
        
        # Criar arquivo .bat
        bat_content = f"""@echo off
cd /d "{sistema_dir}"
python iniciar_obpc_silencioso.py
pause"""
        
        atalho_bat = desktop / "Sistema OBPC.bat"
        with open(atalho_bat, 'w', encoding='utf-8') as f:
            f.write(bat_content)
        
        print("✅ Atalho .bat criado na área de trabalho!")
        print(f"📂 Local: {atalho_bat}")
        print("🎯 Nome: Sistema OBPC.bat")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro ao criar atalho .bat: {str(e)}")
        return False

if __name__ == "__main__":
    print("🖥️ CRIANDO ATALHO NA ÁREA DE TRABALHO")
    print("="*40)
    
    # Tentar criar atalho .lnk primeiro
    if not criar_atalho_desktop():
        print("\n🔄 Tentando método alternativo...")
        criar_atalho_alternativo()
    
    print("\n✅ CONCLUÍDO!")
    input("Pressione Enter para continuar...")