#!/usr/bin/env python3
"""
Script para fechar o Sistema OBPC
"""

import os
import signal
import sys
from pathlib import Path

def fechar_sistema_obpc():
    """Fecha o sistema OBPC usando o PID salvo"""
    
    sistema_dir = Path(__file__).parent
    pid_file = sistema_dir / "obpc_server.pid"
    
    if not pid_file.exists():
        print("❌ Sistema não está rodando ou PID não encontrado")
        input("Pressione Enter para sair...")
        return
    
    try:
        # Ler PID do arquivo
        with open(pid_file, 'r') as f:
            pid = int(f.read().strip())
        
        # Fechar processo
        if sys.platform.startswith('win'):
            # Windows
            os.system(f"taskkill /F /PID {pid}")
        else:
            # Linux/Mac
            os.kill(pid, signal.SIGTERM)
        
        # Remover arquivo PID
        pid_file.unlink()
        
        print("✅ Sistema OBPC fechado com sucesso!")
        
    except ValueError:
        print("❌ PID inválido no arquivo")
    except ProcessLookupError:
        print("❌ Processo não encontrado (já foi fechado)")
        # Remover arquivo PID órfão
        if pid_file.exists():
            pid_file.unlink()
    except Exception as e:
        print(f"❌ Erro ao fechar sistema: {str(e)}")
    
    input("Pressione Enter para sair...")

if __name__ == "__main__":
    fechar_sistema_obpc()