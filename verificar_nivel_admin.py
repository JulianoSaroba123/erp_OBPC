#!/usr/bin/env python3
"""
Script para verificar o nível de acesso do usuário admin
"""

import sqlite3

def verificar_nivel_admin():
    """Verifica o nível de acesso do usuário admin"""
    print("🔍 VERIFICANDO NÍVEL DE ACESSO DO ADMIN")
    print("=" * 45)
    
    try:
        conn = sqlite3.connect('igreja.db')
        cursor = conn.cursor()
        
        # Verificar usuário admin
        cursor.execute("SELECT id, email, nivel_acesso, ativo FROM usuarios WHERE email = ?", ('admin@obpc.com',))
        admin = cursor.fetchone()
        
        if admin:
            print(f"✅ Usuário admin encontrado:")
            print(f"  - ID: {admin[0]}")
            print(f"  - Email: {admin[1]}")
            print(f"  - Nível de acesso: {admin[2]}")
            print(f"  - Ativo: {'Sim' if admin[3] else 'Não'}")
            
            # Verificar se o nível está correto
            if admin[2] == 'master':
                print("✅ Nível correto: MASTER (tem acesso a tudo)")
            elif admin[2] == 'administrador':
                print("✅ Nível correto: ADMINISTRADOR (tem acesso a quase tudo)")
            else:
                print(f"⚠️ Nível '{admin[2]}' pode ter acesso limitado")
                print("💡 Vou atualizar para 'master'...")
                
                cursor.execute("UPDATE usuarios SET nivel_acesso = ? WHERE email = ?", ('master', 'admin@obpc.com'))
                conn.commit()
                print("✅ Nível atualizado para 'master'!")
        else:
            print("❌ Usuário admin não encontrado!")
        
        # Listar todos os usuários e seus níveis
        print("\n📋 TODOS OS USUÁRIOS:")
        cursor.execute("SELECT id, email, nivel_acesso, ativo FROM usuarios")
        usuarios = cursor.fetchall()
        
        for user in usuarios:
            status = "✅" if user[3] else "❌"
            print(f"  {status} {user[1]} - {user[2]}")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Erro: {e}")

if __name__ == "__main__":
    verificar_nivel_admin()