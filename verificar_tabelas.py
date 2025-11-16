#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Verificar estrutura das tabelas para debug
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import create_app

def verificar_tabelas():
    print("=" * 60)
    print("VERIFICAÇÃO: Estrutura das Tabelas")
    print("=" * 60)
    
    app = create_app()
    
    with app.app_context():
        from app import db
        
        print("\n📋 TABELAS NO BANCO:")
        print("-" * 40)
        
        # Verificar tabelas
        inspector = db.inspect(db.engine)
        tables = inspector.get_table_names()
        
        for table in tables:
            print(f"✅ {table}")
            
        print(f"\n📊 Total: {len(tables)} tabelas")
        
        print("\n🔍 VERIFICANDO MODELOS:")
        print("-" * 40)
        
        try:
            from app.midia.midia_model import AgendaSemanal, Certificado, CarteiraMembro
            
            print("✅ AgendaSemanal importado")
            agenda_count = AgendaSemanal.query.count()
            print(f"   📊 Registros: {agenda_count}")
            
            print("✅ Certificado importado")
            cert_count = Certificado.query.count()
            print(f"   📊 Registros: {cert_count}")
            
            print("✅ CarteiraMembro importado")
            carteira_count = CarteiraMembro.query.count()
            print(f"   📊 Registros: {carteira_count}")
            
        except Exception as e:
            print(f"❌ Erro ao importar modelos: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    verificar_tabelas()