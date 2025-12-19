#!/usr/bin/env python3
"""
Iniciador Automático do Sistema OBPC
- Inicia o sistema em background
- Abre automaticamente no navegador
- Fecha a janela do CMD automaticamente
"""

import sys
import os
import subprocess
import time
import webbrowser
from pathlib import Path
import socket

def verificar_servidor_online(host="127.0.0.1", port=5000, timeout=30):
    """Verifica se o servidor está online usando socket"""
    inicio = time.time()
    while time.time() - inicio < timeout:
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(2)
            result = sock.connect_ex((host, port))
            sock.close()
            if result == 0:
                return True
        except:
            pass
        time.sleep(1)
    return False

def iniciar_obpc_automatico():
    """Inicia o OBPC automaticamente e abre no navegador"""
    
    # Configurações
    sistema_dir = Path(__file__).parent
    run_py = sistema_dir / "run.py"
    url_sistema = "http://127.0.0.1:5000"
    
    if not run_py.exists():
        print("❌ Sistema OBPC não encontrado!")
        return False
    
    try:
        # 1. Iniciar servidor Flask em background (sem console)
        if sys.platform.startswith('win'):
            # Usar pythonw.exe para não mostrar janela
            python_exe = sys.executable.replace('python.exe', 'pythonw.exe')
            if not os.path.exists(python_exe):
                python_exe = sys.executable
        else:
            python_exe = sys.executable
            
        # Iniciar processo completamente em background
        processo = subprocess.Popen(
            [python_exe, str(run_py)],
            cwd=str(sistema_dir),
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            stdin=subprocess.DEVNULL,
            creationflags=subprocess.CREATE_NO_WINDOW if sys.platform.startswith('win') else 0
        )
        
        # 2. Aguardar servidor ficar online
        print("🚀 Iniciando Sistema OBPC...")
        if verificar_servidor_online():
            print("✅ Sistema iniciado com sucesso!")
            
            # 3. Salvar PID para controle
            pid_file = sistema_dir / "obpc_server.pid"
            with open(pid_file, 'w') as f:
                f.write(str(processo.pid))
            
            # 4. Abrir automaticamente no navegador
            print("🌐 Abrindo navegador...")
            webbrowser.open(url_sistema)
            
            # 5. Mostrar informações e fechar automaticamente
            print(f"🎯 Sistema disponível em: {url_sistema}")
            print("📧 Login: admin@obpc.com | 🔑 Senha: 123456")
            print("🔴 Para fechar: python fechar_obpc.py")
            
            # Aguardar um pouco para garantir que o navegador abra
            time.sleep(3)
            
            # 6. Fechar automaticamente esta janela
            print("✨ Fechando janela automaticamente...")
            return True
            
        else:
            print("❌ Erro: Sistema não conseguiu iniciar!")
            processo.terminate()
            return False
            
    except Exception as e:
        print(f"❌ Erro crítico: {str(e)}")
        return False

def main():
    """Função principal"""
    # Configurar título da janela
    if sys.platform.startswith('win'):
        os.system('title Sistema OBPC - Iniciando...')
    
    # Iniciar sistema
    sucesso = iniciar_obpc_automatico()
    
    if not sucesso:
        print("\n❌ Falha ao iniciar o sistema!")
        input("Pressione Enter para sair...")

if __name__ == "__main__":
    main()