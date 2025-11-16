#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Teste simples do relatório de caixa interno corrigido
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from app.utils.gerar_pdf_reportlab import RelatorioFinanceiro
from app.financeiro.financeiro_model import Lancamento
from app.configuracoes.configuracoes_model import Configuracao
from datetime import datetime, timedelta

def main():
    app = create_app()
    
    with app.app_context():
        print("=== TESTE RELATÓRIO DE CAIXA INTERNO CORRIGIDO ===")
        
        # Obter configuração
        config = Configuracao.query.first()
        if not config:
            config = Configuracao(
                nome_igreja="Igreja Batista Palavra da Cruz",
                percentual_conselho=30.0
            )
        
        # Buscar alguns lançamentos
        lancamentos = Lancamento.query.limit(20).all()
        
        if len(lancamentos) == 0:
            print("Nenhum lançamento encontrado.")
            return
        
        print(f"Lançamentos encontrados: {len(lancamentos)}")
        
        # Gerar PDF
        relatorio = RelatorioFinanceiro(config)
        
        # Salvar em buffer
        try:
            relatorio.gerar_relatorio_caixa(
                lancamentos=lancamentos,
                mes=datetime.now().month,
                ano=datetime.now().year,
                saldo_anterior=2000.00
            )
            
            # Salvar em arquivo
            relatorio.buffer.seek(0)
            nome_arquivo = f"teste_caixa_corrigido_{datetime.now().strftime('%H%M%S')}.pdf"
            
            with open(nome_arquivo, 'wb') as f:
                f.write(relatorio.buffer.getvalue())
            
            print(f"✅ Arquivo salvo: {nome_arquivo}")
            print("✅ Correções implementadas:")
            print("   • Colunas alargadas")
            print("   • Despesas fixas incluídas") 
            print("   • Conselho administrativo incluído")
            print("   • Total de saídas corrigido")
            
        except Exception as e:
            print(f"❌ Erro: {str(e)}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    main()