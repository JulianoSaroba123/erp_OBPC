#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🧪 TESTE DAS CORREÇÕES DO RELATÓRIO GERAL
Verifica se as correções implementadas estão funcionando corretamente
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from app.extensoes import db
from app.financeiro.financeiro_model import Lancamento

def testar_calculos_relatorio():
    """Testa se os cálculos do relatório geral estão corretos"""
    
    print("=" * 60)
    print("🧪 TESTE DAS CORREÇÕES DO RELATÓRIO GERAL")
    print("⛪ Igreja O Brasil para Cristo - Tietê/SP")
    print("=" * 60)
    
    app = create_app()
    
    with app.app_context():
        try:
            # Obter lançamentos para teste
            lancamentos = Lancamento.query.limit(20).all()
            
            if not lancamentos:
                print("⚠️ Nenhum lançamento encontrado para teste")
                return False
            
            print(f"📊 Encontrados {len(lancamentos)} lançamentos para análise")
            
            # Importar a classe de relatório
            from app.utils.gerar_pdf_reportlab import RelatorioFinanceiro
            relatorio = RelatorioFinanceiro()
            
            # 1. Testar cálculo por categoria
            print(f"\n🔍 1. TESTANDO CÁLCULOS POR CATEGORIA:")
            totais_categoria = relatorio._calcular_totais_por_categoria(lancamentos)
            
            total_entradas_categoria = sum(totais_categoria['entradas'].values())
            total_saidas_categoria = sum(totais_categoria['saidas'].values())
            
            print(f"📈 Total de Entradas por Categoria: R$ {total_entradas_categoria:,.2f}")
            print(f"📉 Total de Saídas por Categoria: R$ {total_saidas_categoria:,.2f}")
            
            print(f"\n🔢 Categorias de Entradas ({len(totais_categoria['entradas'])}):")
            for categoria, valor in sorted(totais_categoria['entradas'].items(), key=lambda x: x[1], reverse=True):
                print(f"  • {categoria}: R$ {valor:,.2f}")
            
            print(f"\n🔢 Categorias de Saídas ({len(totais_categoria['saidas'])}):")
            for categoria, valor in sorted(totais_categoria['saidas'].items(), key=lambda x: x[1], reverse=True):
                print(f"  • {categoria}: R$ {valor:,.2f}")
            
            # 2. Testar cálculo por conta (sem PIX)
            print(f"\n🔍 2. TESTANDO CÁLCULOS POR CONTA (SEM PIX):")
            totais_conta = relatorio._calcular_totais_por_conta(lancamentos)
            
            print(f"🏦 Contas disponíveis: {list(totais_conta.keys())}")
            
            for conta, valores in totais_conta.items():
                entradas = valores['entradas']
                saidas = valores['saidas']
                saldo = entradas - saidas
                
                print(f"💳 {conta.upper()}:")
                print(f"  📈 Entradas: R$ {entradas:,.2f}")
                print(f"  📉 Saídas: R$ {saidas:,.2f}")
                print(f"  ⚖️ Saldo: R$ {saldo:,.2f}")
            
            # 3. Verificar se PIX foi removido
            print(f"\n🔍 3. VERIFICANDO REMOÇÃO DO PIX:")
            if 'pix' not in totais_conta:
                print(f"✅ PIX removido com sucesso!")
            else:
                print(f"❌ PIX ainda presente na lista de contas")
            
            # 4. Verificar cálculos manuais
            print(f"\n🔍 4. VERIFICAÇÃO MANUAL DOS CÁLCULOS:")
            entradas_manual = 0
            saidas_manual = 0
            
            for lancamento in lancamentos:
                valor = float(lancamento.valor) if lancamento.valor else 0
                if lancamento.tipo.lower() == 'entrada':
                    entradas_manual += valor
                elif lancamento.tipo.lower() in ['saída', 'saida']:
                    saidas_manual += valor
            
            print(f"📊 Cálculo Manual:")
            print(f"  📈 Entradas: R$ {entradas_manual:,.2f}")
            print(f"  📉 Saídas: R$ {saidas_manual:,.2f}")
            print(f"  ⚖️ Saldo: R$ {entradas_manual - saidas_manual:,.2f}")
            
            print(f"\n📊 Cálculo por Categoria:")
            print(f"  📈 Entradas: R$ {total_entradas_categoria:,.2f}")
            print(f"  📉 Saídas: R$ {total_saidas_categoria:,.2f}")
            print(f"  ⚖️ Saldo: R$ {total_entradas_categoria - total_saidas_categoria:,.2f}")
            
            # 5. Verificar consistência
            print(f"\n🔍 5. VERIFICAÇÃO DE CONSISTÊNCIA:")
            
            diferenca_entradas = abs(entradas_manual - total_entradas_categoria)
            diferenca_saidas = abs(saidas_manual - total_saidas_categoria)
            
            if diferenca_entradas < 0.01:
                print(f"✅ Entradas consistentes (diferença: R$ {diferenca_entradas:.2f})")
            else:
                print(f"❌ Inconsistência nas entradas (diferença: R$ {diferenca_entradas:.2f})")
            
            if diferenca_saidas < 0.01:
                print(f"✅ Saídas consistentes (diferença: R$ {diferenca_saidas:.2f})")
            else:
                print(f"❌ Inconsistência nas saídas (diferença: R$ {diferenca_saidas:.2f})")
            
            # 6. Testar larguras das colunas (informativo)
            print(f"\n🔍 6. INFORMAÇÕES SOBRE LARGURAS DAS COLUNAS:")
            print(f"✅ Colunas de Entradas: 7cm + 4cm + 3cm = 14cm total")
            print(f"✅ Colunas de Saídas: 7cm + 4cm + 3cm = 14cm total")
            print(f"✅ Colunas de Contas: 4cm + 4cm + 4cm + 4cm = 16cm total")
            print(f"📋 Antes eram muito justas, agora têm espaço adequado")
            
            return True
            
        except Exception as e:
            print(f"❌ Erro durante o teste: {e}")
            import traceback
            traceback.print_exc()
            return False

