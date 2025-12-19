#!/usr/bin/env python3
"""
Script para testar certificados específicamente
"""

import sys
import os

# Adicionar o diretório raiz ao path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from app.midia.midia_model import Certificado

def testar_certificados():
    """Testa função de certificados"""
    
    app = create_app()
    
    with app.app_context():
        print("🎓 Teste de certificados")
        print("=" * 30)
        
        try:
            # Verificar dados
            certificados = Certificado.query.all()
            print(f"✅ Total certificados: {len(certificados)}")
            
            # Testar query
            query = Certificado.query
            certificados = query.order_by(Certificado.data_evento.desc()).all()
            print(f"✅ Query executada: {len(certificados)} itens")
            
            # Testar template
            from flask import render_template
            tipos_certificado = ['Batismo', 'Apresentação']
            
            resultado = render_template('certificados/lista_certificados.html',
                                      certificados=certificados,
                                      tipos_certificado=tipos_certificado,
                                      tipo_atual='',
                                      nome_atual='')
            
            print("✅ Template renderizado com sucesso!")
            return True
            
        except Exception as e:
            print(f"❌ ERRO: {type(e).__name__}: {e}")
            import traceback
            traceback.print_exc()
            return False

if __name__ == "__main__":
    testar_certificados()