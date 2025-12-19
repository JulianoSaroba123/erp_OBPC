"""
Script para testar PDF com configurações dinâmicas
"""
from app import create_app
from app.extensoes import db
from app.configuracoes.configuracoes_model import Configuracao
from app.secretaria.atas.atas_model import Ata
from datetime import datetime
from flask import render_template

app = create_app()

with app.app_context():
    print("🔍 === TESTANDO PDF COM CONFIGURAÇÕES DINÂMICAS ===")
    
    # Buscar configuração
    config_obj = Configuracao.query.first()
    print(f"✅ Configuração carregada: {config_obj.nome_igreja}")
    
    # Buscar uma ata
    ata = Ata.query.first()
    if ata:
        print(f"📄 Ata encontrada: {ata.titulo}")
        
        # Dados da igreja (usando nova lógica)
        if config_obj:
            config = {
                'nome_igreja': config_obj.nome_igreja,
                'endereco': config_obj.endereco if config_obj.endereco else 'Rua das Flores, 123',
                'cidade': f"{config_obj.cidade} - SP" if config_obj.cidade else 'Tietê - SP',
                'cnpj': config_obj.cnpj if config_obj.cnpj else '12.345.678/0001-99',
                'telefone': config_obj.telefone if config_obj.telefone else '(15) 3285-1234',
                'email': config_obj.email if config_obj.email else 'contato@obpctcp.org.br',
                'dirigente': config_obj.dirigente if config_obj.dirigente else 'Pastor João Silva',
                'tesoureiro': config_obj.tesoureiro if config_obj.tesoureiro else 'Maria Santos'
            }
        
        print("🏛️  Dados que serão usados no PDF:")
        print(f"   Nome Igreja: {config['nome_igreja']}")
        print(f"   Endereço: {config['endereco']}")
        print(f"   Cidade: {config['cidade']}")
        print(f"   CNPJ: {config['cnpj']}")
        print(f"   Dirigente: {config['dirigente']}")
        print(f"   Tesoureiro: {config['tesoureiro']}")
        
        # Testar renderização do template
        html_content = render_template('atas/pdf_ata.html',
                                     ata=ata,
                                     config=config,
                                     data_geracao=datetime.now().strftime('%d/%m/%Y às %H:%M'))
        
        print(f"\n📄 Template renderizado com {len(html_content)} caracteres")
        
        # Verificar se os dados da configuração estão no HTML
        if config_obj.nome_igreja in html_content:
            print("✅ Nome da igreja encontrado no PDF!")
        else:
            print("❌ Nome da igreja NÃO encontrado no PDF!")
            
        if config_obj.cnpj in html_content:
            print("✅ CNPJ encontrado no PDF!")
        else:
            print("❌ CNPJ NÃO encontrado no PDF!")
            
    else:
        print("❌ Nenhuma ata encontrada!")
        
    print("\n🎯 === TESTE FINALIZADO ===")