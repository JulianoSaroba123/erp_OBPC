"""
Script para adicionar tabela Projetos e campo projeto_id em Lancamentos
Execute: python atualizar_banco_projetos.py
"""
from app import create_app
from app.extensoes import db
from app.financeiro.projeto_model import Projeto
from sqlalchemy import text

def atualizar_banco():
    app = create_app()
    
    with app.app_context():
        print("=== Atualizando banco de dados para suportar Projetos ===\n")
        
        try:
            # 1. Criar tabela projetos
            print("1. Criando tabela 'projetos'...")
            db.create_all()
            print("   ✅ Tabela 'projetos' criada com sucesso!\n")
            
            # 2. Adicionar coluna projeto_id na tabela lancamentos (se não existir)
            print("2. Adicionando coluna 'projeto_id' em 'lancamentos'...")
            try:
                with db.engine.connect() as conn:
                    # Verifica se a coluna já existe
                    result = conn.execute(text("PRAGMA table_info(lancamentos)"))
                    columns = [row[1] for row in result]
                    
                    if 'projeto_id' not in columns:
                        conn.execute(text("ALTER TABLE lancamentos ADD COLUMN projeto_id INTEGER"))
                        conn.commit()
                        print("   ✅ Coluna 'projeto_id' adicionada com sucesso!\n")
                    else:
                        print("   ⚠️  Coluna 'projeto_id' já existe!\n")
            except Exception as e:
                print(f"   ⚠️  Erro ao adicionar coluna (pode já existir): {e}\n")
            
            # 3. Criar alguns projetos de exemplo
            print("3. Criando projetos de exemplo...")
            
            projetos_exemplo = [
                {
                    'nome': 'MENIBRAC',
                    'descricao': 'Doações destinadas ao departamento MENIBRAC',
                    'tipo': 'Doação',
                    'status': 'Ativo'
                },
                {
                    'nome': 'Anistia 30%',
                    'descricao': 'Recurso anistiado dos 30% pela sede para melhorias no templo',
                    'tipo': 'Anistia',
                    'status': 'Ativo',
                    'meta_valor': 10000.00
                },
                {
                    'nome': 'Reformas Gerais',
                    'descricao': 'Reformas e manutenções do templo',
                    'tipo': 'Reforma',
                    'status': 'Ativo'
                }
            ]
            
            for proj_data in projetos_exemplo:
                # Verifica se já existe
                existe = Projeto.query.filter_by(nome=proj_data['nome']).first()
                if not existe:
                    projeto = Projeto(**proj_data)
                    db.session.add(projeto)
                    print(f"   ✅ Projeto '{proj_data['nome']}' criado!")
                else:
                    print(f"   ⚠️  Projeto '{proj_data['nome']}' já existe!")
            
            db.session.commit()
            print("\n=== Atualização concluída com sucesso! ===")
            print("\nPróximos passos:")
            print("1. Reinicie o servidor Flask")
            print("2. Acesse Financeiro > Gerenciar Projetos")
            print("3. Ao cadastrar lançamentos com 'Outras Ofertas' ou 'DESTINAÇÃO', selecione o projeto\n")
            
        except Exception as e:
            print(f"\n❌ Erro durante atualização: {e}")
            db.session.rollback()
            raise

if __name__ == '__main__':
    atualizar_banco()
