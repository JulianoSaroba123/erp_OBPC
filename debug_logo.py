#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Debug do logo - Verificar como o caminho está sendo passado
"""

import sys
import os

# Adicionar o diretório do projeto ao path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from app.extensoes import db
from app.configuracoes.configuracoes_model import Configuracao

def debug_logo():
    """Debug do logo das configurações"""
    
    app = create_app()
    
    with app.app_context():
        try:
            print("🔍 DEBUG DO LOGO")
            print("=" * 50)
            
            # Buscar configuração
            config = Configuracao.obter_configuracao()
            
            print(f"Config logo: '{config.logo}'")
            print(f"Exibir logo: {config.exibir_logo_relatorio}")
            
            # Testar diferentes caminhos
            caminhos_teste = [
                config.logo,
                f"/{config.logo}",
                f"http://127.0.0.1:5000/{config.logo}",
                config.logo.replace('static/', ''),
                f"http://127.0.0.1:5000/static/{config.logo.replace('static/', '')}"
            ]
            
            print("\n🧪 CAMINHOS TESTE:")
            for i, caminho in enumerate(caminhos_teste, 1):
                print(f"{i}. {caminho}")
            
            # Verificar arquivo físico
            logo_path_absoluto = os.path.join(app.root_path, '..', config.logo)
            print(f"\n📂 Caminho absoluto: {logo_path_absoluto}")
            print(f"📁 Existe: {os.path.exists(logo_path_absoluto)}")
            
            if os.path.exists(logo_path_absoluto):
                print(f"📏 Tamanho: {os.path.getsize(logo_path_absoluto)} bytes")
            
            print(f"\n🌐 URL Root seria: http://127.0.0.1:5000/")
            print(f"🖼️  Logo URL final: http://127.0.0.1:5000/{config.logo}")
            
        except Exception as e:
            print(f"❌ Erro: {str(e)}")

if __name__ == '__main__':
    debug_logo()