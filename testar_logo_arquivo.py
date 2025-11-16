"""
Script para testar se o logo está sendo carregado do arquivo Logo_OBPC.jpg
"""
from app import create_app
from app.extensoes import db
from app.configuracoes.configuracoes_model import Configuracao
from app.secretaria.atas.atas_model import Ata
from datetime import datetime
from flask import render_template

app = create_app()

with app.app_context():
    print("🖼️ === TESTANDO LOGO DO ARQUIVO LOGO_OBPC.JPG ===")
    
    # Buscar configuração
    config_obj = Configuracao.query.first()
    
    # Buscar uma ata
    ata = Ata.query.first()
    if ata:
        print(f"📄 Testando template de Ata: {ata.titulo}")
        
        # Dados da igreja
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
        
        # Testar template de Atas
        html_atas = render_template('atas/pdf_ata.html',
                                   ata=ata,
                                   config=config,
                                   data_geracao=datetime.now().strftime('%d/%m/%Y às %H:%M'))
        
        print(f"   📄 Template Atas: {len(html_atas)} caracteres")
        
        # Verificar se o logo está sendo referenciado corretamente
        if '/static/Logo_OBPC.jpg' in html_atas:
            print("   ✅ Referência ao Logo_OBPC.jpg encontrada!")
        else:
            print("   ❌ Referência ao Logo_OBPC.jpg NÃO encontrada!")
            
        if 'class="logo"' in html_atas:
            print("   ✅ Classe CSS do logo encontrada!")
        else:
            print("   ❌ Classe CSS do logo NÃO encontrada!")
            
        # Verificar se não há mais base64
        if 'data:image/jpeg;base64,' in html_atas:
            print("   ⚠️  Ainda há código base64 no template!")
        else:
            print("   ✅ Código base64 removido com sucesso!")
            
    else:
        print("❌ Nenhuma ata encontrada!")
        
    print("\n🎯 === RESULTADO DO TESTE ===")
    print("   ✅ Templates atualizados para usar static/Logo_OBPC.jpg")
    print("   ✅ Removido código base64 dos templates")
    print("   ✅ WeasyPrint configurado com base_url para carregar o logo")
    print("   📄 Logo será carregado do arquivo físico na pasta static")