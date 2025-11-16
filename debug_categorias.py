"""
Script para debugar categorias de lançamentos financeiros
"""

import sys
import os

# Adicionar o diretório do projeto ao path
sys.path.insert(0, os.path.abspath('.'))

from app import create_app
from app.financeiro.financeiro_model import Lancamento
from sqlalchemy import extract

app = create_app()

with app.app_context():
    # Buscar todos os lançamentos de entrada de 2025
    ano = 2025
    
    print(f"=== TODOS OS LANÇAMENTOS DE ENTRADA DE {ano} ===")
    
    # Buscar todos os meses com dados
    for mes in range(1, 13):
        lancamentos = Lancamento.query.filter(
            extract('month', Lancamento.data) == mes,
            extract('year', Lancamento.data) == ano,
            Lancamento.tipo == 'Entrada'
        ).all()
        
        if lancamentos:
            print(f"\n--- MÊS {mes}/{ano} ---")
            print(f"Total de entradas encontradas: {len(lancamentos)}")
            
            for lancamento in lancamentos:
                categoria = lancamento.categoria.lower() if lancamento.categoria else ''
                valor = lancamento.valor or 0
                
                print(f"Data: {lancamento.data}")
                print(f"Categoria original: '{lancamento.categoria}'")
                print(f"Categoria lowercase: '{categoria}'")
                print(f"Valor: R$ {valor:.2f}")
                print(f"Tipo: {lancamento.tipo}")
                print(f"Conta: {lancamento.conta}")
                
                # Verificar em qual categoria seria classificada
                if 'dízimo' in categoria or 'dizimo' in categoria:
                    classificacao = "DÍZIMOS"
                elif 'oferta' in categoria:
                    if 'omn' in categoria or 'especial' in categoria:
                        classificacao = "OUTRAS OFERTAS (especial)"
                    else:
                        classificacao = "OFERTAS ALÇADAS (regular)"
                else:
                    classificacao = "OUTRAS OFERTAS (não é dízimo nem oferta)"
                
                print(f"SERIA CLASSIFICADO COMO: {classificacao}")
                print("-" * 50)
    
    # Se não encontrar dados em 2025, buscar em anos anteriores
    for ano_anterior in [2024, 2023]:
        print(f"\n=== VERIFICANDO {ano_anterior} ===")
        total_ano = Lancamento.query.filter(
            extract('year', Lancamento.data) == ano_anterior,
            Lancamento.tipo == 'Entrada'
        ).count()
        print(f"Total de entradas em {ano_anterior}: {total_ano}")
        
        if total_ano > 0:
            print(f"Mostrando primeiros 5 registros de {ano_anterior}:")
            primeiros = Lancamento.query.filter(
                extract('year', Lancamento.data) == ano_anterior,
                Lancamento.tipo == 'Entrada'
            ).limit(5).all()
            
            for lancamento in primeiros:
                categoria = lancamento.categoria.lower() if lancamento.categoria else ''
                valor = lancamento.valor or 0
                print(f"Data: {lancamento.data}, Categoria: '{lancamento.categoria}', Valor: R$ {valor:.2f}")
            break