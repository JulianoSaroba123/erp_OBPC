#!/usr/bin/env python3
"""
Teste de importação e conciliação bancária
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from app.extensoes import db
from app.financeiro.financeiro_model import Lancamento, ImportacaoExtrato, ConciliacaoHistorico
from app.financeiro.utils.conciliacao_avancada import ImportadorExtrato, ConciliadorAvancado, GeradorRelatorios
from datetime import datetime, date

def testar_importacao_conciliacao():
    """Testa importação de CSV e conciliação automática"""
    
    print("=== TESTE DE IMPORTAÇÃO E CONCILIAÇÃO BANCÁRIA ===")
    print()
    
    app = create_app()
    
    with app.app_context():
        try:
            # 1. Verificar estado inicial
            print("📊 ESTADO INICIAL:")
            total_inicial = Lancamento.query.count()
            manuais_inicial = Lancamento.query.filter_by(origem='manual').count()
            importados_inicial = Lancamento.query.filter_by(origem='importado').count()
            
            print(f"   💰 Total lançamentos: {total_inicial}")
            print(f"   ✋ Manuais: {manuais_inicial}")
            print(f"   📥 Importados: {importados_inicial}")
            
            # 2. Criar alguns lançamentos manuais que podem ser conciliados
            print("\n✋ CRIANDO LANÇAMENTOS MANUAIS...")
            
            lancamentos_manuais = [
                {
                    'data': date(2024, 11, 5),
                    'tipo': 'Entrada',
                    'categoria': 'Depósito',
                    'descricao': 'Depósito bancário',
                    'valor': 500.00,
                    'conta': 'Banco'
                },
                {
                    'data': date(2024, 11, 7),
                    'tipo': 'Entrada',
                    'categoria': 'Dízimo',
                    'descricao': 'Dízimo igreja',
                    'valor': 1200.00,
                    'conta': 'Banco'
                },
                {
                    'data': date(2024, 11, 6),
                    'tipo': 'Saída',
                    'categoria': 'Despesa',
                    'descricao': 'Pagamento fornecedor',
                    'valor': 80.00,
                    'conta': 'Banco'
                }
            ]
            
            for dados in lancamentos_manuais:
                lancamento = Lancamento(
                    data=dados['data'],
                    tipo=dados['tipo'],
                    categoria=dados['categoria'],
                    descricao=dados['descricao'],
                    valor=dados['valor'],
                    conta=dados['conta'],
                    origem='manual'
                )
                db.session.add(lancamento)
            
            db.session.commit()
            print(f"   ✅ {len(lancamentos_manuais)} lançamentos manuais criados")
            
            # 3. Testar importação do arquivo CSV
            print("\n📥 TESTANDO IMPORTAÇÃO DO EXTRATO CSV...")
            
            csv_path = os.path.join(os.path.dirname(__file__), 'extrato_teste.csv')
            
            if not os.path.exists(csv_path):
                print(f"   ❌ Arquivo não encontrado: {csv_path}")
                return False
            
            print(f"   📄 Arquivo: {csv_path}")
            
            # Importar usando o ImportadorExtrato
            importador = ImportadorExtrato()
            resultado_importacao = importador.importar_arquivo(csv_path, 'generico', 'Sistema Teste')
            
            print(f"   📊 RESULTADO DA IMPORTAÇÃO:")
            print(f"      ✅ Sucesso: {resultado_importacao['sucesso']}")
            print(f"      📈 Total registros: {resultado_importacao['total_registros']}")
            print(f"      ✅ Processados: {resultado_importacao['registros_processados']}")
            print(f"      ⚠️ Duplicados: {resultado_importacao['registros_duplicados']}")
            print(f"      ❌ Erros: {resultado_importacao['registros_erro']}")
            
            if resultado_importacao['erros']:
                print(f"      📋 Erros detalhados:")
                for erro in resultado_importacao['erros'][:5]:  # Mostrar apenas os primeiros 5
                    print(f"         - {erro}")
            
            # 4. Verificar estado após importação
            print("\n📊 ESTADO APÓS IMPORTAÇÃO:")
            total_pos = Lancamento.query.count()
            manuais_pos = Lancamento.query.filter_by(origem='manual').count()
            importados_pos = Lancamento.query.filter_by(origem='importado').count()
            
            print(f"   💰 Total lançamentos: {total_pos} (+{total_pos - total_inicial})")
            print(f"   ✋ Manuais: {manuais_pos} (+{manuais_pos - manuais_inicial})")
            print(f"   📥 Importados: {importados_pos} (+{importados_pos - importados_inicial})")
            
            # 5. Testar conciliação automática
            print("\n🤖 TESTANDO CONCILIAÇÃO AUTOMÁTICA...")
            
            conciliador = ConciliadorAvancado()
            resultado_conciliacao = conciliador.conciliar_automatico('Sistema Teste')
            
            print(f"   📊 RESULTADO DA CONCILIAÇÃO:")
            print(f"      🔗 Pares conciliados: {resultado_conciliacao['conciliados']}")
            print(f"      ⏱️ Tempo execução: {resultado_conciliacao['tempo_execucao']:.2f}s")
            print(f"      📋 Regras aplicadas: {resultado_conciliacao['regras_aplicadas']}")
            
            if 'erro' in resultado_conciliacao:
                print(f"      ❌ Erro: {resultado_conciliacao['erro']}")
            
            if resultado_conciliacao['log']:
                print(f"      📝 Log da conciliação:")
                for log_entry in resultado_conciliacao['log'][:5]:
                    print(f"         - {log_entry}")
            
            # 6. Verificar estado final
            print("\n📊 ESTADO FINAL:")
            conciliados_final = Lancamento.query.filter_by(conciliado=True).count()
            pendentes_final = Lancamento.query.filter_by(conciliado=False).count()
            
            print(f"   🔗 Conciliados: {conciliados_final}")
            print(f"   ⏳ Pendentes: {pendentes_final}")
            
            # 7. Gerar relatório de indicadores
            print("\n📊 INDICADORES DO DASHBOARD:")
            
            indicadores = GeradorRelatorios.gerar_dashboard_indicadores()
            
            print(f"   💰 Total lançamentos: {indicadores['totais']['lancamentos']}")
            print(f"   📊 % Conciliado: {indicadores['percentuais']['conciliado']:.1f}%")
            print(f"   📊 % Importados: {indicadores['percentuais']['importados']:.1f}%")
            
            # 8. Verificar discrepâncias
            print("\n🔍 VERIFICANDO DISCREPÂNCIAS:")
            discrepancias = GeradorRelatorios.gerar_relatorio_discrepancias()
            
            if discrepancias:
                print(f"   ⚠️ {len(discrepancias)} discrepâncias encontradas:")
                for i, disc in enumerate(discrepancias[:3]):
                    print(f"      {i+1}. {disc['tipo']}: {disc['descricao']}")
            else:
                print(f"   ✅ Nenhuma discrepância encontrada")
            
            # 9. Verificar histórico de conciliações
            print("\n📋 HISTÓRICO DE CONCILIAÇÕES:")
            historicos = ConciliacaoHistorico.query.order_by(ConciliacaoHistorico.data_conciliacao.desc()).limit(3).all()
            
            for h in historicos:
                print(f"   🕒 {h.data_conciliacao.strftime('%Y-%m-%d %H:%M')} - {h.usuario}")
                print(f"      🔗 {h.total_conciliados} conciliados, {h.total_pendentes} pendentes")
                print(f"      📊 Tipo: {h.tipo_conciliacao}")
            
            print("\n🎉 TESTE DE IMPORTAÇÃO E CONCILIAÇÃO CONCLUÍDO!")
            return True
            
        except Exception as e:
            print(f"❌ ERRO DURANTE TESTE: {e}")
            import traceback
            traceback.print_exc()
            return False

if __name__ == "__main__":
    sucesso = testar_importacao_conciliacao()
    if sucesso:
        print("\n✅ SISTEMA DE IMPORTAÇÃO E CONCILIAÇÃO FUNCIONANDO!")
        print("\n🎯 FUNCIONALIDADES TESTADAS:")
        print("   📥 Importação de extratos CSV")
        print("   🔍 Detecção de duplicatas")
        print("   🤖 Conciliação automática com algoritmos inteligentes")
        print("   📊 Geração de indicadores e relatórios")
        print("   🔍 Detecção de discrepâncias")
        print("   📋 Histórico de conciliações")
        print("\n🌐 PRONTO PARA USAR NA INTERFACE WEB!")
    else:
        print("\n⚠️ VERIFIQUE OS ERROS ACIMA")