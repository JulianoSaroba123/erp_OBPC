#!/usr/bin/env python3
"""
Migração do banco de dados para adicionar colunas de nível de acesso
"""

import sys
import os
import sqlite3

# Adicionar o diretório raiz ao path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from app.usuario.usuario_model import Usuario

def migrar_banco_niveis_acesso():
    """Adiciona as novas colunas ao banco existente"""
    
    app = create_app()
    
    with app.app_context():
        print("🔄 MIGRAÇÃO: Adicionando colunas de nível de acesso...")
        print("=" * 60)
        
        try:
            # Conectar diretamente ao SQLite para fazer ALTER TABLE
            db_path = 'instance/igreja.db'  # Caminho fixo baseado no que encontramos
            
            print(f"📁 Banco de dados: {db_path}")
            
            # Verificar se o arquivo existe
            if not os.path.exists(db_path):
                print(f"❌ Arquivo não encontrado: {db_path}")
                print("� Criando banco de dados...")
                # Criar todas as tabelas usando SQLAlchemy
                db.create_all()
                print("✅ Banco criado!")
            
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # Verificar se a tabela usuarios existe
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='usuarios'")
            if not cursor.fetchone():
                print("❌ Tabela 'usuarios' não encontrada. Criando tabelas...")
                # Criar todas as tabelas usando SQLAlchemy
                conn.close()
                db.create_all()
                print("✅ Tabelas criadas!")
                
                # Reconectar
                conn = sqlite3.connect(db_path)
                cursor = conn.cursor()
            
            # Verificar se as colunas já existem
            cursor.execute("PRAGMA table_info(usuarios)")
            colunas_existentes = [col[1] for col in cursor.fetchall()]
            print(f"📋 Colunas existentes: {colunas_existentes}")
            
            colunas_adicionar = []
            
            if 'nivel_acesso' not in colunas_existentes:
                colunas_adicionar.append(("nivel_acesso", "VARCHAR(20) DEFAULT 'membro'"))
            
            if 'criado_por' not in colunas_existentes:
                colunas_adicionar.append(("criado_por", "INTEGER"))
            
            if 'criado_em' not in colunas_existentes:
                colunas_adicionar.append(("criado_em", "DATETIME"))
            
            if 'ultimo_login' not in colunas_existentes:
                colunas_adicionar.append(("ultimo_login", "DATETIME"))
            
            if colunas_adicionar:
                print(f"\n🔧 Adicionando {len(colunas_adicionar)} colunas...")
                
                for nome_coluna, definicao in colunas_adicionar:
                    try:
                        sql = f"ALTER TABLE usuarios ADD COLUMN {nome_coluna} {definicao}"
                        print(f"   ➕ {nome_coluna}")
                        cursor.execute(sql)
                    except sqlite3.OperationalError as e:
                        if "duplicate column name" in str(e):
                            print(f"   ✅ {nome_coluna} (já existe)")
                        else:
                            raise e
                
                conn.commit()
                print("✅ Colunas adicionadas com sucesso!")
            else:
                print("✅ Todas as colunas já existem!")
            
            # Atualizar usuários existentes para definir nível padrão
            print("\n🔄 Atualizando usuários existentes...")
            
            # Definir admin como master
            cursor.execute("UPDATE usuarios SET nivel_acesso = 'master' WHERE email = 'admin@obpc.com'")
            
            # Definir outros como membro se não tiverem nível
            cursor.execute("UPDATE usuarios SET nivel_acesso = 'membro' WHERE nivel_acesso IS NULL OR nivel_acesso = ''")
            
            conn.commit()
            conn.close()
            
            print("✅ Migração concluída!")
            
            # Agora usar SQLAlchemy para operações mais complexas
            print("\n🔄 Verificando com SQLAlchemy...")
            
            usuarios = Usuario.query.all()
            print(f"📊 Total de usuários: {len(usuarios)}")
            
            for usuario in usuarios:
                print(f"   👤 {usuario.nome} - {usuario.nivel_acesso}")
            
            return True
            
        except Exception as e:
            print(f"❌ Erro na migração: {str(e)}")
            return False

if __name__ == "__main__":
    print("MIGRAÇÃO DE BANCO - NÍVEIS DE ACESSO")
    print("=" * 60)
    
    sucesso = migrar_banco_niveis_acesso()
    
    if sucesso:
        print("\n🎉 MIGRAÇÃO CONCLUÍDA!")
        print("Agora execute: python implementar_niveis_acesso.py")
    else:
        print("\n❌ FALHA NA MIGRAÇÃO")
        sys.exit(1)