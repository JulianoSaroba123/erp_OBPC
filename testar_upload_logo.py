#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Teste de Upload de Logo - Sistema OBPC
Igreja O Brasil para Cristo - Tietê/SP

Script para testar a funcionalidade de upload de logo
"""

import sys
import os

# Adicionar o diretório raiz ao path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from app.configuracoes.configuracoes_model import Configuracao

def testar_upload_logo():
    """Testa a configuração de upload de logo"""
    print("🔧 TESTE DE UPLOAD DE LOGO")
    print("=" * 40)
    
    # Criar app
    app = create_app()
    
    with app.app_context():
        try:
            # Obter configuração
            config = Configuracao.obter_configuracao()
            print(f"✅ Configuração obtida: ID {config.id}")
            print(f"📋 Logo atual: {config.logo}")
            
            # Testar salvamento
            config.logo = "static/teste_logo.jpg"
            if config.salvar():
                print("✅ Logo salva com sucesso no banco!")
            else:
                print("❌ Erro ao salvar logo no banco")
            
            # Verificar se foi salvo
            config_nova = Configuracao.obter_configuracao()
            print(f"📋 Logo após salvamento: {config_nova.logo}")
            
            # Verificar pasta static
            static_path = os.path.join(os.path.dirname(__file__), 'static')
            print(f"📁 Pasta static: {static_path}")
            print(f"📁 Pasta static existe: {os.path.exists(static_path)}")
            print(f"📁 Permissão de escrita: {os.access(static_path, os.W_OK)}")
            
            # Listar arquivos na pasta static
            if os.path.exists(static_path):
                arquivos = os.listdir(static_path)
                print(f"📋 Arquivos na pasta static: {arquivos}")
            
        except Exception as e:
            print(f"❌ Erro durante o teste: {str(e)}")
            import traceback
            traceback.print_exc()

if __name__ == '__main__':
    testar_upload_logo()