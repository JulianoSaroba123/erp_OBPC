#!/usr/bin/env python3
"""
Script para verificar e criar tabelas do banco de dados
"""

from app import create_app
from app.extensoes import db

def verificar_e_criar_tabelas():
    """Verifica se as tabelas existem e cria se necessário"""
    app = create_app()
    
    with app.app_context():
        try:
            # Importa todos os modelos para garantir que estejam registrados
            from app.usuario.usuario_model import Usuario
            from app.membros.membros_model import Membro
            
            print("=== Verificando Banco de Dados ===")
            
            # Cria todas as tabelas
            db.create_all()
            print("✅ Tabelas criadas/verificadas com sucesso!")
            
            # Verifica se as tabelas existem
            inspector = db.inspect(db.engine)
            tabelas = inspector.get_table_names()
            
            print(f"\n📋 Tabelas encontradas: {tabelas}")
            
            # Verifica usuários
            usuarios = Usuario.query.all()
            print(f"👤 Usuários cadastrados: {len(usuarios)}")
            
            # Verifica membros
            membros = Membro.query.all()
            print(f"👥 Membros cadastrados: {len(membros)}")
            
            return True
            
        except Exception as e:
            print(f"❌ Erro ao verificar banco: {str(e)}")
            return False

if __name__ == "__main__":
    verificar_e_criar_tabelas()