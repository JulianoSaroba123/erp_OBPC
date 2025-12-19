#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de teste para verificar se o logo das configurações está sendo usado corretamente
nos PDFs de ata, inventário e ofício.
"""

import sys
import os

# Adicionar o diretório do projeto ao path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from app.extensoes import db
from app.configuracoes.configuracoes_model import Configuracao

def testar_logo_configuracoes():
    """Testa se o logo das configurações está configurado corretamente"""
    
    app = create_app()
    
    with app.app_context():
        try:
            print("🔍 TESTE DO LOGO DAS CONFIGURAÇÕES")
            print("=" * 60)
            
            # Buscar configuração
            config = Configuracao.obter_configuracao()
            
            if not config:
                print("❌ Configuração não encontrada!")
                return False
            
            print(f"✅ Configuração encontrada: {config.nome_igreja}")
            print(f"📂 Logo configurado: {config.logo}")
            print(f"🖼️  Exibir logo em relatórios: {config.exibir_logo_relatorio}")
            
            # Verificar se o arquivo do logo existe
            if config.logo:
                logo_path = os.path.join(app.root_path, '..', config.logo)
                if os.path.exists(logo_path):
                    print(f"✅ Arquivo do logo existe: {logo_path}")
                    
                    # Verificar tamanho do arquivo
                    file_size = os.path.getsize(logo_path)
                    print(f"📏 Tamanho do arquivo: {file_size:,} bytes")
                    
                    if file_size > 0:
                        print("✅ Arquivo do logo válido")
                    else:
                        print("❌ Arquivo do logo está vazio")
                        return False
                else:
                    print(f"❌ Arquivo do logo não encontrado: {logo_path}")
                    return False
            else:
                print("⚠️  Nenhum logo configurado")
            
            print("\n🎯 VERIFICAÇÃO DOS TEMPLATES:")
            print("-" * 40)
            
            # Verificar templates
            templates_para_verificar = [
                'app/secretaria/atas/templates/atas/pdf_ata.html',
                'app/secretaria/inventario/templates/inventario/pdf_inventario.html',
                'app/secretaria/oficios/templates/oficios/pdf_oficio.html'
            ]
            
            for template_path in templates_para_verificar:
                if os.path.exists(template_path):
                    print(f"✅ Template encontrado: {template_path}")
                    
                    # Verificar se o template usa config.logo
                    with open(template_path, 'r', encoding='utf-8') as f:
                        conteudo = f.read()
                        
                    if 'config.logo' in conteudo and 'config.exibir_logo_relatorio' in conteudo:
                        print("   ✅ Template atualizado para usar logo das configurações")
                    else:
                        print("   ❌ Template ainda usa logo fixo")
                        return False
                else:
                    print(f"❌ Template não encontrado: {template_path}")
                    return False
            
            print("\n🎉 TODOS OS TESTES PASSARAM!")
            print("✨ O logo das configurações está configurado corretamente")
            print("📋 Templates atualizados para usar o logo dinâmico")
            
            return True
            
        except Exception as e:
            print(f"❌ Erro durante o teste: {str(e)}")
            return False

if __name__ == '__main__':
    sucesso = testar_logo_configuracoes()
    if sucesso:
        print("\n✅ Sistema pronto! O logo da igreja será usado nos PDFs.")
    else:
        print("\n❌ Problemas encontrados. Verifique a configuração do logo.")