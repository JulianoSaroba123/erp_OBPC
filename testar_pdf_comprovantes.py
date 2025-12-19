#!/usr/bin/env python3
"""
Script para testar funcionalidade de comprovantes no PDF de caixa
"""

import sys
import os
from datetime import datetime, timedelta

# Adicionar o diretório raiz ao Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from run import app
from app import db
from app.financeiro.financeiro_model import Lancamento

def testar_pdf_comprovantes():
    """Testa a geração de PDF com comprovantes"""
    
    with app.app_context():
        print("=== TESTANDO PDF DE CAIXA COM COMPROVANTES ===")
        print()
        
        # Verificar se existem lançamentos com comprovantes
        lancamentos_com_comprovante = Lancamento.query.filter(
            Lancamento.comprovante.isnot(None)
        ).all()
        
        print(f"✅ Lançamentos com comprovante encontrados: {len(lancamentos_com_comprovante)}")
        
        if lancamentos_com_comprovante:
            for lancamento in lancamentos_com_comprovante[:3]:  # Mostrar apenas os 3 primeiros
                print(f"   📎 ID {lancamento.id}: {lancamento.descricao} - {lancamento.comprovante}")
        
        # Verificar se existem lançamentos do mês atual
        mes_atual = datetime.now().month
        ano_atual = datetime.now().year
        
        lancamentos_mes = Lancamento.query.filter(
            db.extract('month', Lancamento.data) == mes_atual,
            db.extract('year', Lancamento.data) == ano_atual
        ).all()
        
        print(f"✅ Lançamentos do mês {mes_atual:02d}/{ano_atual}: {len(lancamentos_mes)}")
        
        # Contar quantos têm comprovante
        com_comprovante = sum(1 for l in lancamentos_mes if l.comprovante)
        sem_comprovante = len(lancamentos_mes) - com_comprovante
        
        print(f"   📎 Com comprovante: {com_comprovante}")
        print(f"   📋 Sem comprovante: {sem_comprovante}")
        print()
        
        # Testar a geração do PDF (simulação)
        print("🔄 TESTANDO GERAÇÃO DE PDF...")
        
        try:
            from app.utils.gerar_pdf_reportlab import RelatorioFinanceiro
            from app.configuracoes.configuracoes_model import Configuracao
            
            # Obter configurações
            config = Configuracao.obter_configuracao()
            
            # Criar instância do relatório
            relatorio = RelatorioFinanceiro(config)
            
            # Testar método _gerar_info_comprovante
            print("🔍 Testando método _gerar_info_comprovante:")
            
            for lancamento in lancamentos_mes[:5]:  # Testar com 5 lançamentos
                info_comprovante = relatorio._gerar_info_comprovante(lancamento)
                comprovante_str = str(info_comprovante)
                
                if lancamento.comprovante:
                    print(f"   ✅ ID {lancamento.id}: {comprovante_str[:50]}...")
                else:
                    print(f"   ➖ ID {lancamento.id}: {comprovante_str}")
            
            print()
            print("✅ TESTE DE COMPROVANTES NO PDF CONCLUÍDO!")
            print()
            print("🎯 COMO TESTAR NO NAVEGADOR:")
            print(f"   1. Acesse: http://127.0.0.1:5000/financeiro/relatorio-caixa?mes={mes_atual}&ano={ano_atual}")
            print("   2. Clique em 'PDF' para gerar o relatório")
            print("   3. Verifique se a coluna 'Comprovante' aparece")
            print("   4. Clique nos links dos comprovantes para abrir os arquivos")
            print()
            
        except Exception as e:
            print(f"❌ Erro ao testar PDF: {str(e)}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    testar_pdf_comprovantes()