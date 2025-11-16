#!/usr/bin/env python3
"""
Script para testar o login e resolver problemas de sessão
"""

import sqlite3
from werkzeug.security import check_password_hash

def testar_login():
    """Testa o login diretamente no banco"""
    print("🔐 TESTANDO LOGIN")
    print("=" * 30)
    
    try:
        # Conectar ao banco
        conn = sqlite3.connect('igreja.db')
        cursor = conn.cursor()
        
        # Verificar se existe a tabela usuarios
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='usuarios'")
        if not cursor.fetchone():
            print("❌ Tabela 'usuarios' não existe!")
            return
        
        # Verificar usuários
        cursor.execute("SELECT id, email, senha_hash, ativo FROM usuarios")
        usuarios = cursor.fetchall()
        
        print(f"📊 Total de usuários: {len(usuarios)}")
        
        for user in usuarios:
            print(f"  - ID: {user[0]} | Email: {user[1]} | Ativo: {user[3]}")
        
        # Testar login do admin
        cursor.execute("SELECT id, email, senha_hash, ativo FROM usuarios WHERE email = ?", ('admin@obpc.com',))
        admin = cursor.fetchone()
        
        if admin:
            print(f"\n✅ Usuário admin encontrado:")
            print(f"  - ID: {admin[0]}")
            print(f"  - Email: {admin[1]}")
            print(f"  - Ativo: {admin[3]}")
            
            # Testar senha
            senha_teste = "123456"
            if check_password_hash(admin[2], senha_teste):
                print(f"  ✅ Senha '{senha_teste}' está correta!")
            else:
                print(f"  ❌ Senha '{senha_teste}' está incorreta!")
        else:
            print("❌ Usuário admin não encontrado!")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Erro: {e}")

if __name__ == "__main__":
    testar_login()