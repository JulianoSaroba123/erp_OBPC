from app import create_app
from app.extensoes import db
from sqlalchemy import inspect, text

app = create_app()

with app.app_context():
    # Verificar quais colunas existem na tabela conciliacao_historico
    inspector = inspect(db.engine)
    colunas_existentes = [col['name'] for col in inspector.get_columns('conciliacao_historico')]
    
    print("Colunas existentes na tabela conciliacao_historico:")
    for col in colunas_existentes:
        print(f"  - {col}")
    
    # Colunas que deveriam existir no modelo atual
    colunas_esperadas = [
        'tipo_conciliacao', 'tempo_execucao', 'regras_aplicadas'
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
        with db.engine.connect() as conn:
            if 'tipo_conciliacao' in colunas_faltando:
                conn.execute(text("ALTER TABLE conciliacao_historico ADD COLUMN tipo_conciliacao VARCHAR(20) DEFAULT 'manual'"))
                conn.commit()
                print("  ✓ tipo_conciliacao")
            
            if 'tempo_execucao' in colunas_faltando:
                conn.execute(text("ALTER TABLE conciliacao_historico ADD COLUMN tempo_execucao FLOAT"))
                conn.commit()
                print("  ✓ tempo_execucao")
            
            if 'regras_aplicadas' in colunas_faltando:
                conn.execute(text("ALTER TABLE conciliacao_historico ADD COLUMN regras_aplicadas TEXT"))
                conn.commit()
                print("  ✓ regras_aplicadas")
        
        print("\n✅ Schema conciliacao_historico atualizado com sucesso!")
    else:
        print("\n✅ Todas as colunas necessárias já existem!")
    
    # Verificar tabela conciliacao_pares
    print("\n" + "="*50)
    if 'conciliacao_pares' in inspector.get_table_names():
        colunas_pares = [col['name'] for col in inspector.get_columns('conciliacao_pares')]
        print("Colunas existentes na tabela conciliacao_pares:")
        for col in colunas_pares:
            print(f"  - {col}")
        
        # Verificar se precisa atualizar estrutura dos pares
        colunas_esperadas_pares = [
            'lancamento_manual_id', 'lancamento_importado_id', 
            'score_similaridade', 'regra_aplicada', 'metodo_conciliacao', 'ativo'
        ]
        
        colunas_faltando_pares = []
        for col in colunas_esperadas_pares:
            if col not in colunas_pares:
                colunas_faltando_pares.append(col)
        
        if colunas_faltando_pares:
            print(f"\nColunas em falta na tabela conciliacao_pares: {colunas_faltando_pares}")
            
            with db.engine.connect() as conn:
                if 'lancamento_manual_id' in colunas_faltando_pares:
                    conn.execute(text("ALTER TABLE conciliacao_pares ADD COLUMN lancamento_manual_id INTEGER"))
                    conn.commit()
                    print("  ✓ lancamento_manual_id")
                
                if 'lancamento_importado_id' in colunas_faltando_pares:
                    conn.execute(text("ALTER TABLE conciliacao_pares ADD COLUMN lancamento_importado_id INTEGER"))
                    conn.commit()
                    print("  ✓ lancamento_importado_id")
                
                if 'score_similaridade' in colunas_faltando_pares:
                    conn.execute(text("ALTER TABLE conciliacao_pares ADD COLUMN score_similaridade FLOAT"))
                    conn.commit()
                    print("  ✓ score_similaridade")
                
                if 'regra_aplicada' in colunas_faltando_pares:
                    conn.execute(text("ALTER TABLE conciliacao_pares ADD COLUMN regra_aplicada VARCHAR(200)"))
                    conn.commit()
                    print("  ✓ regra_aplicada")
                
                if 'metodo_conciliacao' in colunas_faltando_pares:
                    conn.execute(text("ALTER TABLE conciliacao_pares ADD COLUMN metodo_conciliacao VARCHAR(50) DEFAULT 'manual'"))
                    conn.commit()
                    print("  ✓ metodo_conciliacao")
                
                if 'ativo' in colunas_faltando_pares:
                    conn.execute(text("ALTER TABLE conciliacao_pares ADD COLUMN ativo BOOLEAN DEFAULT 1"))
                    conn.commit()
                    print("  ✓ ativo")
        else:
            print("✅ Tabela conciliacao_pares com todas as colunas!")
    else:
        print("❌ Tabela conciliacao_pares não existe!")