"""
Script para testar importação do extrato PagSeguro
"""
from app import create_app, db
from app.financeiro.financeiro_model import Lancamento
import pandas as pd
from datetime import datetime

app = create_app()

with app.app_context():
    print("=" * 80)
    print("TESTE DE IMPORTAÇÃO - EXTRATO PAGSEGURO")
    print("=" * 80)
    
    # Ler o arquivo CSV
    arquivo = r"f:\Ano 2025\Ano 2025\ERP_OBPC\Extrato da Conta - PagSeguro.csv"
    
    print(f"\n📂 Lendo arquivo: {arquivo}")
    
    try:
        # Ler CSV com encoding correto e separador ponto-e-vírgula
        df = pd.read_csv(arquivo, sep=';', encoding='utf-8')
        
        print(f"✅ Arquivo lido com sucesso!")
        print(f"\n📊 Total de registros encontrados: {len(df)}")
        print(f"\n📋 Colunas encontradas: {list(df.columns)}")
        
        print("\n" + "=" * 80)
        print("PRIMEIRAS 5 LINHAS DO ARQUIVO")
        print("=" * 80)
        print(df.head())
        
        print("\n" + "=" * 80)
        print("PROCESSANDO LANÇAMENTOS")
        print("=" * 80)
        
        # Limpar lançamentos de teste anteriores
        Lancamento.query.filter_by(banco_origem='pagseguro_teste').delete()
        db.session.commit()
        
        importados = 0
        erros = 0
        
        for idx, row in df.iterrows():
            try:
                # Converter data (formato DD/MM/YYYY)
                data_str = str(row['DATA'])
                data_obj = datetime.strptime(data_str, '%d/%m/%Y').date()
                
                # Converter valor (formato brasileiro: vírgula como decimal)
                valor_str = str(row['VALOR']).replace(',', '.')
                valor = abs(float(valor_str))
                
                # Determinar tipo (Entrada ou Saída)
                tipo_transacao = str(row['TIPO'])
                descricao = str(row['DESCRICAO'])
                
                # Identificar se é entrada ou saída
                if 'enviado' in tipo_transacao.lower() or valor_str.startswith('-'):
                    tipo = 'Saída'
                elif 'recebido' in tipo_transacao.lower() or 'rendimento' in tipo_transacao.lower():
                    tipo = 'Entrada'
                else:
                    tipo = 'Entrada'  # Default
                
                # Criar lançamento
                novo = Lancamento(
                    data=data_obj,
                    tipo=tipo,
                    categoria='PagSeguro',
                    descricao=f"{tipo_transacao} - {descricao}",
                    valor=valor,
                    origem='importado',
                    banco_origem='pagseguro_teste',
                    documento_ref=str(row['CODIGO DA TRANSACAO']),
                    observacoes=f"Importado de extrato PagSeguro"
                )
                
                db.session.add(novo)
                importados += 1
                
                print(f"✅ {idx+1:2d}. {data_obj} | {tipo:7s} | R$ {valor:9.2f} | {descricao[:40]}")
                
            except Exception as e:
                erros += 1
                print(f"❌ {idx+1:2d}. ERRO: {str(e)}")
        
        # Salvar no banco
        db.session.commit()
        
        print("\n" + "=" * 80)
        print("RESULTADO DA IMPORTAÇÃO")
        print("=" * 80)
        print(f"✅ Importados com sucesso: {importados}")
        print(f"❌ Erros: {erros}")
        print(f"📊 Total processado: {len(df)}")
        
        # Verificar no banco
        print("\n" + "=" * 80)
        print("VERIFICAÇÃO NO BANCO DE DADOS")
        print("=" * 80)
        
        total_banco = Lancamento.query.filter_by(banco_origem='pagseguro_teste').count()
        print(f"💾 Lançamentos no banco (pagseguro_teste): {total_banco}")
        
        # Calcular totais
        entradas = db.session.query(db.func.sum(Lancamento.valor))\
                    .filter(Lancamento.banco_origem == 'pagseguro_teste', 
                           Lancamento.tipo == 'Entrada').scalar() or 0
        
        saidas = db.session.query(db.func.sum(Lancamento.valor))\
                  .filter(Lancamento.banco_origem == 'pagseguro_teste',
                         Lancamento.tipo == 'Saída').scalar() or 0
        
        print(f"\n💰 TOTAIS:")
        print(f"   Entradas: R$ {entradas:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'))
        print(f"   Saídas:   R$ {saidas:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'))
        print(f"   Saldo:    R$ {entradas - saidas:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'))
        
        print("\n" + "=" * 80)
        print("✅ TESTE CONCLUÍDO COM SUCESSO!")
        print("=" * 80)
        
    except Exception as e:
        print(f"\n❌ ERRO GERAL: {str(e)}")
        import traceback
        traceback.print_exc()
