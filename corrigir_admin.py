#!/usr/bin/env python3
"""
Script para verificar e corrigir o nível do usuário admin
"""

import sqlite3
from werkzeug.security import generate_password_hash

def verificar_e_corrigir_admin():
    """Verifica e corrige o usuário admin"""
    print("🔧 VERIFICANDO USUÁRIO ADMINISTRADOR")
    print("=" * 45)
    
    try:
        conn = sqlite3.connect('igreja.db')
        cursor = conn.cursor()
        
        # Verificar estrutura da tabela usuarios
        cursor.execute("PRAGMA table_info(usuarios)")
        colunas = cursor.fetchall()
        print("📋 Estrutura da tabela usuarios:")
        for col in colunas:
            print(f"  - {col[1]} ({col[2]})")
        
        # Verificar usuário admin atual
        cursor.execute("SELECT id, email, nivel_acesso, ativo FROM usuarios WHERE email = ?", ('admin@obpc.com',))
        admin = cursor.fetchone()
        
        if admin:
            print(f"\n👤 Usuário admin encontrado:")
            print(f"  - ID: {admin[0]}")
            print(f"  - Email: {admin[1]}")
            print(f"  - Nível de acesso: {admin[2]}")
            print(f"  - Ativo: {admin[3]}")
            
            # Verificar se o nível está correto
            if admin[2] != 'Admin':
                print(f"\n🔧 Corrigindo nível de acesso de '{admin[2]}' para 'Admin'...")
                cursor.execute("UPDATE usuarios SET nivel_acesso = 'Admin' WHERE email = ?", ('admin@obpc.com',))
                conn.commit()
                print("✅ Nível de acesso corrigido!")
            else:
                print("✅ Nível de acesso já está correto!")
            
            # Verificar se está ativo
            if admin[3] != 1:
                print(f"\n🔧 Ativando usuário...")
                cursor.execute("UPDATE usuarios SET ativo = 1 WHERE email = ?", ('admin@obpc.com',))
                conn.commit()
                print("✅ Usuário ativado!")
            else:
                print("✅ Usuário já está ativo!")
                
        else:
            print("\n❌ Usuário admin não encontrado! Criando...")
            # Criar usuário admin
            senha_hash = generate_password_hash('123456')
            cursor.execute("""
                INSERT INTO usuarios (email, senha_hash, nivel_acesso, ativo, data_criacao)
                VALUES (?, ?, 'Admin', 1, datetime('now'))
            """, ('admin@obpc.com', senha_hash))
            conn.commit()
            print("✅ Usuário admin criado!")
        
        # Verificar todos os usuários
        print("\n👥 TODOS OS USUÁRIOS:")
        cursor.execute("SELECT id, email, nivel_acesso, ativo FROM usuarios")
        usuarios = cursor.fetchall()
        
        for user in usuarios:
            status = "🟢 Ativo" if user[3] else "🔴 Inativo"
            print(f"  - ID: {user[0]} | {user[1]} | {user[2]} | {status}")
        
        # Verificar final do admin
        print("\n🔍 VERIFICAÇÃO FINAL DO ADMIN:")
        cursor.execute("SELECT email, nivel_acesso, ativo FROM usuarios WHERE email = ?", ('admin@obpc.com',))
        admin_final = cursor.fetchone()
        
        if admin_final:
            print(f"  Email: {admin_final[0]}")
            print(f"  Nível: {admin_final[1]}")
            print(f"  Ativo: {'Sim' if admin_final[2] else 'Não'}")
            
            if admin_final[1] == 'Admin' and admin_final[2] == 1:
                print("\n✅ USUÁRIO ADMIN ESTÁ CONFIGURADO CORRETAMENTE!")
                print("📧 Email: admin@obpc.com")
                print("🔑 Senha: 123456")
                print("🎯 Nível: Admin")
            else:
                print("\n❌ Ainda há problemas com o usuário admin")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Erro: {e}")

if __name__ == "__main__":
    verificar_e_corrigir_admin()