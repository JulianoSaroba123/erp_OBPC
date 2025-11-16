#!/usr/bin/env python3
"""
Script para verificar e testar login direto
"""

import sys
import os

# Adicionar o diretório raiz ao path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from app.usuario.usuario_model import Usuario

def verificar_usuario_admin():
    """Verifica se o usuário admin existe"""
    
    app = create_app()
    
    with app.app_context():
        print("🔍 Verificando usuário admin...")
        
        # Buscar usuário admin
        admin = Usuario.query.filter_by(email='admin@obpc.com').first()
        
        if not admin:
            print("❌ Usuário admin não encontrado!")
            print("Execute: python criar_admin.py")
            return False
        
        print(f"✅ Usuário admin encontrado:")
        print(f"   ID: {admin.id}")
        print(f"   Nome: {admin.nome}")
        print(f"   Email: {admin.email}")
        
        # Testar senha
        if admin.check_senha('123456'):
            print("✅ Senha '123456' está correta")
        else:
            print("❌ Senha '123456' está incorreta")
            return False
        
        # Verificar método UserMixin
        print(f"✅ is_authenticated: {admin.is_authenticated}")
        print(f"✅ is_active: {admin.is_active}")
        print(f"✅ is_anonymous: {admin.is_anonymous}")
        print(f"✅ get_id(): {admin.get_id()}")
        
        return True

def testar_user_loader():
    """Testa se o user_loader está funcionando"""
    
    app = create_app()
    
    with app.app_context():
        print("\n🔍 Testando user_loader...")
        
        from app.extensoes import login_manager
        
        # Buscar admin para pegar o ID
        admin = Usuario.query.filter_by(email='admin@obpc.com').first()
        if not admin:
            print("❌ Admin não encontrado")
            return False
        
        # Testar user_loader
        user_id = str(admin.id)
        loaded_user = login_manager._user_callback(user_id)
        
        if loaded_user:
            print(f"✅ user_loader funcionando")
            print(f"   Carregou usuário: {loaded_user.nome}")
            return True
        else:
            print("❌ user_loader não funcionou")
            return False

if __name__ == "__main__":
    print("=" * 50)
    print("🔐 DIAGNÓSTICO DE LOGIN")
    print("=" * 50)
    
    # Verificar usuário
    if not verificar_usuario_admin():
        sys.exit(1)
    
    # Testar user_loader
    if not testar_user_loader():
        sys.exit(1)
    
    print("\n" + "=" * 50)
    print("✅ TUDO OK - Sistema de login funcionando!")
    print("=" * 50)