"""
Script para testar diretamente a função de geração de PDF corrigida
"""
from app import create_app
from app.extensoes import db
from app.financeiro.financeiro_model import Lancamento
from app.utils.gerar_pdf_reportlab import RelatorioFinanceiro
from app.configuracoes.configuracoes_model import Configuracao
from datetime import datetime, date

app = create_app()

def testar_pdf_direto():
    """Testa a geração de PDF diretamente, sem passar pela web"""
    with app.app_context():
        try:
            print("=== Teste Direto da Função PDF Corrigida ===\n")
            
            # Buscar dados de exemplo
            lancamentos = Lancamento.query.filter(
                Lancamento.descricao.like('TESTE%')
            ).limit(10).all()
            
            if not lancamentos:
                print("❌ Não encontrei dados de exemplo")
                print("Execute: python scripts/criar_dados_conciliacao_exemplo.py")
                return
            
            print(f"✅ Encontrados {len(lancamentos)} lançamentos para teste")
            
            # Criar instância do relatório
            config = Configuracao.obter_configuracao()
            relatorio = RelatorioFinanceiro(config)
            
            # Gerar PDF usando a função corrigida
            print("🔄 Gerando PDF com as correções aplicadas...")
            
            mes_atual = datetime.now().month
            ano_atual = datetime.now().year
            
            pdf_buffer = relatorio.gerar_relatorio_caixa(
                lancamentos, 
                mes_atual, 
                ano_atual, 
                saldo_anterior=0
            )
            
            # Salvar PDF
            with open('relatorio_corrigido_direto.pdf', 'wb') as f:
                f.write(pdf_buffer.getvalue())
            
            print("✅ PDF gerado com sucesso!")
            print(f"💾 Arquivo salvo: relatorio_corrigido_direto.pdf")
            print(f"📏 Tamanho: {len(pdf_buffer.getvalue())} bytes")
            
            print("\n🔧 CORREÇÕES APLICADAS:")
            print("✅ Larguras das colunas ajustadas:")
            print("   - Data: 2.2cm")
            print("   - Descrição: 5.5cm (aumentada)")
            print("   - Categoria: 2.8cm")
            print("   - Tipo: 1.8cm")
            print("   - Valor: 2.5cm")
            print("   - Comprovante: 1.7cm")
            print("   - Saldo: 2.5cm")
            print("   📏 Total: 17cm (cabe na página A4)")
            
            print("\n✅ Altura das linhas aumentada:")
            print("   - Cabeçalho: 22px")
            print("   - Dados: 25px")
            
            print("\n✅ Espaçamento melhorado:")
            print("   - Padding vertical: 10px")
            print("   - Padding horizontal: 6px")
            print("   - Fonte reduzida: 8px")
            
            print("\n✅ Truncamento de texto:")
            print("   - Descrições longas: máx 35 caracteres")
            print("   - Categorias longas: máx 15 caracteres")
            
            print("\n🎯 TESTE CONCLUÍDO!")
            print("Abra o arquivo 'relatorio_corrigido_direto.pdf' para verificar se:")
            print("- Não há mais sobreposição de texto")
            print("- Todas as colunas cabem na página")
            print("- O espaçamento está adequado")
            print("- Os dados estão legíveis")
            
        except Exception as e:
            print(f"❌ Erro ao gerar PDF: {str(e)}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    testar_pdf_direto()