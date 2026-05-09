"""
Script para criar a tabela de recibos no banco de dados
Executar: python configurar_banco_recibos.py
"""

from app import create_app
from app.extensoes import db
from app.financeiro.recibo_model import Recibo
from sqlalchemy import inspect

def verificar_tabela_existe(engine, nome_tabela):
    """Verifica se uma tabela existe no banco"""
    inspector = inspect(engine)
    return nome_tabela in inspector.get_table_names()

def main():
    print("="*60)
    print("CONFIGURAÇÃO DO BANCO DE DADOS - RECIBOS")
    print("="*60)
    
    # Criar aplicação
    app = create_app()
    
    with app.app_context():
        try:
            # Verificar se a tabela já existe
            engine = db.engine
            tabela_existe = verificar_tabela_existe(engine, 'recibo')
            
            if tabela_existe:
                print("\n⚠️  A tabela 'recibo' já existe no banco de dados!")
                resposta = input("\nDeseja recriar a tabela? (ATENÇÃO: isso apagará todos os dados) [s/N]: ")
                
                if resposta.lower() == 's':
                    print("\n🗑️  Excluindo tabela existente...")
                    Recibo.__table__.drop(db.engine)
                    print("✅ Tabela excluída com sucesso!")
                    
                    print("\n📝 Criando nova tabela de recibos...")
                    db.create_all()
                    print("✅ Tabela 'recibo' criada com sucesso!")
                else:
                    print("\n❌ Operação cancelada pelo usuário.")
                    return
            else:
                # Criar apenas a tabela de recibos
                print("\n📝 Criando tabela de recibos...")
                db.create_all()
                print("✅ Tabela 'recibo' criada com sucesso!")
            
            # Mostrar estrutura da tabela
            print("\n" + "="*60)
            print("ESTRUTURA DA TABELA CRIADA:")
            print("="*60)
            print("\nTabela: recibo")
            print("\nColunas:")
            print("  - id (INTEGER, PRIMARY KEY)")
            print("  - numero_recibo (VARCHAR(50), UNIQUE)")
            print("  - nome_recebedor (VARCHAR(200))")
            print("  - cpf_cnpj_recebedor (VARCHAR(20))")
            print("  - valor (NUMERIC(10, 2))")
            print("  - data_pagamento (DATE)")
            print("  - referente_a (TEXT)")
            print("  - forma_pagamento (VARCHAR(50))")
            print("  - observacoes (TEXT)")
            print("  - criado_em (DATETIME)")
            print("  - criado_por (VARCHAR(100))")
            print("  - pdf_gerado (BOOLEAN, default=False)")
            
            print("\n" + "="*60)
            print("✅ CONFIGURAÇÃO CONCLUÍDA COM SUCESSO!")
            print("="*60)
            print("\nPróximos passos:")
            print("1. Acesse o sistema")
            print("2. Vá em Financeiro > Emitir Recibo")
            print("3. Preencha os dados e gere seu primeiro recibo")
            print("\nOu acesse diretamente: Financeiro > Gerenciar Recibos")
            print("="*60)
            
        except Exception as e:
            print(f"\n❌ Erro ao configurar banco de dados: {str(e)}")
            import traceback
            print("\nDetalhes do erro:")
            print(traceback.format_exc())
            return

if __name__ == "__main__":
    main()
