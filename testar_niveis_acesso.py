#!/usr/bin/env python3
"""
Teste do Sistema de Níveis de Acesso
Sistema OBPC - Organização Brasileira de Pastores e Cooperadores
"""

import sys
import os

# Adicionar o diretório do projeto ao path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from app.usuario.usuario_model import Usuario, NivelAcesso

def testar_sistema_niveis():
    """Testa o sistema de níveis de acesso"""
    
    app = create_app()
    
    with app.app_context():
        print("🔍 Testando Sistema de Níveis de Acesso...")
        print("=" * 60)
        
        # Buscar todos os usuários
        usuarios = Usuario.query.all()
        
        if not usuarios:
            print("❌ Nenhum usuário encontrado no banco de dados!")
            return
        
        print(f"📊 Total de usuários cadastrados: {len(usuarios)}")
        print()
        
        # Testar cada usuário
        for usuario in usuarios:
            print(f"👤 Usuário: {usuario.nome} ({usuario.email})")
            print(f"🎯 Nível de Acesso: {usuario.nivel_acesso}")
            print(f"📅 Criado em: {usuario.criado_em}")
            print(f"🔐 Último login: {usuario.ultimo_login or 'Nunca'}")
            
            # Testar permissões
            print("🔑 Permissões:")
            print(f"   • Financeiro: {'✅' if usuario.tem_acesso_financeiro() else '❌'}")
            print(f"   • Secretaria: {'✅' if usuario.tem_acesso_secretaria() else '❌'}")
            print(f"   • Mídia: {'✅' if usuario.tem_acesso_midia() else '❌'}")
            print(f"   • Membros: {'✅' if usuario.tem_acesso_membros() else '❌'}")
            print(f"   • Obreiros: {'✅' if usuario.tem_acesso_obreiros() else '❌'}")
            print(f"   • Departamentos: {'✅' if usuario.tem_acesso_departamentos() else '❌'}")
            print(f"   • Configurações: {'✅' if usuario.tem_acesso_configuracoes() else '❌'}")
            print(f"   • Gerenciar Usuários: {'✅' if usuario.pode_gerenciar_usuarios() else '❌'}")
            
            # Menu principal
            menu = usuario.get_menu_principal()
            print(f"🏠 Menu Principal: {menu}")
            
            print("-" * 40)
        
        # Verificar níveis de acesso disponíveis
        print("\n📋 Níveis de Acesso Disponíveis:")
        for nivel in NivelAcesso:
            count = Usuario.query.filter_by(nivel_acesso=nivel.value).count()
            print(f"   • {nivel.value}: {count} usuário(s)")
        
        print("\n✅ Teste concluído com sucesso!")

if __name__ == "__main__":
    testar_sistema_niveis()