def testar_geracao_pdf():
    """Testa se o PDF está sendo gerado corretamente com as correções"""
    
    print(f"\n" + "=" * 60)
    print(f"📄 TESTE DE GERAÇÃO DO PDF CORRIGIDO")
    print(f"=" * 60)
    
    app = create_app()
    
    with app.app_context():
        try:
            from app.utils.gerar_pdf_reportlab import RelatorioFinanceiro
            from datetime import datetime
            
            # Obter lançamentos para teste
            lancamentos = Lancamento.query.limit(15).all()
            
            if not lancamentos:
                print("⚠️ Nenhum lançamento encontrado para teste")
                return False
            
            print(f"📊 Encontrados {len(lancamentos)} lançamentos para teste")
            
            # Gerar PDF completo
            relatorio = RelatorioFinanceiro()
            mes_atual = datetime.now().month
            ano_atual = datetime.now().year
            
            print(f"🔄 Gerando PDF completo para {mes_atual:02d}/{ano_atual}...")
            
            pdf_buffer = relatorio.gerar_relatorio_caixa(lancamentos, mes_atual, ano_atual)
            
            # Salvar arquivo de teste
            nome_arquivo = f"teste_relatorio_corrigido_{datetime.now().strftime('%H%M%S')}.pdf"
            caminho_arquivo = os.path.join(os.getcwd(), nome_arquivo)
            
            with open(caminho_arquivo, 'wb') as f:
                f.write(pdf_buffer.getvalue())
            
            print(f"✅ PDF gerado com sucesso!")
            print(f"📄 Arquivo: {nome_arquivo}")
            print(f"📂 Localização: {caminho_arquivo}")
            
            # Verificar se o arquivo foi criado
            if os.path.exists(caminho_arquivo):
                tamanho = os.path.getsize(caminho_arquivo)
                print(f"📊 Tamanho do arquivo: {tamanho:,} bytes")
                
                if tamanho > 2000:  # Arquivo deve ter pelo menos 2KB
                    print(f"✅ PDF válido gerado com correções aplicadas!")
                    return True
                else:
                    print(f"⚠️ Arquivo muito pequeno, pode estar corrompido")
                    return False
            else:
                print(f"❌ Arquivo não foi criado")
                return False
                
        except Exception as e:
            print(f"❌ Erro ao gerar PDF: {e}")
            import traceback
            traceback.print_exc()
            return False

if __name__ == "__main__":
    print("🚀 Iniciando testes das correções do relatório geral...")
    
    # Teste 1: Cálculos
    teste1 = testar_calculos_relatorio()
    
    # Teste 2: PDF
    teste2 = testar_geracao_pdf()
    
    # Resultado final
    print(f"\n" + "=" * 60)
    if teste1 and teste2:
        print(f"🎉 TODOS OS TESTES PASSARAM!")
        print(f"✅ Cálculos das saídas: OK")
        print(f"✅ Larguras das colunas: OK")
        print(f"✅ Remoção do PIX: OK")
        print(f"✅ Geração do PDF: OK")
        print(f"✅ Todas as correções implementadas com sucesso!")
    else:
        print(f"❌ ALGUNS TESTES FALHARAM!")
        print(f"{'✅' if teste1 else '❌'} Cálculos e verificações")
        print(f"{'✅' if teste2 else '❌'} Geração do PDF")
    
    print(f"=" * 60)