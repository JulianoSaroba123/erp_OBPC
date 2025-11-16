"""
Script para criar dados de exemplo para ensinar conciliação
"""
from app import create_app
from app.extensoes import db
from app.financeiro.financeiro_model import Lancamento
from datetime import datetime, date
import random

app = create_app()

with app.app_context():
    print("=== Criando dados de exemplo para conciliação ===\n")
    
    # Limpar dados de teste anteriores
    Lancamento.query.filter(Lancamento.descricao.like('EXEMPLO%')).delete()
    db.session.commit()
    
    # 1. CENÁRIO SIMPLES - Correspondência exata
    print("1️⃣ CENÁRIO: Correspondência Exata")
    print("   Situação: Mesmo valor, mesma data, descrições similares")
    
    # Lançamento manual
    manual1 = Lancamento(
        descricao="EXEMPLO Dízimo - João Silva",
        valor=250.00,
        data=date(2024, 11, 1),
        tipo="Entrada",  # Entrada
        categoria="Dízimos",
        banco_origem="manual",
        observacoes="Dízimo recebido em dinheiro"
    )
    
    # Lançamento do extrato bancário (importado)
    import1 = Lancamento(
        descricao="EXEMPLO PIX João Silva - dizimo",
        valor=250.00,
        data=date(2024, 11, 1),
        tipo="Entrada",
        categoria="Transferências",
        banco_origem="banco_brasil",
        observacoes="PIX recebido"
    )
    
    db.session.add_all([manual1, import1])
    print(f"   ✓ Manual: {manual1.descricao} - R$ {manual1.valor}")
    print(f"   ✓ Extrato: {import1.descricao} - R$ {import1.valor}")
    
    # 2. CENÁRIO MÉDIO - Valores próximos
    print("\n2️⃣ CENÁRIO: Valores Próximos (com taxa)")
    print("   Situação: Valor manual maior que o bancário (descontada taxa)")
    
    manual2 = Lancamento(
        descricao="EXEMPLO Oferta Domingo - Maria Santos",
        valor=100.00,
        data=date(2024, 11, 2),
        tipo="Entrada",
        categoria="Ofertas",
        banco_origem="manual"
    )
    
    import2 = Lancamento(
        descricao="EXEMPLO TED Maria Santos oferta",
        valor=98.50,  # Valor menor (taxa bancária)
        data=date(2024, 11, 2),
        tipo="Entrada",
        categoria="Transferências",
        banco_origem="itau"
    )
    
    db.session.add_all([manual2, import2])
    print(f"   ✓ Manual: {manual2.descricao} - R$ {manual2.valor}")
    print(f"   ✓ Extrato: {import2.descricao} - R$ {import2.valor} (taxa descontada)")
    
    # 3. CENÁRIO DIFÍCIL - Datas diferentes
    print("\n3️⃣ CENÁRIO: Datas Diferentes")
    print("   Situação: Lançamento feito em uma data, compensado em outra")
    
    manual3 = Lancamento(
        descricao="EXEMPLO Contribuição especial - Pedro Costa",
        valor=500.00,
        data=date(2024, 10, 30),  # Data do compromisso
        tipo="Entrada",
        categoria="Contribuições",
        banco_origem="manual"
    )
    
    import3 = Lancamento(
        descricao="EXEMPLO DEPOSITO PEDRO COSTA",
        valor=500.00,
        data=date(2024, 11, 3),  # Data da compensação
        tipo="Entrada",
        categoria="Depósitos",
        banco_origem="santander"
    )
    
    db.session.add_all([manual3, import3])
    print(f"   ✓ Manual: {manual3.descricao} - R$ {manual3.valor} (30/10)")
    print(f"   ✓ Extrato: {import3.descricao} - R$ {import3.valor} (03/11)")
    
    # 4. CENÁRIO GASTOS - Correspondência de débitos
    print("\n4️⃣ CENÁRIO: Gastos/Débitos")
    print("   Situação: Pagamentos que devem ser conciliados")
    
    manual4 = Lancamento(
        descricao="EXEMPLO Pagamento energia elétrica",
        valor=180.50,  # Valor positivo (será saída pelo tipo)
        data=date(2024, 11, 1),
        tipo="Saída",
        categoria="Energia",
        banco_origem="manual"
    )
    
    import4 = Lancamento(
        descricao="EXEMPLO CEMIG ENERGIA ELETRICA",
        valor=180.50,
        data=date(2024, 11, 1),
        tipo="Saída",
        categoria="Débitos",
        banco_origem="banco_brasil"
    )
    
    db.session.add_all([manual4, import4])
    print(f"   ✓ Manual: {manual4.descricao} - R$ {manual4.valor}")
    print(f"   ✓ Extrato: {import4.descricao} - R$ {import4.valor}")
    
    # 5. CENÁRIO SEM CORRESPONDÊNCIA
    print("\n5️⃣ CENÁRIO: Sem Correspondência")
    print("   Situação: Lançamentos que não têm par (precisam investigação)")
    
    manual5 = Lancamento(
        descricao="EXEMPLO Doação anônima",
        valor=75.00,
        data=date(2024, 11, 4),
        tipo="Entrada",
        categoria="Doações",
        banco_origem="manual"
    )
    
    import5 = Lancamento(
        descricao="EXEMPLO TARIFA BANCARIA",
        valor=12.90,
        data=date(2024, 11, 4),
        tipo="Saída",
        categoria="Tarifas",
        banco_origem="itau"
    )
    
    db.session.add_all([manual5, import5])
    print(f"   ✓ Manual órfão: {manual5.descricao} - R$ {manual5.valor}")
    print(f"   ✓ Extrato órfão: {import5.descricao} - R$ {import5.valor}")
    
    # Salvar tudo
    db.session.commit()
    
    print(f"\n✅ Criados 10 lançamentos de exemplo para conciliação!")
    print("\n" + "="*60)
    print("🎯 PRÓXIMOS PASSOS:")
    print("1. Acesse: http://127.0.0.1:5000/financeiro/conciliacao")
    print("2. Clique em 'Gerar Sugestões'")
    print("3. Analise os pares sugeridos")
    print("4. Aceite os corretos e investigue os órfãos")
    print("="*60)