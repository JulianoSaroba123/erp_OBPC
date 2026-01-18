"""
Script para adicionar campos CPF, número e bairro na tabela de membros
"""

from app import create_app, db
from sqlalchemy import text

def adicionar_campos_membros():
    """Adiciona os novos campos na tabela membros"""
    app = create_app()
    
    with app.app_context():
        try:
            print("Verificando e adicionando campos na tabela membros...")
            
            # Verifica se as colunas já existem
            inspector = db.inspect(db.engine)
            colunas_existentes = [col['name'] for col in inspector.get_columns('membros')]
            
            # Adiciona CPF se não existir
            if 'cpf' not in colunas_existentes:
                print("Adicionando coluna 'cpf'...")
                db.session.execute(text("""
                    ALTER TABLE membros 
                    ADD COLUMN cpf VARCHAR(14)
                """))
                print("✓ Coluna 'cpf' adicionada com sucesso!")
            else:
                print("✓ Coluna 'cpf' já existe.")
            
            # Adiciona número se não existir
            if 'numero' not in colunas_existentes:
                print("Adicionando coluna 'numero'...")
                db.session.execute(text("""
                    ALTER TABLE membros 
                    ADD COLUMN numero VARCHAR(10)
                """))
                print("✓ Coluna 'numero' adicionada com sucesso!")
            else:
                print("✓ Coluna 'numero' já existe.")
            
            # Adiciona bairro se não existir
            if 'bairro' not in colunas_existentes:
                print("Adicionando coluna 'bairro'...")
                db.session.execute(text("""
                    ALTER TABLE membros 
                    ADD COLUMN bairro VARCHAR(100)
                """))
                print("✓ Coluna 'bairro' adicionada com sucesso!")
            else:
                print("✓ Coluna 'bairro' já existe.")
            
            db.session.commit()
            print("\n✅ Todas as alterações foram aplicadas com sucesso!")
            print("\nNovos campos disponíveis:")
            print("  - CPF (formato: XXX.XXX.XXX-XX)")
            print("  - Número (número do endereço)")
            print("  - Bairro (bairro do endereço)")
            
        except Exception as e:
            db.session.rollback()
            print(f"\n❌ Erro ao adicionar campos: {e}")
            raise

if __name__ == "__main__":
    adicionar_campos_membros()
