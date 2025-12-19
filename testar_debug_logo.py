#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Teste de debug do logo OBPC
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from flask import url_for

def main():
    app = create_app()
    
    with app.app_context():
        print("=== DEBUG DO LOGO OBPC ===")
        
        # Verificar caminhos dos arquivos
        arquivos_logo = [
            'Logo_OBPC.jpg',
            'logo_obpc_novo.jpg', 
            'Logo_IBPC.jpg',
            'logo_obpc.ico'
        ]
        
        print("📁 VERIFICANDO ARQUIVOS DE LOGO:")
        for arquivo in arquivos_logo:
            caminho_completo = os.path.join(app.static_folder, arquivo)
            existe = os.path.exists(caminho_completo)
            
            if existe:
                tamanho = os.path.getsize(caminho_completo) / 1024
                url = url_for('static', filename=arquivo)
                print(f"✅ {arquivo} - {tamanho:.1f}KB - URL: {url}")
            else:
                print(f"❌ {arquivo} - NÃO ENCONTRADO")
        
        print(f"\n📂 Pasta static: {app.static_folder}")
        
        # URL que deve funcionar
        print(f"\n🔗 URL DO LOGO PRINCIPAL:")
        try:
            url_logo = url_for('static', filename='Logo_OBPC.jpg')
            print(f"   {url_logo}")
        except Exception as e:
            print(f"❌ Erro ao gerar URL: {e}")

if __name__ == "__main__":
    main()