#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Script para adicionar a coluna departamento_id na tabela usuarios
"""

from app import create_app
from app.extensoes import db

app = create_app()

with app.app_context():
    print("=" * 70)
    print("ADICIONANDO COLUNA departamento_id NA TABELA usuarios")
    print("=" * 70)
    
    try:
        # Verificar se a coluna já existe
        from sqlalchemy import inspect, text
        inspector = inspect(db.engine)
        columns = [col['name'] for col in inspector.get_columns('usuarios')]
        
        if 'departamento_id' in columns:
            print("\n⚠️  A coluna departamento_id já existe!")
        else:
            # Adicionar a coluna
            with db.engine.connect() as conn:
                conn.execute(text("""
                    ALTER TABLE usuarios 
                    ADD COLUMN departamento_id INTEGER;
                """))
                conn.commit()
                
                print("\n✅ Coluna departamento_id adicionada com sucesso!")
            
            # Adicionar a foreign key
            with db.engine.connect() as conn:
                conn.execute(text("""
                    ALTER TABLE usuarios 
                    ADD CONSTRAINT fk_usuarios_departamento 
                    FOREIGN KEY (departamento_id) 
                    REFERENCES departamentos(id);
                """))
                conn.commit()
                
                print("✅ Foreign key adicionada com sucesso!")
                
    except Exception as e:
        print(f"\n❌ Erro: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "=" * 70)
    print("CONCLUÍDO!")
    print("=" * 70)
