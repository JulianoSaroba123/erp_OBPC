#!/usr/bin/env python3
"""
Script para simular erro e testar a função de PDF de ofícios diretamente
Sistema OBPC
"""

import sys
import os
from datetime import datetime

# Adiciona o diretório raiz ao path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from app.secretaria.oficios.oficios_model import Oficio

def simular_geracao_pdf():
    """Simula a geração de PDF do ofício"""
    app = create_app()
    
    with app.app_context():
        try:
            print("🧪 === SIMULANDO GERAÇÃO DE PDF OFÍCIO ===")
            print()
            
            # Buscar um ofício
            oficio = Oficio.query.first()
            if not oficio:
                print("❌ Nenhum ofício encontrado!")
                return False
            
            print(f"📄 Ofício: {oficio.numero}")
            print(f"📝 Assunto: {oficio.assunto}")
            print(f"👤 Destinatário: {oficio.destinatario}")
            print()
            
            # Simular as configurações
            dados_igreja = {
                'nome': 'ORGANIZAÇÃO BATISTA PEDRA DE CRISTO',
                'endereco': 'Rua das Flores, 123 - Tietê - SP',
                'cnpj': '12.345.678/0001-99',
                'telefone': '(15) 3285-1234',
                'email': 'contato@obpctcp.org.br'
            }
            
            print("🏛️  Dados da igreja configurados")
            
            # Simular renderização do template
            from flask import render_template
            
            print("📋 Renderizando template...")
            html_content = render_template('oficios/pdf_oficio.html', 
                                         oficio=oficio,
                                         dados_igreja=dados_igreja,
                                         data_geracao=datetime.now().strftime('%d/%m/%Y'))
            
            print(f"   ✅ Template renderizado: {len(html_content)} caracteres")
            
            # Testar WeasyPrint
            print("🔄 Testando WeasyPrint...")
            import weasyprint
            
            pdf = weasyprint.HTML(string=html_content).write_pdf()
            print(f"   ✅ PDF gerado: {len(pdf)} bytes")
            
            # Testar salvamento
            print("💾 Testando salvamento...")
            nome_arquivo = f"teste_oficio_{oficio.numero}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
            caminho_arquivo = os.path.join('app', 'static', 'oficios', nome_arquivo)
            
            os.makedirs(os.path.dirname(caminho_arquivo), exist_ok=True)
            with open(caminho_arquivo, 'wb') as f:
                f.write(pdf)
            
            if os.path.exists(caminho_arquivo):
                tamanho = os.path.getsize(caminho_arquivo)
                print(f"   ✅ Arquivo salvo: {caminho_arquivo}")
                print(f"   📏 Tamanho: {tamanho} bytes")
                
                # Remove arquivo de teste
                os.remove(caminho_arquivo)
                print("   🗑️  Arquivo de teste removido")
            
            print()
            print("🎉 SIMULAÇÃO CONCLUÍDA COM SUCESSO!")
            print("   A função de geração de PDF deveria estar funcionando.")
            print("   O problema pode ser:")
            print("   1. Autenticação/Login requerido")
            print("   2. Erro no template específico")
            print("   3. Configuração do blueprint/rota")
            
            return True
            
        except Exception as e:
            print(f"❌ ERRO durante simulação: {str(e)}")
            import traceback
            traceback.print_exc()
            return False

if __name__ == "__main__":
    sucesso = simular_geracao_pdf()
    if sucesso:
        print("\n✨ Simulação bem-sucedida!")
    else:
        print("\n❌ Simulação falhou!")
        sys.exit(1)