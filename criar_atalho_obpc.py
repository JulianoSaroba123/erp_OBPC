#!/usr/bin/env python3
"""
Criador de Atalho Desktop para Sistema OBPC
Cria um atalho elegante no desktop que inicia o sistema automaticamente
"""

import os
import sys
from pathlib import Path
import winshell
from win32com.client import Dispatch

def criar_atalho_desktop():
    """Cria atalho no desktop para o Sistema OBPC"""
    
    try:
        # Caminhos
        sistema_dir = Path(__file__).parent
        bat_file = sistema_dir / "OBPC_Sistema_Automatico.bat"
        vbs_file = sistema_dir / "Sistema_OBPC_Invisivel.vbs"
        
        # Desktop do usuário
        desktop = winshell.desktop()
        
        # Nome do atalho
        atalho_nome = "Sistema OBPC - Igreja"
        atalho_path = os.path.join(desktop, f"{atalho_nome}.lnk")
        
        # Criar atalho
        shell = Dispatch('WScript.Shell')
        shortcut = shell.CreateShortCut(atalho_path)
        
        # Configurar atalho para usar VBS (invisível)
        if vbs_file.exists():
            shortcut.Targetpath = str(vbs_file)
            shortcut.Arguments = ""
            shortcut.Description = "Sistema OBPC - Igreja O Brasil Para Cristo (Inicia automaticamente)"
        else:
            shortcut.Targetpath = str(bat_file)
            shortcut.Arguments = ""
            shortcut.Description = "Sistema OBPC - Igreja O Brasil Para Cristo"
        
        shortcut.WorkingDirectory = str(sistema_dir)
        
        # Tentar usar ícone personalizado se existir
        icone_path = sistema_dir / "obpc_icon.ico"
        if icone_path.exists():
            shortcut.IconLocation = str(icone_path)
        
        # Salvar atalho
        shortcut.save()
        
        print(f"✅ Atalho criado com sucesso!")
        print(f"📍 Local: {atalho_path}")
        print(f"🎯 Nome: {atalho_nome}")
        print(f"📁 Diretório: {sistema_dir}")
        
        return True
        
    except ImportError:
        print("❌ Bibliotecas necessárias não encontradas!")
        print("Execute: pip install winshell pywin32")
        return False
        
    except Exception as e:
        print(f"❌ Erro ao criar atalho: {str(e)}")
        return False

def main():
    """Função principal"""
    print("🖥️ Criador de Atalho - Sistema OBPC")
    print("=" * 40)
    
    if not sys.platform.startswith('win'):
        print("❌ Este script funciona apenas no Windows!")
        return
    
    sucesso = criar_atalho_desktop()
    
    if sucesso:
        print("\n🎉 Atalho criado com sucesso!")
        print("🖱️ Clique duplo no atalho para abrir o sistema")
        print("✨ O sistema abrirá automaticamente no navegador")
    else:
        print("\n❌ Não foi possível criar o atalho")
    
    input("\nPressione Enter para sair...")

if __name__ == "__main__":
    main()