#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os

# Adicionar o diretório raiz ao path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Configurar Flask para usar o banco correto
os.environ['FLASK_APP'] = 'run.py'
os.environ['FLASK_ENV'] = 'development'

from app import create_app
from app.extensoes import db
from app.midia.midia_model import Certificado
from datetime import datetime

def inicializar_banco():
    """Inicializa o banco e cria dados de exemplo"""
    app = create_app()
    
    with app.app_context():
        print("🔄 Inicializando banco de dados...")
        
        # Criar todas as tabelas
        db.create_all()
        print("✅ Tabelas criadas!")
        
        # Verificar se a coluna gênero existe, senão adicionar
        try:
            # Testar se consegue criar um certificado com gênero
            cert_teste = Certificado(
                nome_pessoa="Teste",
                tipo_certificado="Batismo",
                data_evento=datetime.now().date(),
                genero="masculino"
            )
            print("✅ Coluna gênero já existe!")
        except Exception as e:
            print(f"⚠️ Coluna gênero não existe ou erro: {e}")
            # Adicionar coluna se não existir
            try:
                db.engine.execute("ALTER TABLE certificados ADD COLUMN genero VARCHAR(10) DEFAULT 'masculino'")
                print("✅ Coluna gênero adicionada!")
            except Exception as e2:
                print(f"❌ Erro ao adicionar coluna: {e2}")
        
        # Limpar certificados existentes
        Certificado.query.delete()
        
        # Criar certificados de exemplo
        certificados_exemplo = [
            # Apresentações
            Certificado(
                nome_pessoa='Ana Sofia Mendes',
                tipo_certificado='Apresentação',
                data_evento=datetime(2024, 11, 5).date(),
                local_evento='Igreja OBPC Tietê',
                pastor_responsavel='Pastor Marcos Silva',
                padrinhos='João Mendes e Maria Mendes',
                observacoes='Apresentação da pequena Ana',
                genero='feminino'
            ),
            Certificado(
                nome_pessoa='Pedro Henrique Costa',
                tipo_certificado='Apresentação',
                data_evento=datetime(2024, 10, 20).date(),
                local_evento='Igreja OBPC Tietê',
                pastor_responsavel='Pastor Marcos Silva',
                padrinhos='Carlos Costa e Ana Costa',
                observacoes='Apresentação do pequeno Pedro',
                genero='masculino'
            ),
            Certificado(
                nome_pessoa='Isabella Santos',
                tipo_certificado='Apresentação',
                data_evento=datetime(2024, 9, 15).date(),
                local_evento='Igreja OBPC Tietê',
                pastor_responsavel='Pastor Marcos Silva',
                padrinhos='Roberto Santos e Lucia Santos',
                observacoes='Apresentação da pequena Isabella',
                genero='feminino'
            ),
            
            # Batismos
            Certificado(
                nome_pessoa='Carlos Roberto Silva',
                tipo_certificado='Batismo',
                data_evento=datetime(2024, 11, 3).date(),
                local_evento='Igreja OBPC Tietê',
                pastor_responsavel='Pastor Marcos Silva',
                observacoes='Batismo realizado com alegria',
                genero='masculino'
            ),
            Certificado(
                nome_pessoa='Mariana Oliveira',
                tipo_certificado='Batismo',
                data_evento=datetime(2024, 10, 27).date(),
                local_evento='Igreja OBPC Tietê',
                pastor_responsavel='Pastor Marcos Silva',
                observacoes='Nova vida em Cristo',
                genero='feminino'
            ),
            Certificado(
                nome_pessoa='João Paulo Santos',
                tipo_certificado='Batismo',
                data_evento=datetime(2024, 10, 13).date(),
                local_evento='Igreja OBPC Tietê',
                pastor_responsavel='Pastor Marcos Silva',
                observacoes='Testemunho público de fé',
                genero='masculino'
            ),
        ]
        
        for certificado in certificados_exemplo:
            db.session.add(certificado)
        
        db.session.commit()
        
        # Verificar resultado
        total = Certificado.query.count()
        print(f"✅ {total} certificados de exemplo criados!")
        
        # Listar certificados
        certificados = Certificado.query.order_by(Certificado.id.desc()).all()
        print("\n📋 Certificados criados:")
        for cert in certificados:
            icone = "👧" if cert.genero == 'feminino' else "👦"
            print(f"   {icone} {cert.nome_pessoa} - {cert.tipo_certificado} ({cert.genero})")
        
        print(f"\n🌐 TESTE NO NAVEGADOR:")
        print(f"Lista: http://127.0.0.1:5000/midia/certificados")
        print(f"Novo: http://127.0.0.1:5000/midia/certificados/novo")
        
        print(f"\n🎉 BANCO CONFIGURADO COM SUCESSO!")

if __name__ == "__main__":
    print("=== INICIALIZANDO BANCO DE CERTIFICADOS ===\n")
    inicializar_banco()