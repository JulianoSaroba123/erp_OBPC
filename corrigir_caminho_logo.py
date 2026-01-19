#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Script para corrigir o caminho da logo nas configurações
Remove o prefixo 'static/' do caminho salvo no banco
"""

import os
import sys

# Adicionar o diretório raiz ao path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from app import create_app
from app.extensoes import db
from app.configuracoes.configuracoes_model import Configuracao

def corrigir_caminho_logo():
    """Corrige o caminho da logo removendo 'static/' do início"""
    app = create_app()
    
    with app.app_context():
        try:
            config = Configuracao.query.first()
            
            if not config:
                print("❌ Nenhuma configuração encontrada no banco")
                return
            
            print(f"📋 Logo atual: {config.logo}")
            
            # Se a logo começa com 'static/', remover
            if config.logo and config.logo.startswith('static/'):
                novo_caminho = config.logo.replace('static/', '', 1)
                print(f"🔧 Corrigindo para: {novo_caminho}")
                
                config.logo = novo_caminho
                db.session.commit()
                
                print(f"✅ Logo corrigida com sucesso!")
                print(f"   Caminho antigo: static/{novo_caminho}")
                print(f"   Caminho novo: {novo_caminho}")
            else:
                print(f"✅ Logo já está no formato correto: {config.logo}")
                
        except Exception as e:
            print(f"❌ Erro ao corrigir logo: {str(e)}")
            import traceback
            traceback.print_exc()

if __name__ == '__main__':
    corrigir_caminho_logo()
