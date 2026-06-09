#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Script para corrigir logo com logo_version concatenado incorretamente
Problema: logo_igreja_20260207_180639.jpg21 (21 é o logo_version)
Execute no Render: python corrigir_logo_render.py
"""

import os
import sys
import re

# Adicionar o diretório raiz ao path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from app import create_app
from app.extensoes import db
from app.configuracoes.configuracoes_model import Configuracao

def corrigir_logo():
    """Corrige logo com logo_version concatenado incorretamente no final"""
    app = create_app()
    
    with app.app_context():
        try:
            config = Configuracao.query.first()
            
            if not config:
                print("❌ Nenhuma configuração encontrada")
                return
            
            print(f"📋 Logo atual no banco: '{config.logo}'")
            print(f"📋 Logo version: {config.logo_version}")
            
            # Detectar se logo tem números extras no final (logo_version concatenado)
            # Padrão: logo_igreja_YYYYMMDD_HHMMSS.jpg + números
            if config.logo:
                match = re.match(r'(logo_igreja_\d{8}_\d{6}\.(jpg|jpeg|png|gif))(\d+)$', config.logo)
                
                if match:
                    logo_correto = match.group(1)
                    numero_extra = match.group(3)
                    
                    print(f"\n❌ PROBLEMA DETECTADO!")
                    print(f"   Logo tem logo_version concatenado: '{numero_extra}'")
                    print(f"   Logo CORRETO: '{logo_correto}'")
                    
                    # Corrigir
                    config.logo = logo_correto
                    db.session.commit()
                    
                    print(f"\n✅ CORRIGIDO!")
                    print(f"   Novo valor: '{config.logo}'")
                    return True
                
                # Também corrigir se começa com 'static/'
                elif config.logo.startswith('static/'):
                    novo_caminho = config.logo.replace('static/', '', 1)
                    print(f"\n🔧 Removendo 'static/' do início")
                    print(f"   De: '{config.logo}'")
                    print(f"   Para: '{novo_caminho}'")
                    
                    config.logo = novo_caminho
                    db.session.commit()
                    
                    print(f"\n✅ CORRIGIDO!")
                    return True
                
                else:
                    print(f"\n✅ Logo está correto (sem problemas detectados)")
                    return False
            else:
                print(f"\n⚠️ Nenhum logo configurado")
                return False
                
        except Exception as e:
            print(f"❌ Erro: {str(e)}")
            import traceback
            traceback.print_exc()
            return False

if __name__ == '__main__':
    corrigir_logo()
