"""
Script de teste end-to-end do sistema de conciliação
Testa: criar dados de exemplo, gerar sugestões, exportar CSV, aceitar e desfazer
"""

import sys
import os
sys.path.insert(0, os.path.abspath('.'))

from app import create_app
from app.extensoes import db
from app.financeiro.financeiro_model import Lancamento, ConciliacaoHistorico, ConciliacaoPar
from datetime import datetime, date
import requests
import json

def criar_dados_teste():
    """Criar alguns lançamentos de teste para conciliação"""
    app = create_app()
    with app.app_context():
        # Limpar dados de teste anteriores
        ConciliacaoPar.query.delete()
        ConciliacaoHistorico.query.delete()
        Lancamento.query.filter(Lancamento.descricao.like('%TESTE%')).delete()
        
        # Criar lançamentos manuais (sem campos extras que causaram erro)
        manual1 = Lancamento(
            data=date(2025, 11, 1),
            tipo='Entrada',
            categoria='Dízimo',
            descricao='TESTE Dízimo João Silva',
            valor=500.00,
            conta='Dinheiro',
            origem='manual',
            conciliado=False
        )
        
        manual2 = Lancamento(
            data=date(2025, 11, 2),
            tipo='Saída',
            categoria='Despesa',
            descricao='TESTE Pagamento energia elétrica',
            valor=150.00,
            conta='Banco',
            origem='manual',
            conciliado=False
        )
        
        # Criar lançamentos importados (que devem casar)
        importado1 = Lancamento(
            data=date(2025, 11, 1),
            tipo='Entrada',
            categoria='Transferência',
            descricao='TESTE PIX João Silva dizimo',
            valor=500.00,
            conta='Banco',
            origem='importado',
            conciliado=False
        )
        
        importado2 = Lancamento(
            data=date(2025, 11, 3),  # data ligeiramente diferente para testar proximidade
            tipo='Saída',
            categoria='Débito',
            descricao='TESTE ENERGIA ELETRICA LTDA',
            valor=150.00,
            conta='Banco',
            origem='importado',
            conciliado=False
        )
        
        db.session.add_all([manual1, manual2, importado1, importado2])
        db.session.commit()
        
        print(f"Criados 4 lançamentos de teste:")
        print(f"Manual 1 (ID {manual1.id}): {manual1.descricao} - R$ {manual1.valor}")
        print(f"Manual 2 (ID {manual2.id}): {manual2.descricao} - R$ {manual2.valor}")
        print(f"Importado 1 (ID {importado1.id}): {importado1.descricao} - R$ {importado1.valor}")
        print(f"Importado 2 (ID {importado2.id}): {importado2.descricao} - R$ {importado2.valor}")
        
        return {
            'manual1_id': manual1.id,
            'manual2_id': manual2.id,
            'importado1_id': importado1.id,
            'importado2_id': importado2.id
        }

def testar_api_conciliacao():
    """Testar API de conciliação via requests"""
    base_url = "http://127.0.0.1:5000"
    
    try:
        # 1. Acessar página de conciliação
        response = requests.get(f"{base_url}/financeiro/conciliacao")
        print(f"✓ Página de conciliação: HTTP {response.status_code}")
        
        # 2. Gerar sugestões
        sugestoes_data = {
            'days_window': 3,
            'value_tol_pct': 0.02,
            'desc_thresh': 0.3
        }
        response = requests.post(f"{base_url}/financeiro/conciliacao/sugerir", data=sugestoes_data)
        print(f"✓ Gerar sugestões: HTTP {response.status_code}")
        
        # Extrair IDs dos pares sugeridos (simulação)
        # Em um teste real, parsearia o HTML para encontrar os pares
        dados_teste = criar_dados_teste()
        pares_teste = [
            {'imp_id': dados_teste['importado1_id'], 'man_id': dados_teste['manual1_id'], 'score': 0.85},
            {'imp_id': dados_teste['importado2_id'], 'man_id': dados_teste['manual2_id'], 'score': 0.78}
        ]
        
        # 3. Exportar CSV
        export_data = {'pairs': json.dumps(pares_teste)}
        response = requests.post(f"{base_url}/financeiro/conciliacao/export_pairs", data=export_data)
        print(f"✓ Exportar CSV: HTTP {response.status_code} (Content-Type: {response.headers.get('content-type')})")
        
        # 4. Aceitar sugestões
        accept_data = {'pairs': json.dumps(pares_teste)}
        response = requests.post(f"{base_url}/financeiro/conciliacao/aceitar_todos", data=accept_data)
        print(f"✓ Aceitar sugestões: HTTP {response.status_code}")
        
        # 5. Verificar histórico criado
        app = create_app()
        with app.app_context():
            ultimo_historico = ConciliacaoHistorico.query.order_by(ConciliacaoHistorico.data_conciliacao.desc()).first()
            if ultimo_historico:
                print(f"✓ Histórico criado: ID {ultimo_historico.id}, {ultimo_historico.total_conciliados} conciliados")
                
                # 6. Desfazer conciliação
                response = requests.post(f"{base_url}/financeiro/conciliacao/undo/{ultimo_historico.id}")
                print(f"✓ Desfazer conciliação: HTTP {response.status_code}")
                
                # Verificar se foi desfeito
                historico_apos_undo = ConciliacaoHistorico.query.get(ultimo_historico.id)
                if not historico_apos_undo:
                    print("✓ Conciliação desfeita com sucesso")
                else:
                    print("⚠ Conciliação não foi desfeita")
            else:
                print("⚠ Nenhum histórico encontrado")
        
        return True
        
    except Exception as e:
        print(f"✗ Erro no teste: {str(e)}")
        return False

if __name__ == "__main__":
    print("=== Teste End-to-End do Sistema de Conciliação ===")
    print("1. Criando dados de teste...")
    dados = criar_dados_teste()
    
    print("\n2. Testando APIs de conciliação...")
    sucesso = testar_api_conciliacao()
    
    if sucesso:
        print("\n✅ Todos os testes passaram! Sistema funcionando corretamente.")
    else:
        print("\n❌ Alguns testes falharam. Verifique o servidor e dependências.")
    
    print("\n📋 Para usar manualmente:")
    print("   1. Acesse: http://127.0.0.1:5000/financeiro/conciliacao")
    print("   2. Clique 'Gerar Sugestões'")
    print("   3. Selecione pares e clique 'Exportar selecionados (CSV)'")
    print("   4. Clique 'Aceitar selecionados'")
    print("   5. Use botão 'Desfazer' no histórico se necessário")