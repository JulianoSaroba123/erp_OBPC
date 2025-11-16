"""
Script para testar o PDF com login automático
"""
from app import create_app
from app.extensoes import db
from app.financeiro.financeiro_model import Lancamento
from datetime import datetime, date
import requests

app = create_app()

def testar_pdf_com_login():
    """Testa o PDF fazendo login primeiro"""
    with app.app_context():
        try:
            print("=== Teste do PDF com Login Automático ===\n")
            
            # Criar sessão de requisições
            session = requests.Session()
            base_url = 'http://127.0.0.1:5000'
            
            # 1. Acessar página de login para obter CSRF token
            print("1. Acessando página de login...")
            login_page = session.get(f'{base_url}/login')
            if login_page.status_code != 200:
                print("❌ Erro ao acessar página de login")
                return
            
            # 2. Fazer login (assumindo que existe usuário admin)
            print("2. Fazendo login...")
            login_data = {
                'username': 'admin',
                'password': 'admin123'
            }
            
            login_response = session.post(f'{base_url}/login', data=login_data)
            
            # 3. Verificar se login foi bem-sucedido
            if 'login' not in login_response.url:
                print("✅ Login realizado com sucesso")
                
                # 4. Tentar gerar o PDF
                print("3. Gerando PDF do relatório...")
                pdf_response = session.get(f'{base_url}/financeiro/relatorio-caixa/pdf')
                
                if pdf_response.status_code == 200:
                    content_type = pdf_response.headers.get('Content-Type', '')
                    
                    if 'application/pdf' in content_type:
                        print("✅ PDF gerado com sucesso!")
                        print(f"📄 Content-Type: {content_type}")
                        print(f"📏 Tamanho: {len(pdf_response.content)} bytes")
                        
                        # Salvar o PDF
                        with open('relatorio_caixa_corrigido.pdf', 'wb') as f:
                            f.write(pdf_response.content)
                        print("💾 PDF salvo como: relatorio_caixa_corrigido.pdf")
                        
                        print("\n🔍 CORREÇÕES APLICADAS:")
                        print("✅ Larguras das colunas otimizadas")
                        print("✅ Altura das linhas aumentada") 
                        print("✅ Padding melhorado")
                        print("✅ Fonte ajustada")
                        print("✅ Texto truncado quando necessário")
                        print("\n🎯 Verifique o arquivo PDF para confirmar que não há mais sobreposição!")
                        
                    else:
                        print(f"⚠️  Resposta não é PDF: {content_type}")
                        print("Primeiros 200 caracteres da resposta:")
                        print(pdf_response.text[:200])
                        
                else:
                    print(f"❌ Erro ao gerar PDF: HTTP {pdf_response.status_code}")
                    
            else:
                print("❌ Falha no login - verificar credenciais")
                print("Tente criar um usuário admin primeiro ou usar outras credenciais")
                
        except requests.exceptions.ConnectionError:
            print("❌ Servidor não está rodando!")
            print("Execute: python run.py")
            
        except Exception as e:
            print(f"❌ Erro: {str(e)}")

if __name__ == "__main__":
    testar_pdf_com_login()
    
    print("\n" + "="*50)
    print("💡 COMO TESTAR MANUALMENTE:")
    print("1. Acesse: http://127.0.0.1:5000")
    print("2. Faça login no sistema")
    print("3. Vá para: Financeiro → Relatório de Caixa")
    print("4. Clique no botão de gerar PDF")
    print("5. Verifique se não há mais sobreposição de texto")
    print("="*50)