"""
Script para diagnosticar problema na importação de lançamentos financeiros
"""
from app import create_app, db
from app.financeiro.financeiro_model import Lancamento

app = create_app()

with app.app_context():
    print("=" * 70)
    print("DIAGNÓSTICO: IMPORTAÇÃO DE LANÇAMENTOS")
    print("=" * 70)
    
    # Contar todos os lançamentos
    total_lancamentos = Lancamento.query.count()
    print(f"\n📊 Total de lançamentos no banco: {total_lancamentos}")
    
    # Lançamentos por origem
    manuais = Lancamento.query.filter_by(origem='manual').count()
    importados = Lancamento.query.filter_by(origem='importado').count()
    
    print(f"\n📝 Lançamentos por origem:")
    print(f"   - Manuais: {manuais}")
    print(f"   - Importados: {importados}")
    
    # Últimos 10 lançamentos
    print(f"\n📋 Últimos 10 lançamentos:")
    ultimos = Lancamento.query.order_by(Lancamento.criado_em.desc()).limit(10).all()
    
    for lanc in ultimos:
        print(f"\n   ID: {lanc.id}")
        print(f"   Data: {lanc.data}")
        print(f"   Tipo: {lanc.tipo}")
        print(f"   Descrição: {lanc.descricao}")
        print(f"   Valor: R$ {lanc.valor:.2f}")
        print(f"   Origem: {lanc.origem}")
        print(f"   Banco Origem: {lanc.banco_origem}")
        print(f"   Criado em: {lanc.criado_em}")
        print(f"   Categoria: {lanc.categoria}")
        print(f"   Observações: {lanc.observacoes}")
        print("   " + "-" * 60)
    
    # Verificar se há lançamentos sem data
    sem_data = Lancamento.query.filter(Lancamento.data == None).count()
    print(f"\n⚠️  Lançamentos sem data: {sem_data}")
    
    # Verificar se há lançamentos sem categoria
    sem_categoria = Lancamento.query.filter(
        (Lancamento.categoria == None) | (Lancamento.categoria == '')
    ).count()
    print(f"⚠️  Lançamentos sem categoria: {sem_categoria}")
    
    print("\n" + "=" * 70)
    print("DIAGNÓSTICO CONCLUÍDO")
    print("=" * 70)
