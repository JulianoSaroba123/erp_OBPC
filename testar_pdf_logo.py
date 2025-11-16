#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Teste de geração de PDF para verificar o logo
"""

import sys
import os

# Adicionar o diretório do projeto ao path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from app.extensoes import db
from app.configuracoes.configuracoes_model import Configuracao
from app.secretaria.atas.atas_model import Ata
from flask import render_template
from datetime import datetime

def testar_pdf_ata():
    """Testa a geração do HTML da ata para verificar o logo"""
    
    app = create_app()
    
    with app.app_context():
        try:
            print("🔍 TESTE DE PDF COM LOGO")
            print("=" * 50)
            
            # Buscar primeira ata
            ata = Ata.query.first()
            if not ata:
                print("❌ Nenhuma ata encontrada")
                return
            
            print(f"✅ Ata encontrada: {ata.titulo}")
            
            # Buscar configuração
            config = Configuracao.obter_configuracao()
            print(f"✅ Configuração: {config.nome_igreja}")
            print(f"📂 Logo: {config.logo}")
            print(f"🖼️  Exibir: {config.exibir_logo_relatorio}")
            
            # Renderizar template HTML
            with app.test_request_context('http://127.0.0.1:5000/'):
                html_content = render_template('atas/pdf_ata.html', 
                                             ata=ata, 
                                             config=config,
                                             data_geracao=datetime.now().strftime('%d/%m/%Y às %H:%M'),
                                             base_url='http://127.0.0.1:5000/')
            
            print("\n🔍 CONTEÚDO HTML GERADO:")
            print("-" * 30)
            
            # Extrair apenas a parte do logo do HTML
            linhas = html_content.split('\n')
            logo_encontrado = False
            
            for i, linha in enumerate(linhas):
                if 'Logo' in linha or 'logo' in linha or 'img' in linha:
                    print(f"Linha {i+1}: {linha.strip()}")
                    logo_encontrado = True
            
            if not logo_encontrado:
                print("❌ Nenhuma referência ao logo encontrada no HTML")
            
            # Salvar HTML para debug
            with open('debug_ata.html', 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            print(f"\n📄 HTML salvo em: debug_ata.html")
            print("🌐 Para testar, abra este arquivo no navegador")
            
        except Exception as e:
            print(f"❌ Erro: {str(e)}")
            import traceback
            traceback.print_exc()

if __name__ == '__main__':
    testar_pdf_ata()