#!/usr/bin/env python3
"""
Script para testar a visualização de carteira com logo
"""

import sys
import os

# Adicionar o diretório raiz ao path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def testar_carteira_logo():
    try:
        from app import create_app, db
        from app.midia.midia_model import Carteira
        
        app = create_app()
        
        with app.app_context():
            # Buscar uma carteira existente
            carteira = Carteira.query.first()
            
            if carteira:
                print(f"✅ Carteira encontrada: {carteira.nome_completo}")
                print(f"📄 URL para visualizar: http://localhost:5000/midia/carteiras/visualizar/{carteira.id}")
                
                # Verificar se o arquivo de logo existe
                logo_path = os.path.join(app.static_folder, 'Logo_OBPC.jpg')
                if os.path.exists(logo_path):
                    print(f"✅ Logo encontrado em: {logo_path}")
                    print(f"📏 Tamanho do arquivo: {os.path.getsize(logo_path)} bytes")
                else:
                    print(f"❌ Logo não encontrado em: {logo_path}")
                    
                    # Buscar em outros locais
                    outros_locais = [
                        os.path.join(os.path.dirname(__file__), 'static', 'Logo_OBPC.jpg'),
                        os.path.join(os.path.dirname(__file__), 'app', 'static', 'uploads', 'Logo_OBPC.jpg')
                    ]
                    
                    for local in outros_locais:
                        if os.path.exists(local):
                            print(f"✅ Logo encontrado em local alternativo: {local}")
                            break
                
                return True
            else:
                print("❌ Nenhuma carteira encontrada no banco")
                return False
                
    except Exception as e:
        print(f"❌ Erro: {e}")
        return False

if __name__ == "__main__":
    print("🔍 Testando visualização de carteira com logo...")
    testar_carteira_logo()