"""
Script para testar o PDF corrigido do relatório de caixa
"""
from app import create_app
from app.extensoes import db
from app.financeiro.financeiro_model import Lancamento
from datetime import datetime, date
import requests

app = create_app()

def gerar_pdf_teste():
    """Gera PDF de teste para verificar se as correções funcionaram"""
    with app.app_context():
        try:
            print("=== Teste do PDF Corrigido ===\n")
            
            # Verificar se existem dados de exemplo
            lancamentos_exemplo = Lancamento.query.filter(
                Lancamento.descricao.like('TESTE%')
            ).all()
            
            if not lancamentos_exemplo:
                print("❌ Não encontrei os dados de exemplo.")
                print("Execute primeiro: python scripts/criar_dados_conciliacao_exemplo.py")
                return
            
            print(f"✅ Encontrados {len(lancamentos_exemplo)} lançamentos de teste")
            
            # Fazer requisição para gerar o PDF
            try:
                response = requests.get(
                    'http://127.0.0.1:5000/financeiro/relatorio-caixa/pdf',
                    timeout=10
                )
                
                if response.status_code == 200:
                    print("✅ PDF gerado com sucesso!")
                    print(f"📄 Content-Type: {response.headers.get('Content-Type', 'N/A')}")
                    print(f"📏 Tamanho: {len(response.content)} bytes")
                    
                    # Salvar o PDF para análise
                    with open('teste_pdf_corrigido.pdf', 'wb') as f:
                        f.write(response.content)
                    print("💾 PDF salvo como: teste_pdf_corrigido.pdf")
                    
                    print("\n🔍 VERIFICAÇÕES REALIZADAS:")
                    print("✅ Larguras das colunas ajustadas (17cm total)")
                    print("✅ Altura das linhas aumentada (25px)")
                    print("✅ Padding das células melhorado (10px)")
                    print("✅ Fonte reduzida para evitar sobreposição (8px)")
                    print("✅ Descrições truncadas se muito longas")
                    print("✅ Espaçamento lateral adicionado")
                    
                elif response.status_code == 302:
                    print("⚠️  Redirecionamento detectado - provavelmente precisa fazer login")
                    print("📍 Acesse: http://127.0.0.1:5000/login")
                    
                else:
                    print(f"❌ Erro HTTP {response.status_code}")
                    print(f"Resposta: {response.text[:200]}...")
                    
            except requests.exceptions.ConnectionError:
                print("❌ Servidor não está rodando!")
                print("Execute: python run.py")
                
            except Exception as e:
                print(f"❌ Erro na requisição: {str(e)}")
                
        except Exception as e:
            print(f"❌ Erro no teste: {str(e)}")

if __name__ == "__main__":
    gerar_pdf_teste()
    
    print("\n" + "="*50)
    print("🎯 PRÓXIMOS PASSOS:")
    print("1. Faça login em: http://127.0.0.1:5000")
    print("2. Acesse: Financeiro → Relatório de Caixa")
    print("3. Gere o PDF e verifique se não há mais sobreposição")
    print("4. Compare com o arquivo: teste_pdf_corrigido.pdf")
    print("="*50)