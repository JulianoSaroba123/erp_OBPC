#!/usr/bin/env python3
"""
Teste do PDF com melhorias de espaçamento
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from app.extensoes import db
from app.financeiro.financeiro_model import Lancamento
from app.utils.gerar_pdf_reportlab import RelatorioFinanceiro
from app.configuracoes.configuracoes_model import Configuracao
from datetime import datetime

def testar_pdf_melhorado():
    """Testa geração de PDF com espaçamento melhorado"""
    app = create_app()
    
    with app.app_context():
        print("📄 Testando PDF com melhorias de espaçamento...")
        
        # Buscar alguns lançamentos
        lancamentos = Lancamento.query.limit(10).all()
        print(f"✅ Encontrados {len(lancamentos)} lançamentos para teste")
        
        # Obter configuração
        config = Configuracao.obter_configuracao()
        
        # Criar relatório
        relatorio = RelatorioFinanceiro(config)
        
        try:
            # Gerar PDF de teste
            mes = datetime.now().month
            ano = datetime.now().year
            pdf_buffer = relatorio.gerar_relatorio_caixa(lancamentos, mes, ano, 0)
            
            # Salvar arquivo de teste
            nome_arquivo = f"teste_pdf_melhorado_{mes}_{ano}.pdf"
            with open(nome_arquivo, 'wb') as f:
                f.write(pdf_buffer.getvalue())
            
            print(f"✅ PDF de teste gerado: {nome_arquivo}")
            print("🔍 Verifique se:")
            print("   • As letras não estão mais encavaladas")
            print("   • Há espaçamento adequado entre as linhas")
            print("   • As tabelas ficaram mais legíveis")
            
        except Exception as e:
            print(f"❌ Erro ao gerar PDF: {e}")

if __name__ == "__main__":
    testar_pdf_melhorado()