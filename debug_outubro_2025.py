import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from app.models import Lancamento
from app.config import Config
from datetime import datetime

app = create_app(Config)

with app.app_context():
    # Verifica lançamentos de outubro 2025
    print("=== LANÇAMENTOS DE OUTUBRO 2025 ===")
    
    entradas = Lancamento.query.filter(
        Lancamento.tipo == 'Entrada',
        Lancamento.data >= datetime(2025, 10, 1),
        Lancamento.data < datetime(2025, 11, 1)
    ).all()
    
    if not entradas:
        print("Nenhum lançamento encontrado em outubro 2025")
        
        # Vamos criar alguns dados de exemplo para testar
        print("\n=== CRIANDO DADOS DE EXEMPLO ===")
        
        from app import db
        
        # Exemplo de oferta (deveria ir para ofertas alçadas)
        oferta = Lancamento(
            data=datetime(2025, 10, 15),
            categoria='OFERTA',
            valor=236.52,
            tipo='Entrada',
            conta='Caixa',
            origem_destino='Igreja Local',
            descricao='Oferta dominical'
        )
        db.session.add(oferta)
        
        # Exemplo de dízimo
        dizimo = Lancamento(
            data=datetime(2025, 10, 15),
            categoria='DÍZIMO',
            valor=500.00,
            tipo='Entrada',
            conta='Caixa',
            origem_destino='Membro',
            descricao='Dízimo mensal'
        )
        db.session.add(dizimo)
        
        # Exemplo de rendimento (deveria ir para outras ofertas)
        rendimento = Lancamento(
            data=datetime(2025, 10, 15),
            categoria='RENDIMENTOS',
            valor=10.00,
            tipo='Entrada',
            conta='Banco',
            origem_destino='Banco',
            descricao='Rendimento poupança'
        )
        db.session.add(rendimento)
        
        try:
            db.session.commit()
            print("Dados de exemplo criados com sucesso!")
            
            # Agora vamos verificar novamente
            entradas = Lancamento.query.filter(
                Lancamento.tipo == 'Entrada',
                Lancamento.data >= datetime(2025, 10, 1),
                Lancamento.data < datetime(2025, 11, 1)
            ).all()
            
        except Exception as e:
            print(f"Erro ao criar dados: {e}")
            db.session.rollback()
    
    print(f"\nTotal de entradas em outubro 2025: {len(entradas)}")
    
    for entrada in entradas:
        print(f"\nData: {entrada.data.strftime('%Y-%m-%d')}")
        print(f"Categoria: '{entrada.categoria}'")
        print(f"Valor: R$ {entrada.valor:.2f}")
        print(f"Tipo: {entrada.tipo}")
        print(f"Conta: {entrada.conta}")
        
        # Simular a classificação como no código
        categoria_lower = entrada.categoria.lower()
        
        if 'dízimo' in categoria_lower or 'dizimo' in categoria_lower:
            classificacao = "DÍZIMOS"
        elif 'oferta' in categoria_lower:
            classificacao = "OFERTAS ALÇADAS (regular)"
        else:
            classificacao = "OUTRAS OFERTAS (não é dízimo nem oferta)"
            
        print(f"SERIA CLASSIFICADO COMO: {classificacao}")
        print("-" * 50)