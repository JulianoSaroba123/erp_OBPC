#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
sys.path.append(os.path.abspath('.'))

from app.financeiro.utils.conciliacao_avancada import ImportadorExtrato
import pandas as pd

def testar_importacao_direta():
    """Testa importação sem usar Flask, diretamente na classe"""
    
    print("🧪 TESTE: Importação Direta (sem Flask)")
    print("=" * 50)
    
    # Arquivo de teste
    arquivo = 'extrato_teste_novo.csv'
    
    try:
        # Ler arquivo
        df = pd.read_csv(arquivo)
        print(f"📁 Arquivo lido: {len(df)} linhas, {len(df.columns)} colunas")
        print(f"📋 Colunas: {list(df.columns)}")
        print(f"📝 Amostra:\n{df.head(3)}")
        
        # Criar importador
        importador = ImportadorExtrato()
        
        # Tentar importação
        resultado = importador.importar_arquivo(
            arquivo_path=arquivo,
            banco='PagBank',
            usuario='Teste Automático'
        )
        
        print(f"\n📊 Resultado da importação:")
        for key, value in resultado.items():
            if key == 'erros' and value:
                print(f"  {key}:")
                for erro in value[:3]:  # Mostrar só os primeiros 3 erros
                    print(f"    - {erro[:100]}...")
            else:
                print(f"  {key}: {value}")
        
        if resultado['sucesso']:
            print("✅ Importação realizada com sucesso!")
        else:
            print("❌ Importação falhou")
            if resultado.get('erros'):
                print("Erros encontrados:")
                for erro in resultado['erros'][:3]:
                    print(f"  - {erro[:100]}...")
        
    except Exception as e:
        print(f"❌ Erro no teste: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    testar_importacao_direta()