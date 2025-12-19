#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import pandas as pd
import os

def analisar_pagseguro():
    """Analisa especificamente o arquivo do PagSeguro"""
    
    arquivo = "Extrato da Conta - PagSeguro.csv"
    
    print(f"🔍 ANÁLISE: {arquivo}")
    print("=" * 60)
    
    # 1. Verificar se arquivo existe
    if not os.path.exists(arquivo):
        print("❌ ERRO: Arquivo não encontrado!")
        return
    
    print(f"✅ Arquivo encontrado: {os.path.getsize(arquivo)} bytes")
    
    # 2. Tentar ler arquivo
    try:
        print("\n📖 Tentando ler CSV...")
        
        # Testar diferentes encodings e separadores
        encodings = ['utf-8', 'latin-1', 'iso-8859-1', 'cp1252']
        separadores = [';', ',', '\t']
        
        df = None
        encoding_usado = None
        separador_usado = None
        
        for encoding in encodings:
            for sep in separadores:
                try:
                    df_test = pd.read_csv(arquivo, encoding=encoding, sep=sep)
                    if len(df_test.columns) > 1 and len(df_test) > 0:
                        df = df_test
                        encoding_usado = encoding
                        separador_usado = sep
                        break
                except:
                    continue
            if df is not None:
                break
                
        if df is None:
            print("❌ ERRO: Não foi possível ler o arquivo CSV!")
            return
            
        print(f"✅ CSV lido com sucesso!")
        print(f"   Encoding: {encoding_usado}")
        print(f"   Separador: '{separador_usado}'")
        
        # 3. Analisar estrutura
        print(f"\n📊 ESTRUTURA DO ARQUIVO:")
        print(f"   Linhas: {len(df)}")
        print(f"   Colunas: {len(df.columns)}")
        print(f"   Colunas: {list(df.columns)}")
        
        # 4. Mostrar primeiras linhas
        print(f"\n📝 PRIMEIRAS 5 TRANSAÇÕES:")
        for i in range(min(5, len(df))):
            linha = df.iloc[i]
            print(f"   {i+1}. {linha.iloc[1]} | {linha.iloc[2]} | {linha.iloc[3]} | R$ {linha.iloc[4]}")
        
        # 5. Analisar tipos de transação
        print(f"\n💰 TIPOS DE TRANSAÇÃO:")
        if len(df.columns) >= 3:
            tipos = df.iloc[:, 2].value_counts()  # Coluna TIPO
            for tipo, qtd in tipos.items():
                print(f"   {tipo}: {qtd} transações")
        
        # 6. Verificar valores
        print(f"\n💵 ANÁLISE DE VALORES:")
        if len(df.columns) >= 5:
            valores_col = df.iloc[:, 4]  # Coluna VALOR
            
            # Converter vírgulas para pontos
            valores_str = valores_col.astype(str).str.replace(',', '.')
            valores_num = pd.to_numeric(valores_str, errors='coerce')
            
            entradas = valores_num[valores_num > 0].sum()
            saidas = abs(valores_num[valores_num < 0].sum())
            saldo = entradas - saidas
            
            print(f"   💚 Entradas: R$ {entradas:,.2f}")
            print(f"   🔴 Saídas: R$ {saidas:,.2f}")
            print(f"   💙 Saldo: R$ {saldo:,.2f}")
        
        # 7. Verificar compatibilidade com mapeamento
        print(f"\n🏦 COMPATIBILIDADE COM SISTEMA:")
        
        colunas_esperadas = {
            'CODIGO DA TRANSACAO': 'documento/id',
            'DATA': 'data',
            'TIPO': 'tipo',
            'DESCRICAO': 'descricao', 
            'VALOR': 'valor'
        }
        
        compativel = True
        for col_esperada, funcao in colunas_esperadas.items():
            if col_esperada in df.columns:
                print(f"   ✅ {funcao}: {col_esperada}")
            else:
                print(f"   ❌ {funcao}: não encontrado")
                compativel = False
        
        print(f"\n🎯 RESULTADO FINAL:")
        if compativel:
            print("   ✅ ARQUIVO TOTALMENTE COMPATÍVEL!")
            print("   ✅ Pode ser importado diretamente")
            print("   ✅ Todas as colunas mapeadas corretamente")
        else:
            print("   ⚠️  Arquivo precisa de ajustes no mapeamento")
        
        # 8. Recomendações
        print(f"\n💡 RECOMENDAÇÕES:")
        print("   1. Use o banco 'PagBank' na importação")
        print("   2. O sistema detectará automaticamente o separador ';'")
        print(f"   3. {len(df)} transações serão processadas")
        
        if 'Pix recebido' in df.iloc[:, 2].values:
            print("   4. ✅ Contém receitas (Pix recebido)")
        if any('enviado' in str(val).lower() for val in df.iloc[:, 2].values):
            print("   5. ✅ Contém despesas (Pix enviado)")
        
    except Exception as e:
        print(f"❌ ERRO ao analisar arquivo: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    analisar_pagseguro()