#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Script para criar TODAS as tabelas no PostgreSQL do Render
Execute este script UMA VEZ para criar as tabelas no banco de produção
"""

from app import create_app
from app.extensoes import db

# Importar TODOS os modelos para garantir que sejam criados
from app.usuario.usuario_model import Usuario
from app.configuracoes.configuracoes_model import Configuracao
from app.departamentos.departamentos_model import Departamento, CronogramaDepartamento, AulaDepartamento
from app.financeiro.financeiro_model import Lancamento, Categoria
from app.financeiro.projeto_model import Projeto
from app.membros.membro_model import Membro
from app.secretaria.atas.atas_model import Ata
from app.secretaria.oficios.oficios_model import Oficio
from app.eventos.eventos_model import Evento

app = create_app()

with app.app_context():
    print("=" * 70)
    print("CRIANDO TODAS AS TABELAS NO BANCO DE DADOS")
    print("=" * 70)
    
    # Criar TODAS as tabelas
    db.create_all()
    
    print("\n✅ Tabelas criadas com sucesso!")
    print("\nTabelas no banco:")
    
    # Listar tabelas criadas
    from sqlalchemy import inspect
    inspector = inspect(db.engine)
    
    for table_name in inspector.get_table_names():
        print(f"  ✓ {table_name}")
    
    print("\n" + "=" * 70)
    print("CONCLUÍDO!")
    print("=" * 70)
