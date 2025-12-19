#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import pandas as pd
import os

def diagnosticar_arquivo(arquivo_path):
    """Diagnóstica problemas no arquivo de importação"""
    
    print(f"🔍 DIAGNÓSTICO: {arquivo_path}")
    print("=" * 50)
    
    # 1. Verificar se arquivo existe
    if not os.path.exists(arquivo_path):
        print("❌ ERRO: Arquivo não encontrado!")
        return
    
    print(f"✅ Arquivo encontrado: {os.path.getsize(arquivo_path)} bytes")
    
    # 2. Verificar extensão
    extensao = arquivo_path.split('.')[-1].lower()
    formatos_suportados = ['csv', 'xlsx', 'xls']
    
    if extensao not in formatos_suportados:
        print(f"❌ ERRO: Formato {extensao} não suportado!")
        print(f"   Formatos aceitos: {formatos_suportados}")
        return
    
    print(f"✅ Formato suportado: {extensao}")
    
    # 3. Tentar ler arquivo
    try:
        if extensao == 'csv':
            print("\n📖 Tentando ler CSV...")
            
            # Testar diferentes encodings e separadores
            encodings = ['utf-8', 'latin-1', 'iso-8859-1', 'cp1252']
            separadores = [',', ';', '\t']
            
            df = None
            encoding_usado = None
            separador_usado = None
            
            for encoding in encodings:
                for sep in separadores:
                    try:
                        df_test = pd.read_csv(arquivo_path, encoding=encoding, sep=sep)
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
            
        else:  # Excel
            print("\n📖 Tentando ler Excel...")
            df = pd.read_excel(arquivo_path)
            print(f"✅ Excel lido com sucesso!")
        
        # 4. Analisar estrutura
        print(f"\n📊 ESTRUTURA DO ARQUIVO:")
        print(f"   Linhas: {len(df)}")
        print(f"   Colunas: {len(df.columns)}")
        print(f"   Colunas: {list(df.columns)}")
        
        if len(df) == 0:
            print("❌ ERRO: Arquivo vazio!")
            return
        
        # 5. Verificar mapeamento PagBank
        print(f"\n🏦 VERIFICAÇÃO MAPEAMENTO PAGBANK:")
        
        colunas_df = df.columns.str.lower()
        mapeamento_encontrado = {}
        
        # Verificar mapeamentos possíveis
        mapeamentos = {
            'data': ['data', 'dt_transacao', 'data_transacao', 'date'],
            'descricao': ['descrição', 'descricao', 'histórico', 'historico', 'description'],
            'valor': ['valor', 'vlr_transacao', 'valor_transacao', 'amount'],
            'tipo': ['tipo', 'type', 'debito', 'credito']
        }
        
        for campo, opcoes in mapeamentos.items():
            encontrado = False
            for opcao in opcoes:
                for col_df in df.columns:
                    if opcao in col_df.lower():
                        mapeamento_encontrado[campo] = col_df
                        print(f"   ✅ {campo}: {col_df}")
                        encontrado = True
                        break
                if encontrado:
                    break
            
            if not encontrado:
                print(f"   ❌ {campo}: não encontrado")
        
        # 6. Verificar dados da primeira linha
        print(f"\n📝 AMOSTRA (primeira linha):")
        primeira_linha = df.iloc[0]
        for col in df.columns:
            valor = primeira_linha[col]
            print(f"   {col}: {valor} (tipo: {type(valor).__name__})")
        
        # 7. Verificar se tem colunas obrigatórias
        campos_obrigatorios = ['data', 'descricao', 'valor']
        campos_encontrados = list(mapeamento_encontrado.keys())
        
        print(f"\n✅ RESULTADO:")
        if all(campo in campos_encontrados for campo in campos_obrigatorios):
            print("   ✅ Mapeamento PagBank: SUCESSO")
            print("   ✅ Arquivo deve importar corretamente!")
        else:
            faltando = [c for c in campos_obrigatorios if c not in campos_encontrados]
            print(f"   ❌ Mapeamento PagBank: FALHOU")
            print(f"   ❌ Campos faltando: {faltando}")
            print("   ⚠️  Tentará mapeamento genérico...")
        
    except Exception as e:
        print(f"❌ ERRO ao analisar arquivo: {str(e)}")

if __name__ == "__main__":
    # Testar arquivos disponíveis
    arquivos_teste = [
        'extrato_teste_novo.csv',
        'extrato_novo_teste.csv'
    ]
    
    for arquivo in arquivos_teste:
        if os.path.exists(arquivo):
            diagnosticar_arquivo(arquivo)
            print("\n" + "="*50 + "\n")