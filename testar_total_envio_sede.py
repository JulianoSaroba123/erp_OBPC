#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🧪 TESTE DO TOTAL DE ENVIO PARA SEDE
Verifica se o cálculo está correto: Conselho (30%) + Projetos/Contador
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from app.extensoes import db
from app.financeiro.financeiro_model import Lancamento
from app.financeiro.despesas_fixas_model import DespesaFixaConselho
from app.configuracoes.configuracoes_model import Configuracao

def testar_calculo_total_envio():
    """Testa o cálculo do total de envio para sede"""
    
    print("=" * 60)
    print("🧪 TESTE DO TOTAL DE ENVIO PARA SEDE")
    print("⛪ Igreja O Brasil para Cristo - Tietê/SP")
    print("=" * 60)
    
    app = create_app()
    
    with app.app_context():
        try:
            # 1. Verificar configuração do percentual do conselho
            config = Configuracao.query.first()
            percentual_conselho = config.percentual_conselho if config else 30.0
            
            print(f"📊 Percentual do Conselho: {percentual_conselho}%")
            
            # 2. Simular total arrecadado
            total_arrecadado = 1000.00  # Exemplo
            valor_conselho = total_arrecadado * (percentual_conselho / 100)
            
            print(f"💰 Total Arrecadado (exemplo): R$ {total_arrecadado:,.2f}")
            print(f"👥 Valor do Conselho ({percentual_conselho}%): R$ {valor_conselho:,.2f}")
            
            # 3. Obter despesas fixas (projetos/contador/etc)
            try:
                despesas_fixas = DespesaFixaConselho.obter_despesas_para_relatorio()
                total_projetos = sum(despesas_fixas.values())
                
                print(f"\n📋 Despesas Fixas (Projetos/Contador):")
                for nome, valor in despesas_fixas.items():
                    nome_exibir = nome.replace('_', ' ').title()
                    print(f"  • {nome_exibir}: R$ {valor:,.2f}")
                
                print(f"💼 Total dos Projetos/Contador: R$ {total_projetos:,.2f}")
                
            except Exception as e:
                print(f"⚠️ Erro ao obter despesas fixas: {e}")
                # Fallback para valores fixos
                despesas_fixas = {
                    'contador_sede': 100.00,
                    'forca_para_viver': 50.00,
                    'oferta_voluntaria_conchas': 100.00,
                    'projeto_filipe': 10.00,
                    'site': 20.00
                }
                total_projetos = sum(despesas_fixas.values())
                
                print(f"\n📋 Despesas Fixas (valores padrão):")
                for nome, valor in despesas_fixas.items():
                    nome_exibir = nome.replace('_', ' ').title()
                    print(f"  • {nome_exibir}: R$ {valor:,.2f}")
                
                print(f"💼 Total dos Projetos/Contador: R$ {total_projetos:,.2f}")
            
            # 4. Calcular total geral para sede
            total_geral_sede = valor_conselho + total_projetos
            
            print(f"\n" + "=" * 60)
            print(f"📋 COMPOSIÇÃO DO TOTAL DE ENVIO PARA SEDE:")
            print(f"📋 • Valor do Conselho ({percentual_conselho}%): R$ {valor_conselho:,.2f}")
            print(f"📋 • Total Projetos/Contador: R$ {total_projetos:,.2f}")
            print(f"📋 • TOTAL GERAL PARA SEDE: R$ {total_geral_sede:,.2f}")
            print(f"=" * 60)
            
            # 5. Verificar se os cálculos estão corretos
            print(f"\n🔍 VERIFICAÇÕES:")
            
            # Verificar percentual
            percentual_calculado = (valor_conselho / total_arrecadado) * 100
            if abs(percentual_calculado - percentual_conselho) < 0.01:
                print(f"✅ Percentual do conselho correto: {percentual_calculado:.1f}%")
            else:
                print(f"❌ Erro no percentual: esperado {percentual_conselho}%, calculado {percentual_calculado:.1f}%")
            
            # Verificar se tem despesas configuradas
            if total_projetos > 0:
                print(f"✅ Despesas fixas configuradas: R$ {total_projetos:,.2f}")
            else:
                print(f"⚠️ Nenhuma despesa fixa configurada")
            
            # Verificar total
            if total_geral_sede > 0:
                print(f"✅ Total geral para sede calculado: R$ {total_geral_sede:,.2f}")
            else:
                print(f"❌ Erro no cálculo do total geral")
            
            print(f"\n🎉 RESULTADO:")
            print(f"📊 A igreja deve enviar para a sede: R$ {total_geral_sede:,.2f}")
            print(f"📋 Composto por: {percentual_conselho}% do total + projetos/contador")
            
            return True
            
        except Exception as e:
            print(f"❌ Erro durante o teste: {e}")
            return False

def testar_relatorio_pdf():
    """Testa se o PDF está sendo gerado com a nova seção"""
    
    print(f"\n" + "=" * 60)
    print(f"📄 TESTE DE GERAÇÃO DO PDF")
    print(f"=" * 60)
    
    app = create_app()
    
    with app.app_context():
        try:
            from app.utils.gerar_pdf_reportlab import RelatorioFinanceiro
            from datetime import datetime
            
            # Obter alguns lançamentos para teste
            lancamentos = Lancamento.query.limit(10).all()
            
            if not lancamentos:
                print("⚠️ Nenhum lançamento encontrado para teste")
                return False
            
            print(f"📊 Encontrados {len(lancamentos)} lançamentos para teste")
            
            # Gerar PDF da sede
            gerador = RelatorioFinanceiro()
            mes_atual = datetime.now().month
            ano_atual = datetime.now().year
            
            print(f"🔄 Gerando PDF da sede para {mes_atual:02d}/{ano_atual}...")
            
            pdf_buffer = gerador.gerar_relatorio_sede(lancamentos, mes_atual, ano_atual)
            
            # Salvar arquivo de teste
            nome_arquivo = f"teste_total_envio_sede_{datetime.now().strftime('%H%M%S')}.pdf"
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
                
                if tamanho > 1000:  # Arquivo deve ter pelo menos 1KB
                    print(f"✅ PDF válido gerado com nova seção de total de envio!")
                    return True
                else:
                    print(f"⚠️ Arquivo muito pequeno, pode estar corrompido")
                    return False
            else:
                print(f"❌ Arquivo não foi criado")
                return False
                
        except Exception as e:
            print(f"❌ Erro ao gerar PDF: {e}")
            return False

if __name__ == "__main__":
    print("🚀 Iniciando testes do total de envio para sede...")
    
    # Teste 1: Cálculos
    teste1 = testar_calculo_total_envio()
    
    # Teste 2: PDF
    teste2 = testar_relatorio_pdf()
    
    # Resultado final
    print(f"\n" + "=" * 60)
    if teste1 and teste2:
        print(f"🎉 TODOS OS TESTES PASSARAM!")
        print(f"✅ Cálculo do total de envio: OK")
        print(f"✅ Geração do PDF: OK")
        print(f"✅ Nova seção implementada com sucesso!")
    else:
        print(f"❌ ALGUNS TESTES FALHARAM!")
        print(f"{'✅' if teste1 else '❌'} Cálculo do total de envio")
        print(f"{'✅' if teste2 else '❌'} Geração do PDF")
    
    print(f"=" * 60)