#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Testar query dos certificados especificamente
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import create_app

def testar_query_certificados():
    print("=" * 60)
    print("TESTE: Query de Certificados")
    print("=" * 60)
    
    app = create_app()
    
    with app.app_context():
        from app.midia.midia_model import Certificado
        from app import db
        
        print("\n🧪 Testando query básica...")
        try:
            certificados = Certificado.query.all()
            print(f"✅ Query básica funcionou! Total: {len(certificados)}")
            
            for cert in certificados:
                print(f"   - {cert.nome_pessoa} ({cert.tipo_certificado})")
                
        except Exception as e:
            print(f"❌ Erro na query básica: {e}")
            return
        
        print("\n🧪 Testando query com order_by...")
        try:
            certificados = Certificado.query.order_by(Certificado.data_evento.desc()).all()
            print(f"✅ Query com order_by funcionou! Total: {len(certificados)}")
        except Exception as e:
            print(f"❌ Erro na query com order_by: {e}")
            return
        
        print("\n🧪 Testando db.extract...")
        try:
            # Testar extract para mês
            from sqlalchemy import extract
            query = Certificado.query.filter(extract('month', Certificado.data_evento) == 1)
            resultado = query.all()
            print(f"✅ db.extract funcionou! Registros do mês 1: {len(resultado)}")
        except Exception as e:
            print(f"❌ Erro no db.extract: {e}")
            print("   Vou testar sem extract...")
            
            # Tentar sem extract
            query = Certificado.query
            resultado = query.all()
            print(f"✅ Query sem filtros funcionou: {len(resultado)}")

if __name__ == "__main__":
    testar_query_certificados()