#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script para adicionar coluna hora_notificacao_automatica ao banco Render
Execute isso no Shell do Render quando o deploy falhar com erro de coluna
"""

from app import create_app, db
from sqlalchemy import text, inspect

def adicionar_coluna():
    """Adiciona coluna hora_notificacao_automatica à tabela"""
    app = create_app()
    
    with app.app_context():
        try:
            print("Verificando se coluna existe...")
            
            # Inspecionar colunas atuais
            inspector = inspect(db.engine)
            columns = [col['name'] for col in inspector.get_columns('configuracao_notificacoes')]
            print(f"Colunas existentes: {columns}")
            
            if 'hora_notificacao_automatica' in columns:
                print("✅ Coluna já existe!")
                return True
            
            print("Adicionando coluna hora_notificacao_automatica...")
            
            # Usar comando SQL direto para PostgreSQL - fazer em passos
            # Passo 1: Adicionar coluna
            db.session.execute(text(
                "ALTER TABLE configuracao_notificacoes "
                "ADD COLUMN hora_notificacao_automatica VARCHAR(5)"
            ))
            print("  - Coluna adicionada")
            
            # Passo 2: Atualizar linhas existentes
            db.session.execute(text(
                "UPDATE configuracao_notificacoes SET hora_notificacao_automatica = '08:00'"
            ))
            print("  - Dados preenchidos")
            
            # Passo 3: Tornar NOT NULL
            db.session.execute(text(
                "ALTER TABLE configuracao_notificacoes "
                "ALTER COLUMN hora_notificacao_automatica SET NOT NULL"
            ))
            print("  - Coluna ajustada")
            
            db.session.commit()
            
            print("✅ Coluna adicionada com sucesso!")
            return True
            
        except Exception as e:
            db.session.rollback()
            erro_str = str(e).lower()
            
            # Se a coluna já existe, não é erro
            if 'already exists' in erro_str or 'already' in erro_str:
                print("✅ Coluna já existe (ou foi criada antes)!")
                return True
            
            print(f"❌ Erro: {str(e)}")
            import traceback
            traceback.print_exc()
            return False

if __name__ == '__main__':
    sucesso = adicionar_coluna()
    exit(0 if sucesso else 1)
