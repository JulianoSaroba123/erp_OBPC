#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Script para adicionar colunas departamento_id e criado_por na tabela eventos
"""

from app import create_app
from app.extensoes import db
from sqlalchemy import text, inspect

app = create_app()

with app.app_context():
    print("=" * 70)
    print("ADICIONANDO COLUNAS NA TABELA eventos")
    print("=" * 70)
    
    try:
        inspector = inspect(db.engine)
        columns = [col['name'] for col in inspector.get_columns('eventos')]
        
        with db.engine.connect() as conn:
            # Adicionar coluna departamento_id
            if 'departamento_id' not in columns:
                conn.execute(text("ALTER TABLE eventos ADD COLUMN departamento_id INTEGER;"))
                conn.execute(text("ALTER TABLE eventos ADD CONSTRAINT fk_eventos_departamento FOREIGN KEY (departamento_id) REFERENCES departamentos(id);"))
                print("✅ Coluna departamento_id adicionada!")
            else:
                print("⚠️  Coluna departamento_id já existe!")
            
            # Adicionar coluna criado_por
            if 'criado_por' not in columns:
                conn.execute(text("ALTER TABLE eventos ADD COLUMN criado_por INTEGER;"))
                conn.execute(text("ALTER TABLE eventos ADD CONSTRAINT fk_eventos_usuario FOREIGN KEY (criado_por) REFERENCES usuarios(id);"))
                print("✅ Coluna criado_por adicionada!")
            else:
                print("⚠️  Coluna criado_por já existe!")
            
            conn.commit()
                
    except Exception as e:
        print(f"\n❌ Erro: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "=" * 70)
    print("CONCLUÍDO!")
    print("=" * 70)
