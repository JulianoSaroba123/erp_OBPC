#!/usr/bin/env python3
"""
Teste direto dos templates de certificados e carteiras
"""

import sys
import os

# Adicionar o diretório raiz ao path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from app.midia.midia_model import Certificado, CarteiraMembro

def testar_templates_diretamente():
    """Testa renderização direta dos templates"""
    
    app = create_app()
    
    with app.app_context():
        print("🎨 Teste direto dos templates")
        print("=" * 40)
        
        # 1. Testar template de certificados
        print("\n📋 Testando template de certificados...")
        try:
            certificados = Certificado.query.all()
            print(f"   Dados: {len(certificados)} certificados")
            
            from flask import render_template
            tipos_certificado = ['Batismo', 'Apresentação']
            
            resultado = render_template('certificados/lista_certificados.html',
                                      certificados=certificados,
                                      tipos_certificado=tipos_certificado,
                                      tipo_atual='',
                                      nome_atual='')
            
            print("   ✅ Template de certificados OK!")
            
        except Exception as e:
            print(f"   ❌ ERRO no template de certificados: {e}")
            import traceback
            traceback.print_exc()
        
        # 2. Testar template de carteiras
        print("\n🎫 Testando template de carteiras...")
        try:
            carteiras = CarteiraMembro.query.filter(CarteiraMembro.ativo == True).all()
            print(f"   Dados: {len(carteiras)} carteiras")
            
            resultado = render_template('carteiras/lista_carteiras.html',
                                      carteiras=carteiras,
                                      nome_atual='',
                                      numero_atual='')
            
            print("   ✅ Template de carteiras OK!")
            
        except Exception as e:
            print(f"   ❌ ERRO no template de carteiras: {e}")
            import traceback
            traceback.print_exc()
        
        print("\n" + "=" * 40)

if __name__ == "__main__":
    testar_templates_diretamente()