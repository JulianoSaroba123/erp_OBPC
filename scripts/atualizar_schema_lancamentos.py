from app import create_app
from app.extensoes import db
from sqlalchemy import inspect
import sqlite3

app = create_app()

with app.app_context():
    # Verificar quais colunas existem na tabela lancamentos
    inspector = inspect(db.engine)
    colunas_existentes = [col['name'] for col in inspector.get_columns('lancamentos')]
    
    print("Colunas existentes na tabela lancamentos:")
    for col in colunas_existentes:
        print(f"  - {col}")
    
    # Colunas que deveriam existir no modelo atual
    colunas_esperadas = [
        'hash_duplicata', 'banco_origem', 'documento_ref', 
        'conciliado_em', 'conciliado_por', 'par_conciliacao_id'
    ]
    
    print("\nColunas em falta:")
    colunas_faltando = []
    for col in colunas_esperadas:
        if col not in colunas_existentes:
            print(f"  - {col}")
            colunas_faltando.append(col)
    
    if colunas_faltando:
        print(f"\nAdicionando {len(colunas_faltando)} colunas...")
        
        # Executar ALTERs diretamente no SQLite
        from sqlalchemy import text
        with db.engine.connect() as conn:
            if 'hash_duplicata' in colunas_faltando:
                conn.execute(text("ALTER TABLE lancamentos ADD COLUMN hash_duplicata VARCHAR(64)"))
                conn.commit()
                print("  ✓ hash_duplicata")
            
            if 'banco_origem' in colunas_faltando:
                conn.execute(text("ALTER TABLE lancamentos ADD COLUMN banco_origem VARCHAR(100)"))
                conn.commit()
                print("  ✓ banco_origem")
            
            if 'documento_ref' in colunas_faltando:
                conn.execute(text("ALTER TABLE lancamentos ADD COLUMN documento_ref VARCHAR(50)"))
                conn.commit()
                print("  ✓ documento_ref")
            
            if 'conciliado_em' in colunas_faltando:
                conn.execute(text("ALTER TABLE lancamentos ADD COLUMN conciliado_em DATETIME"))
                conn.commit()
                print("  ✓ conciliado_em")
            
            if 'conciliado_por' in colunas_faltando:
                conn.execute(text("ALTER TABLE lancamentos ADD COLUMN conciliado_por VARCHAR(100)"))
                conn.commit()
                print("  ✓ conciliado_por")
            
            if 'par_conciliacao_id' in colunas_faltando:
                conn.execute(text("ALTER TABLE lancamentos ADD COLUMN par_conciliacao_id INTEGER"))
                conn.commit()
                print("  ✓ par_conciliacao_id")
        
        # Verificar se todas as tabelas necessárias existem
        tabelas_existentes = inspector.get_table_names()
        print(f"\nTabelas existentes: {tabelas_existentes}")
        
        if 'importacao_extrato' not in tabelas_existentes:
            print("\nCriando tabela importacao_extrato...")
            db.create_all()
            print("  ✓ importacao_extrato criada")
        
        print("\n✅ Schema atualizado com sucesso!")
    else:
        print("\n✅ Todas as colunas necessárias já existem!")