#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os

# Adicionar o diretório raiz ao path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from app.midia.midia_model import Certificado

def testar_sqlalchemy():
    """Testa se o SQLAlchemy está vendo os certificados"""
    
    app = create_app()
    
    with app.app_context():
        try:
            # Testar consulta direta
            certificados = Certificado.query.all()
            total = len(certificados)
            
            print(f"✅ SQLAlchemy funcionando!")
            print(f"📜 Total de certificados encontrados: {total}")
            
            if total > 0:
                print(f"\n📋 Certificados:")
                for cert in certificados:
                    print(f"   - ID {cert.id}: {cert.nome_pessoa} ({cert.tipo_certificado})")
                    if hasattr(cert, 'genero') and cert.genero:
                        print(f"     Gênero: {cert.genero}")
                    if hasattr(cert, 'padrinhos') and cert.padrinhos:
                        print(f"     Padrinhos: {cert.padrinhos}")
            else:
                print(f"⚠️ Nenhum certificado encontrado via SQLAlchemy")
                
                # Verificar tabelas
                from sqlalchemy import inspect
                inspector = inspect(db.engine)
                tabelas = inspector.get_table_names()
                print(f"📋 Tabelas no banco: {tabelas}")
                
                if 'certificados' in tabelas:
                    colunas = inspector.get_columns('certificados')
                    print(f"📊 Colunas da tabela certificados:")
                    for col in colunas:
                        print(f"   - {col['name']}: {col['type']}")
                        
        except Exception as e:
            print(f"❌ Erro no SQLAlchemy: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    print("=== TESTANDO SQLALCHEMY ===\n")
    testar_sqlalchemy()