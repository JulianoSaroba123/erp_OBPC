"""
Script para corrigir problemas no banco de dados
"""
from app import create_app
from app.extensoes import db
from sqlalchemy import text
import os

def corrigir_banco():
    app = create_app()
    with app.app_context():
        print("Verificando integridade do banco...")
        
        try:
            # Verificar se há corrupção no banco
            result = db.session.execute(text("PRAGMA integrity_check")).fetchall()
            print(f"Integridade do banco: {result[0][0]}")
            
            # Limpar cache do SQLAlchemy
            db.session.expunge_all()
            db.session.commit()
            
            # Recriar conexão
            db.engine.dispose()
            
            # Verificar se as tabelas existem
            from app.usuario.usuario_model import Usuario
            from app.financeiro.financeiro_model import Lancamento
            
            print(f"Usuários: {Usuario.query.count()}")
            print(f"Lançamentos: {Lancamento.query.count()}")
            
            # Verificar se há usuários com email problemático
            usuarios = Usuario.query.all()
            for u in usuarios:
                print(f"ID: {u.id}, Email: {u.email}, Nome: {u.nome}")
            
            print("✓ Banco verificado com sucesso!")
            
        except Exception as e:
            print(f"Erro ao verificar banco: {e}")
            
            # Tentar recriar as tabelas se necessário
            try:
                print("Tentando recriar estrutura do banco...")
                db.create_all()
                print("✓ Estrutura recriada!")
            except Exception as e2:
                print(f"Erro ao recriar: {e2}")

if __name__ == "__main__":
    corrigir_banco()