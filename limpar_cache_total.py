#!/usr/bin/env python3
"""
REINICIAR SISTEMA COM CACHE LIMPO
"""

import os
import sys
import time
import subprocess

def limpar_cache():
    """Limpa cache do Flask e força reload"""
    
    print("🧹 LIMPANDO CACHE COMPLETO...")
    
    # Matar qualquer processo Flask ativo
    try:
        subprocess.run("taskkill /f /im python.exe", shell=True, capture_output=True)
        time.sleep(2)
    except:
        pass
    
    # Remover arquivos de cache Python
    cache_dirs = []
    for root, dirs, files in os.walk('.'):
        for d in dirs:
            if d == '__pycache__':
                cache_dirs.append(os.path.join(root, d))
    
    for cache_dir in cache_dirs:
        try:
            import shutil
            shutil.rmtree(cache_dir)
            print(f"🗑️ Removido: {cache_dir}")
        except:
            pass
    
    # Adicionar timestamp para quebrar cache do navegador
    timestamp = str(int(time.time()))
    
    # Forçar reload do template com timestamp
    template_path = "app/financeiro/templates/financeiro/importar_extrato.html"
    
    if os.path.exists(template_path):
        with open(template_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Adicionar comentário com timestamp para quebrar cache
        cache_breaker = f"<!-- CACHE_BREAKER_{timestamp} -->"
        
        if "CACHE_BREAKER" not in content:
            content = content.replace('<head>', f'<head>\n{cache_breaker}')
        else:
            # Substituir timestamp existente
            import re
            content = re.sub(r'<!-- CACHE_BREAKER_\d+ -->', cache_breaker, content)
        
        with open(template_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"✅ Cache breaker adicionado: {timestamp}")
    
    print("🧹 CACHE LIMPO COMPLETAMENTE!")
    return True

if __name__ == "__main__":
    limpar_cache()
    
    print("\n🚀 REINICIANDO SERVIDOR...")
    time.sleep(1)
    
    # Iniciar servidor novo
    os.system("python iniciar_obpc_automatico.py")