#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Script para verificar/criar usuário pastor para teste da funcionalidade
"""

import sys
import os
sys.path.append(os.path.abspath('.'))

from app import create_app, db
from app.usuario.usuario_model import Usuario
from app.config import Config

app = create_app()

with app.app_context():
    print("=== VERIFICANDO USUÁRIOS EXISTENTES ===")
    
    usuarios = Usuario.query.all()
    
    if not usuarios:
        print("Nenhum usuário encontrado. Criando usuário pastor para teste...")
        
        # Criar usuário pastor
        pastor = Usuario(
            nome="Pastor Administrador",
            email="pastor@obpc.com.br",
            perfil="Pastor",
            ativo=True
        )
        pastor.set_senha("pastor123")
        
        db.session.add(pastor)
        db.session.commit()
        
        print("✅ Usuário pastor criado com sucesso!")
        print("Email: pastor@obpc.com.br")
        print("Senha: pastor123")
        print("Perfil: Pastor")
    else:
        print(f"Encontrados {len(usuarios)} usuários:")
        
        pastor_existe = False
        
        for usuario in usuarios:
            print(f"- {usuario.nome} ({usuario.email}) - Perfil: {usuario.perfil}")
            if usuario.perfil == "Pastor":
                pastor_existe = True
        
        if not pastor_existe:
            print("\n⚠️  Nenhum usuário com perfil 'Pastor' encontrado!")
            print("Promovendo primeiro usuário a Pastor...")
            
            primeiro_usuario = usuarios[0]
            primeiro_usuario.perfil = "Pastor"
            db.session.commit()
            
            print(f"✅ {primeiro_usuario.nome} promovido a Pastor!")
        else:
            print("\n✅ Usuário com perfil Pastor já existe!")
    
    print("\n=== RESUMO FINAL ===")
    usuarios_atualizados = Usuario.query.all()
    for usuario in usuarios_atualizados:
        status = "🔑 PASTOR" if usuario.perfil == "Pastor" else f"👤 {usuario.perfil}"
        print(f"{status}: {usuario.nome} ({usuario.email})")