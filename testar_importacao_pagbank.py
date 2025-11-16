#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Script de teste para debug da importação PagBank
"""

import pandas as pd
import sys
import os

def testar_arquivo_pagbank():
    """Testa o arquivo do PagBank para ver as colunas"""
    
    # Caminho do arquivo (você pode mudar este caminho)
    arquivo_excel = r"f:\Ano 2025\Ano 2025\ERP_OBPC\extrato_pagbank_exemplo.csv"
    
    print("🔍 TESTE DE IMPORTAÇÃO PAGBANK")
    print("=" * 50)
    
    try:
        # Tentar ler como CSV primeiro
        print(f"📁 Arquivo: {arquivo_excel}")
        
        if not os.path.exists(arquivo_excel):
            print("❌ Arquivo não encontrado!")
            return
        
        # Ler o arquivo
        df = pd.read_csv(arquivo_excel)
        
        print(f"✅ Arquivo carregado com sucesso!")
        print(f"📊 Número de linhas: {len(df)}")
        print(f"📊 Número de colunas: {len(df.columns)}")
        
        print("\n🗂️ COLUNAS ENCONTRADAS:")
        for i, col in enumerate(df.columns):
            print(f"  {i+1}. '{col}' (tipo: {type(col).__name__})")
        
        print("\n📋 PRIMEIRAS 3 LINHAS:")
        print(df.head(3).to_string())
        
        print("\n🔍 TESTE DE DETECÇÃO DE COLUNAS:")
        
        # Simular a função encontrar_coluna
        def encontrar_coluna_teste(df, palavras_chave):
            print(f"  🔎 Procurando por: {palavras_chave}")
            
            # Primeiro: busca exata
            for col in df.columns:
                for palavra in palavras_chave:
                    if str(col).lower() == palavra.lower():
                        print(f"    ✅ ENCONTRADO (exato): '{col}' = '{palavra}'")
                        return col
            
            # Segundo: busca parcial
            for col in df.columns:
                col_lower = str(col).lower().replace(' ', '').replace('_', '')
                for palavra in palavras_chave:
                    palavra_clean = palavra.lower().replace(' ', '')
                    if palavra_clean in col_lower:
                        print(f"    ✅ ENCONTRADO (parcial): '{col}' contém '{palavra}'")
                        return col
            
            print(f"    ❌ NÃO ENCONTRADO")
            return None
        
        # Testar mapeamento PagBank
        data_cols = ['DATA', 'data', 'datatransacao', 'dataoperacao', 'date', 'created_at']
        desc_cols = ['DESCRICAO', 'descricao', 'descricaotransacao', 'historico', 'description', 'memo', 'reference']
        valor_cols = ['VALOR', 'valor', 'valortransacao', 'amount', 'montante', 'quantia', 'gross_amount']
        tipo_cols = ['TIPO', 'tipo', 'tipotransacao', 'credito', 'debito', 'natureza', 'transaction_type']
        
        col_data = encontrar_coluna_teste(df, data_cols)
        col_desc = encontrar_coluna_teste(df, desc_cols)
        col_valor = encontrar_coluna_teste(df, valor_cols)
        col_tipo = encontrar_coluna_teste(df, tipo_cols)
        
        print(f"\n📊 RESULTADO FINAL:")
        print(f"  📅 DATA: {col_data}")
        print(f"  📝 DESCRIÇÃO: {col_desc}")
        print(f"  💰 VALOR: {col_valor}")
        print(f"  🏷️ TIPO: {col_tipo}")
        
        if all([col_data, col_desc, col_valor]):
            print("\n✅ SUCESSO! Todas as colunas essenciais foram encontradas!")
            
            # Mostrar alguns dados processados
            print("\n📋 DADOS PROCESSADOS (3 primeiras linhas):")
            for i in range(min(3, len(df))):
                row = df.iloc[i]
                print(f"  Linha {i+1}:")
                print(f"    Data: {row[col_data]}")
                print(f"    Descrição: {row[col_desc]}")
                print(f"    Valor: {row[col_valor]}")
                if col_tipo:
                    print(f"    Tipo: {row[col_tipo]}")
                print()
        else:
            print("\n❌ ERRO! Nem todas as colunas essenciais foram encontradas!")
            
    except Exception as e:
        print(f"❌ ERRO ao processar arquivo: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    testar_arquivo_pagbank()