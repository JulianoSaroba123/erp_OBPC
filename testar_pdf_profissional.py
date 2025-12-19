#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Script para testar o novo sistema de PDF profissional
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from app.financeiro.financeiro_model import Lancamento
from app.utils.gerar_pdf_reportlab import RelatorioFinanceiro
from datetime import datetime

def main():
    """Função principal para testar PDF"""
    app = create_app()
    
    with app.app_context():
        try:
            # Buscar lançamentos para teste
            lancamentos = Lancamento.query.limit(10).all()
            print(f"✅ Encontrados {len(lancamentos)} lançamentos para teste")
            
            if lancamentos:
                # Testar novo sistema de PDF
                print("🔄 Gerando relatório profissional...")
                relatorio = RelatorioFinanceiro()
                pdf_buffer = relatorio.gerar_relatorio_caixa(lancamentos, 1, 2025, 1500.0)
                
                # Salvar arquivo de teste
                nome_arquivo = f'teste_relatorio_completo_{datetime.now().strftime("%H%M%S")}.pdf'
                with open(nome_arquivo, 'wb') as f:
                    f.write(pdf_buffer.read())
                
                print(f"✅ PDF profissional gerado com sucesso!")
                print(f"📄 Arquivo salvo como: {nome_arquivo}")
                print(f"📂 Localização: {os.path.abspath(nome_arquivo)}")
                
                # Testar relatório da sede também
                print("\n🔄 Gerando relatório da sede...")
                pdf_buffer_sede = relatorio.gerar_relatorio_sede(lancamentos, 1, 2025, 1500.0)
                
                nome_arquivo_sede = f'teste_relatorio_sede_{datetime.now().strftime("%H%M%S")}.pdf'
                with open(nome_arquivo_sede, 'wb') as f:
                    f.write(pdf_buffer_sede.read())
                
                print(f"✅ Relatório da sede gerado com sucesso!")
                print(f"📄 Arquivo salvo como: {nome_arquivo_sede}")
                
            else:
                print("ℹ️ Nenhum lançamento encontrado para teste")
                
        except Exception as e:
            print(f"❌ Erro durante o teste: {str(e)}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    main()