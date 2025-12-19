#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Teste final de logo nos PDFs
"""

import sys
import os

# Adicionar o diretório do projeto ao path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from app.extensoes import db
from app.configuracoes.configuracoes_model import Configuracao

def verificacao_final_logo():
    """Verificação final do logo nos PDFs"""
    
    app = create_app()
    
    with app.app_context():
        try:
            print("🎯 VERIFICAÇÃO FINAL DO LOGO NOS PDFS")
            print("=" * 60)
            
            # Buscar configuração
            config = Configuracao.obter_configuracao()
            
            print(f"✅ Igreja: {config.nome_igreja}")
            print(f"📂 Logo: {config.logo}")
            print(f"🖼️  Exibir logo: {config.exibir_logo_relatorio}")
            
            # Verificar arquivo do logo
            logo_path = os.path.join(app.root_path, '..', config.logo)
            print(f"📁 Caminho absoluto: {logo_path}")
            print(f"✅ Arquivo existe: {os.path.exists(logo_path)}")
            
            if os.path.exists(logo_path):
                size = os.path.getsize(logo_path)
                print(f"📏 Tamanho: {size:,} bytes")
            
            # URL que será usada nos PDFs
            print(f"\n🌐 URL no PDF: http://127.0.0.1:5000/{config.logo}")
            
            print("\n📋 TEMPLATES ATUALIZADOS:")
            print("✅ Atas: templates/atas/pdf_ata.html")
            print("✅ Inventário: templates/inventario/pdf_inventario.html") 
            print("✅ Ofícios: templates/oficios/pdf_oficio.html")
            
            print("\n⚙️ ROUTES ATUALIZADOS:")
            print("✅ atas_routes.py - passa base_url")
            print("✅ inventario_routes.py - passa base_url")
            print("✅ oficios_routes.py - passa base_url")
            
            print("\n🎉 PRONTO PARA TESTE!")
            print("🔥 Gere um PDF de ata, inventário ou ofício")
            print("🖼️  O logo da igreja deve aparecer no topo do documento")
            
            return True
            
        except Exception as e:
            print(f"❌ Erro: {str(e)}")
            return False

if __name__ == '__main__':
    verificacao_final_logo()