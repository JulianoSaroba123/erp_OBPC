#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Script para corrigir o caminho da logo no Render
Execute: python corrigir_logo_render.py
"""

import os
import sys

# Adicionar o diretório raiz ao path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from app import create_app
from app.extensoes import db
from app.configuracoes.configuracoes_model import Configuracao

def corrigir_logo():
    """Corrige o caminho da logo removendo 'static/' do início"""
    app = create_app()
    
    with app.app_context():
        try:
            config = Configuracao.query.first()
            
            if not config:
                print("❌ Nenhuma configuração encontrada")
                return
            
            print(f"📋 Logo atual no banco: {config.logo}")
            
            # Se a logo começa com 'static/', remover
            if config.logo and config.logo.startswith('static/'):
                novo_caminho = config.logo.replace('static/', '', 1)
                print(f"🔧 Corrigindo de '{config.logo}' para '{novo_caminho}'")
                
                config.logo = novo_caminho
                db.session.commit()
                
                print(f"✅ Logo corrigida com sucesso!")
                print(f"   Novo caminho: {novo_caminho}")
            else:
                print(f"✅ Logo já está correto: {config.logo}")
            
            # Verificar se o arquivo existe
            static_folder = os.path.join(os.path.dirname(__file__), 'app', 'static')
            if config.logo:
                logo_path = os.path.join(static_folder, config.logo)
                if os.path.exists(logo_path):
                    print(f"✅ Arquivo existe: {logo_path}")
                else:
                    print(f"⚠️  Arquivo NÃO encontrado: {logo_path}")
                    print(f"   Faça upload de uma nova logo nas configurações")
                
        except Exception as e:
            print(f"❌ Erro: {str(e)}")
            import traceback
            traceback.print_exc()

if __name__ == '__main__':
    corrigir_logo()
