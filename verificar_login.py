#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Verificar Status de Login - Sistema OBPC
Igreja O Brasil para Cristo - Tietê/SP

Script para verificar se existe usuário admin e qual o status de login
"""

import sys
import os

# Adicionar o diretório raiz ao path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from app.usuario.usuario_model import Usuario

def verificar_usuarios():
    """Verifica os usuários no sistema"""
    print("🔧 VERIFICAÇÃO DE USUÁRIOS")
    print("=" * 40)
    
    # Criar app
    app = create_app()
    
    with app.app_context():
        try:
            # Listar todos os usuários
            usuarios = Usuario.query.all()
            print(f"📋 Total de usuários no sistema: {len(usuarios)}")
            
            for usuario in usuarios:
                print(f"👤 ID: {usuario.id}")
                print(f"   Nome: {usuario.nome}")
                print(f"   Email: {usuario.email}")
                print(f"   Ativo: {usuario.ativo}")
                print(f"   Perfil: {usuario.perfil}")
                print("-" * 30)
                
            # Verificar se existe usuário com email admin
            admin = Usuario.query.filter_by(email='admin@obpc.org.br').first()
            if not admin:
                # Tentar encontrar qualquer usuário admin
                admin = Usuario.query.filter(Usuario.email.like('%admin%')).first()
            
            if admin:
                print("✅ Usuário admin encontrado")
                print(f"   Email: {admin.email}")
                print(f"   Senha hash: {admin.senha_hash[:20]}...")
                
                # Testar login com senhas comuns
                senhas_teste = ['admin123', 'admin', '123456', 'password', '123', 'obpc2024']
                for senha in senhas_teste:
                    if admin.check_senha(senha):
                        print(f"✅ Senha '{senha}' confere!")
                        break
                else:
                    print("❌ Nenhuma senha testada funcionou")
            else:
                print("❌ Usuário admin não encontrado")
                print("📋 Primeiro usuário encontrado:")
                if usuarios:
                    primeiro = usuarios[0]
                    print(f"   Email: {primeiro.email}")
                    # Testar senhas
                    senhas_teste = ['admin123', 'admin', '123456', 'password']
                    for senha in senhas_teste:
                        if primeiro.check_senha(senha):
                            print(f"✅ Senha '{senha}' confere para {primeiro.email}!")
                            break
                
        except Exception as e:
            print(f"❌ Erro durante a verificação: {str(e)}")
            import traceback
            traceback.print_exc()

if __name__ == '__main__':
    verificar_usuarios()