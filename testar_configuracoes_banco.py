"""
Script para testar as configurações no banco de dados
"""
from app import create_app
from app.extensoes import db
from app.configuracoes.configuracoes_model import Configuracao

app = create_app()

with app.app_context():
    print("🔍 === VERIFICANDO CONFIGURAÇÕES NO BANCO ===")
    
    try:
        # Buscar configuração existente
        config = Configuracao.query.first()
        
        if config:
            print("✅ Configuração encontrada:")
            print(f"   🏛️  Nome Igreja: {config.nome_igreja}")
            print(f"   📍 Endereço: {config.endereco}")
            print(f"   🏙️  Cidade: {config.cidade}")
            print(f"   📄 CNPJ: {config.cnpj}")
            print(f"   📞 Telefone: {config.telefone}")
            print(f"   📧 Email: {config.email}")
            print(f"   👨‍💼 Dirigente: {config.dirigente}")
            print(f"   💰 Tesoureiro: {config.tesoureiro}")
        else:
            print("❌ Nenhuma configuração encontrada!")
            print("💡 Criando configuração padrão...")
            
            nova_config = Configuracao(
                nome_igreja="ORGANIZAÇÃO BATISTA PEDRA DE CRISTO",
                endereco="Rua das Flores, 123",
                cidade="Tietê",
                cnpj="12.345.678/0001-99",
                telefone="(15) 3285-1234",
                email="contato@obpctcp.org.br",
                dirigente="Pastor João Silva",
                tesoureiro="Maria Santos"
            )
            
            db.session.add(nova_config)
            db.session.commit()
            
            print("✅ Configuração padrão criada com sucesso!")
            
    except Exception as e:
        print(f"❌ Erro: {e}")
        
    print("\n🎯 === TESTE FINALIZADO ===")