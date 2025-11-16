import sys
import os
sys.path.append(os.path.abspath('.'))

from app import create_app, db
from app.models import Lancamento
from app.config import Config
from datetime import datetime

app = create_app(Config)

with app.app_context():
    # Pegar dados de outubro 2025
    print("=== DEBUG RELATÓRIO OUTUBRO 2025 ===")
    
    ano = 2025
    mes = 10
    
    # Dados de entrada exatamente como no código do relatório
    entradas = db.session.query(Lancamento).filter(
        Lancamento.tipo == 'Entrada',
        Lancamento.data >= datetime(ano, mes, 1),
        Lancamento.data < datetime(ano, mes+1, 1) if mes < 12 else datetime(ano+1, 1, 1)
    ).all()
    
    print(f"Total de entradas encontradas: {len(entradas)}")
    
    # Simulando exatamente o código do relatório
    total_dizimos = 0
    total_ofertas_alcadas = 0
    total_outras_ofertas = 0
    
    print("\n=== PROCESSANDO CADA ENTRADA ===")
    
    for entrada in entradas:
        categoria_lower = entrada.categoria.lower() if entrada.categoria else ''
        valor = float(entrada.valor or 0)
        
        print(f"\nProcessando: {entrada.data.strftime('%Y-%m-%d')}")
        print(f"Categoria original: '{entrada.categoria}'")
        print(f"Categoria lowercase: '{categoria_lower}'")
        print(f"Valor: R$ {valor:.2f}")
        
        # Lógica exata do código
        if 'dízimo' in categoria_lower or 'dizimo' in categoria_lower:
            total_dizimos += valor
            print(f"→ Adicionado aos DÍZIMOS: R$ {valor:.2f}")
        elif 'oferta' in categoria_lower:
            total_ofertas_alcadas += valor
            print(f"→ Adicionado às OFERTAS ALÇADAS: R$ {valor:.2f}")
        else:
            total_outras_ofertas += valor
            print(f"→ Adicionado às OUTRAS OFERTAS: R$ {valor:.2f}")
    
    print(f"\n=== TOTAIS FINAIS ===")
    print(f"Dízimos: R$ {total_dizimos:.2f}")
    print(f"Ofertas Alçadas: R$ {total_ofertas_alcadas:.2f}")
    print(f"Outras Ofertas: R$ {total_outras_ofertas:.2f}")
    
    print(f"\n=== VERIFICAÇÃO: onde está o valor R$ 236,52? ===")
    # Procurar especificamente por valores próximos a 236.52
    for entrada in entradas:
        if abs(float(entrada.valor or 0) - 236.52) < 0.01:
            print(f"ENCONTRADO! Data: {entrada.data}, Categoria: '{entrada.categoria}', Valor: R$ {entrada.valor}")