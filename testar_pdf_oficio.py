#!/usr/bin/env python3
import sys
import os

# Adiciona o diretório raiz do projeto ao path
sys.path.insert(0, os.path.abspath('.'))

from app import create_app, db
from app.configuracoes.configuracoes_model import Configuracao
from app.secretaria.oficios.oficios_model import Oficio

def testar_pdf_oficio():
    """Testa a geração de PDF de ofício sem servidor web"""
    print("Iniciando teste de geração de PDF de ofício...")
    
    app = create_app()
    
    with app.app_context():
        # Testa se consegue buscar configuração
        try:
            config = Configuracao.obter_configuracao()
            print(f"✓ Configuração obtida: {config.nome_igreja}")
        except Exception as e:
            print(f"✗ Erro ao obter configuração: {e}")
            return False
        
        # Testa se consegue buscar um ofício
        try:
            oficio = Oficio.query.first()
            if oficio:
                print(f"✓ Ofício encontrado: {oficio.numero}")
            else:
                print("! Nenhum ofício encontrado no banco")
                return False
        except Exception as e:
            print(f"✗ Erro ao buscar ofício: {e}")
            return False
        
        # Testa renderização do template
        try:
            from flask import render_template
            from datetime import datetime
            
            html_content = render_template('oficios/pdf_oficio.html', 
                                         oficio=oficio,
                                         config=config,
                                         data_geracao=datetime.now().strftime('%d/%m/%Y'),
                                         base_url='http://localhost:5000/')
            
            print(f"✓ Template renderizado com sucesso ({len(html_content)} caracteres)")
            
            # Verifica se há problemas na renderização
            if 'error' in html_content.lower():
                print("! Warning: 'error' encontrado no HTML")
            
            return True
            
        except Exception as e:
            print(f"✗ Erro ao renderizar template: {e}")
            import traceback
            traceback.print_exc()
            return False

if __name__ == "__main__":
    success = testar_pdf_oficio()
    print(f"\nTeste {'PASSOU' if success else 'FALHOU'}")
    sys.exit(0 if success else 1)