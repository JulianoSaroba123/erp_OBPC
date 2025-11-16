#!/usr/bin/env python3
"""
Script para atualizar o banco de dados com o sistema de níveis de acesso
e criar usuários de exemplo para teste
"""

import sys
import os

# Adicionar o diretório raiz ao path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from app.usuario.usuario_model import Usuario, NivelAcesso
from datetime import datetime

def atualizar_banco_niveis_acesso():
    """Atualiza o banco de dados com as novas colunas de nível de acesso"""
    
    app = create_app()
    
    with app.app_context():
        print("🔄 Atualizando banco de dados para sistema de níveis de acesso...")
        print("=" * 60)
        
        try:
            # Criar as tabelas com os novos campos
            db.create_all()
            print("✅ Tabelas criadas/atualizadas com sucesso")
            
            # Verificar se o usuário admin existe
            admin_existente = Usuario.query.filter_by(email='admin@obpc.com').first()
            
            if admin_existente:
                # Atualizar usuário admin existente
                admin_existente.nivel_acesso = 'master'
                print(f"✅ Usuário admin atualizado para nível Master")
            else:
                # Criar usuário master
                admin = Usuario(
                    nome='Administrador Master',
                    email='admin@obpc.com',
                    nivel_acesso='master',
                    perfil='Master',
                    ativo=True
                )
                admin.set_senha('123456')
                db.session.add(admin)
                print("✅ Usuário Master criado: admin@obpc.com / 123456")
            
            # Criar usuários de exemplo para cada nível
            usuarios_exemplo = [
                {
                    'nome': 'João Administrador',
                    'email': 'admin@exemplo.com',
                    'nivel_acesso': 'administrador',
                    'senha': '123456'
                },
                {
                    'nome': 'Maria Tesoureira',
                    'email': 'tesoureiro@exemplo.com',
                    'nivel_acesso': 'tesoureiro',
                    'senha': '123456'
                },
                {
                    'nome': 'Pedro Secretário',
                    'email': 'secretario@exemplo.com',
                    'nivel_acesso': 'secretario',
                    'senha': '123456'
                },
                {
                    'nome': 'Ana Mídia',
                    'email': 'midia@exemplo.com',
                    'nivel_acesso': 'midia',
                    'senha': '123456'
                },
                {
                    'nome': 'Carlos Membro',
                    'email': 'membro@exemplo.com',
                    'nivel_acesso': 'membro',
                    'senha': '123456'
                }
            ]
            
            print("\n📋 Criando usuários de exemplo...")
            criados = 0
            
            for dados in usuarios_exemplo:
                existente = Usuario.query.filter_by(email=dados['email']).first()
                if not existente:
                    usuario = Usuario(
                        nome=dados['nome'],
                        email=dados['email'],
                        nivel_acesso=dados['nivel_acesso'],
                        perfil=dados['nivel_acesso'].title(),
                        ativo=True,
                        criado_por=1  # Criado pelo admin
                    )
                    usuario.set_senha(dados['senha'])
                    db.session.add(usuario)
                    criados += 1
                    print(f"   ✅ {dados['nome']} ({dados['nivel_acesso']})")
                else:
                    # Atualizar nível se necessário
                    existente.nivel_acesso = dados['nivel_acesso']
                    print(f"   🔄 {dados['nome']} atualizado")
            
            # Salvar todas as alterações
            db.session.commit()
            
            print(f"\n✅ {criados} novos usuários criados")
            print("\n" + "=" * 60)
            print("🎉 SISTEMA DE NÍVEIS DE ACESSO IMPLEMENTADO!")
            print("=" * 60)
            
            print("\n📊 USUÁRIOS DISPONÍVEIS:")
            print("-" * 40)
            
            usuarios = Usuario.query.order_by(Usuario.nivel_acesso, Usuario.nome).all()
            for usuario in usuarios:
                status = "✅ Ativo" if usuario.ativo else "❌ Inativo"
                print(f"{usuario.email:<25} | {usuario.get_nome_nivel():<12} | {status}")
            
            print("\n🔐 NÍVEIS DE ACESSO:")
            print("-" * 40)
            print("Master:        Acesso total ao sistema")
            print("Administrador: Gerencia usuários + todos módulos")
            print("Tesoureiro:    Apenas módulo financeiro")
            print("Secretário:    Secretaria, membros e obreiros")
            print("Mídia:         Mídia e departamentos")
            print("Membro:        Apenas dashboard e eventos")
            
            print("\n🚀 COMO TESTAR:")
            print("-" * 40)
            print("1. Reinicie o servidor: python run.py")
            print("2. Acesse: http://127.0.0.1:5000")
            print("3. Teste os diferentes usuários acima")
            print("4. Senha padrão para todos: 123456")
            
            return True
            
        except Exception as e:
            print(f"❌ Erro ao atualizar banco: {str(e)}")
            db.session.rollback()
            return False

if __name__ == "__main__":
    print("SISTEMA DE NÍVEIS DE ACESSO - OBPC")
    print("=" * 60)
    
    sucesso = atualizar_banco_niveis_acesso()
    
    if sucesso:
        print("\n🎉 ATUALIZAÇÃO CONCLUÍDA COM SUCESSO!")
    else:
        print("\n❌ FALHA NA ATUALIZAÇÃO")
        sys.exit(1)