#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Teste final para verificar se todos os templates estão funcionando
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import create_app
import requests

def testar_templates_corrigidos():
    print("=" * 60)
    print("TESTE: Templates Corrigidos")
    print("=" * 60)
    
    # Testar as URLs diretamente
    urls_teste = [
        '/midia/agenda/',
        '/midia/certificados/',
        '/midia/carteiras/'
    ]
    
    for url in urls_teste:
        print(f"\n🧪 Testando: {url}")
        try:
            response = requests.get(f'http://localhost:5000{url}', timeout=5)
            print(f"Status: {response.status_code}")
            
            if response.status_code == 200:
                print("✅ Sucesso!")
            elif response.status_code == 302:
                print("🔄 Redirecionamento (provavelmente para login)")
            elif response.status_code == 404:
                print("❌ Página não encontrada")
            else:
                print(f"⚠️ Status inesperado: {response.status_code}")
                
        except requests.exceptions.ConnectionError:
            print("❌ Servidor não está rodando")
        except Exception as e:
            print(f"❌ Erro: {str(e)}")

if __name__ == "__main__":
    testar_templates_corrigidos()