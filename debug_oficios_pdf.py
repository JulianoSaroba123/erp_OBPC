#!/usr/bin/env python3
"""
Debug específico para função de PDF dos ofícios
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from app.extensoes import db
from app.secretaria.oficios.oficios_model import Oficio

def debug_pdf_oficios():
    """Debug da função de PDF dos ofícios"""
    print("🔍 DEBUG: PDF dos Ofícios")
    print("=" * 40)
    
    app = create_app()
    
    with app.app_context():
        try:
            # 1. Verificar se o ofício existe
            print("1. Verificando ofício ID 1...")
            oficio = Oficio.query.get(1)
            
            if oficio:
                print(f"✅ Ofício encontrado: {oficio.numero}")
                print(f"   Destinatário: {oficio.destinatario}")
                print(f"   Assunto: {oficio.assunto}")
                print(f"   Status: {oficio.status}")
            else:
                print("❌ Ofício ID 1 não encontrado")
                return False
            
            # 2. Verificar configurações
            print("\n2. Verificando configurações...")
            try:
                from app.configuracoes.configuracoes_model import Configuracao
                config_obj = Configuracao.query.first()
                if config_obj:
                    print("✅ Configurações encontradas")
                    print(f"   Nome Igreja: {config_obj.nome_igreja}")
                else:
                    print("⚠️ Nenhuma configuração encontrada (usará fallback)")
            except Exception as e:
                print(f"❌ Erro ao carregar configurações: {e}")
            
            # 3. Testar função ReportLab diretamente
            print("\n3. Testando função ReportLab...")
            try:
                from app.secretaria.oficios.oficios_routes import gerar_pdf_oficio_reportlab
                
                # Dados de teste
                dados_igreja = {
                    'nome': 'ORGANIZAÇÃO BATISTA PEDRA DE CRISTO',
                    'endereco': 'Rua das Flores, 123 - Tietê - SP',
                    'cnpj': '12.345.678/0001-99',
                    'telefone': '(15) 3285-1234',
                    'email': 'contato@obpctcp.org.br',
                    'dirigente': 'Pastor João Silva',
                    'tesoureiro': 'Maria Santos'
                }
                
                print("   Chamando função...")
                response = gerar_pdf_oficio_reportlab(oficio, dados_igreja)
                
                if response:
                    print("✅ Função executada com sucesso!")
                    print(f"   Content-Type: {response.headers.get('Content-Type', 'N/A')}")
                    return True
                else:
                    print("❌ Função retornou None")
                    return False
                    
            except Exception as e:
                print(f"❌ Erro na função ReportLab: {e}")
                import traceback
                traceback.print_exc()
                return False
            
        except Exception as e:
            print(f"❌ Erro geral: {e}")
            import traceback
            traceback.print_exc()
            return False

if __name__ == "__main__":
    sucesso = debug_pdf_oficios()
    
    print("\n" + "=" * 40)
    if sucesso:
        print("🎉 DEBUG CONCLUÍDO - Função OK!")
    else:
        print("❌ PROBLEMAS DETECTADOS NA FUNÇÃO")
    print("=" * 40)