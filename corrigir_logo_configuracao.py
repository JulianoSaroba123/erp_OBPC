#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Script para corrigir o logo nas configurações
Sistema OBPC - Igreja O Brasil para Cristo
"""

import os
import sys

# Adicionar o diretório raiz ao path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from app.extensoes import db
from app.configuracoes.configuracoes_model import Configuracao

def corrigir_logo():
    """Corrige o logo nas configurações se estiver None ou vazio"""
    
    app = create_app()
    
    with app.app_context():
        try:
            print("=" * 70)
            print("CORRIGINDO LOGO NAS CONFIGURAÇÕES")
            print("=" * 70)
            
            # Obter configuração
            config = Configuracao.query.first()
            
            if not config:
                print("\n⚠ Nenhuma configuração encontrada no banco!")
                print("✓ Criando configuração padrão...")
                config = Configuracao.obter_configuracao()
                print(f"✓ Configuração criada com logo: {config.logo}")
            else:
                print(f"\n✓ Configuração encontrada (ID: {config.id})")
                print(f"  Nome: {config.nome_igreja}")
                print(f"  Logo atual: {config.logo}")
                
                # Se logo estiver None, vazio ou com caminho incorreto, corrigir
                if not config.logo or config.logo.strip() == '':
                    print("\n⚠ Logo está vazio ou None!")
                    config.logo = 'logo_obpc_novo.jpg'
                    print(f"✓ Logo definido como: {config.logo}")
                    
                    db.session.commit()
                    print("✓ Configuração atualizada no banco!")
                    
                elif config.logo.startswith('static/'):
                    print("\n⚠ Logo contém 'static/' no caminho!")
                    config.logo = config.logo.replace('static/', '')
                    print(f"✓ Logo corrigido para: {config.logo}")
                    
                    db.session.commit()
                    print("✓ Configuração atualizada no banco!")
                    
                else:
                    print("\n✓ Logo está correto!")
            
            # Verificar se o arquivo existe
            logo_path = os.path.join(app.root_path, 'static', config.logo)
            print(f"\n📁 Verificando arquivo: {logo_path}")
            
            if os.path.exists(logo_path):
                print(f"✓ Arquivo encontrado!")
                file_size = os.path.getsize(logo_path)
                print(f"  Tamanho: {file_size} bytes")
            else:
                print(f"❌ Arquivo não encontrado!")
                print(f"  Procurando arquivos de logo disponíveis...")
                
                static_dir = os.path.join(app.root_path, 'static')
                logo_files = [f for f in os.listdir(static_dir) if 'logo' in f.lower() and f.endswith(('.jpg', '.jpeg', '.png'))]
                
                if logo_files:
                    print(f"\n✓ Encontrados {len(logo_files)} arquivos de logo:")
                    for i, logo_file in enumerate(logo_files, 1):
                        file_path = os.path.join(static_dir, logo_file)
                        file_size = os.path.getsize(file_path)
                        print(f"  {i}. {logo_file} ({file_size} bytes)")
                else:
                    print("  ❌ Nenhum arquivo de logo encontrado!")
            
            print("\n" + "=" * 70)
            print("RESUMO")
            print("=" * 70)
            print(f"✓ Logo configurado: {config.logo}")
            print(f"✓ Caminho completo: static/{config.logo}")
            print(f"✓ Exibir logo nos relatórios: {'SIM' if config.exibir_logo_relatorio else 'NÃO'}")
            print("=" * 70)
            
            print("\n✅ Correção concluída com sucesso!")
            
        except Exception as e:
            print(f"\n❌ ERRO: {str(e)}")
            db.session.rollback()
            import traceback
            traceback.print_exc()
            return False
        
        return True

if __name__ == '__main__':
    print("\n🔧 Iniciando correção do logo...\n")
    
    sucesso = corrigir_logo()
    
    if sucesso:
        print("\n✅ Script executado com sucesso!")
    else:
        print("\n❌ Script finalizado com erros!")
        sys.exit(1)
