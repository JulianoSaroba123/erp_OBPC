#!/usr/bin/env python3
"""
Executador silencioso do Sistema OBPC
Inicia o sistema sem mostrar console - Integrado com ExecutarOBPC.bat
"""

import sys
import os
import subprocess
import time
import webbrowser
from pathlib import Path

def iniciar_sistema_silencioso():
    """Inicia o sistema OBPC em modo silencioso"""
    
    print("🔇 Iniciando OBPC em modo silencioso...")
    
    # Diretório do sistema
    sistema_dir = Path(__file__).parent
    run_py = sistema_dir / "run.py"
    
    if not run_py.exists():
        print("❌ Arquivo run.py não encontrado!")
        input("Pressione Enter para sair...")
        return
    
    try:
        # Iniciar servidor Flask em background
        print("🚀 Iniciando Sistema OBPC...")
        
        # No Windows, usar pythonw.exe para não mostrar console
        if sys.platform.startswith('win'):
            python_exe = sys.executable.replace('python.exe', 'pythonw.exe')
            if not os.path.exists(python_exe):
                python_exe = sys.executable
        else:
            python_exe = sys.executable
            
        # Iniciar processo em background
        processo = subprocess.Popen(
            [python_exe, str(run_py)],
            cwd=str(sistema_dir),
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            creationflags=subprocess.CREATE_NO_WINDOW if sys.platform.startswith('win') else 0
        )
        
        # Aguardar o servidor iniciar
        print("⏳ Aguardando servidor iniciar...")
        time.sleep(5)
        
        # Abrir navegador
        print("🌐 Abrindo navegador...")
        webbrowser.open("http://127.0.0.1:5000")
        
        print("✅ Sistema iniciado com sucesso!")
        print("🎯 Acesse: http://127.0.0.1:5000")
        print("📧 Login: admin@obpc.com")
        print("🔑 Senha: 123456")
        
        # Salvar PID para poder fechar depois
        pid_file = sistema_dir / "obpc_server.pid"
        with open(pid_file, 'w') as f:
            f.write(str(processo.pid))
            
        print(f"💾 PID salvo em: {pid_file}")
        print("\n🔴 Para fechar o sistema, execute: python fechar_obpc.py")
        
    except Exception as e:
        print(f"❌ Erro ao iniciar sistema: {str(e)}")
        input("Pressione Enter para sair...")

if __name__ == "__main__":
    iniciar_sistema_silencioso()