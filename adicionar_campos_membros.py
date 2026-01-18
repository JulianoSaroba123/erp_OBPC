"""
Script para adicionar novos campos na tabela de membros:
- CPF, número e bairro
- Estado civil
- Curso de teologia, nível e instituto
- Deseja servir e área de serviço
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
            
            # Adiciona estado_civil se não existir
            if 'estado_civil' not in colunas_existentes:
                print("Adicionando coluna 'estado_civil'...")
                db.session.execute(text("""
                    ALTER TABLE membros 
                    ADD COLUMN estado_civil VARCHAR(20)
                """))
                print("✓ Coluna 'estado_civil' adicionada com sucesso!")
            else:
                print("✓ Coluna 'estado_civil' já existe.")
            
            # Adiciona curso_teologia se não existir
            if 'curso_teologia' not in colunas_existentes:
                print("Adicionando coluna 'curso_teologia'...")
                db.session.execute(text("""
                    ALTER TABLE membros 
                    ADD COLUMN curso_teologia BOOLEAN DEFAULT 0
                """))
                print("✓ Coluna 'curso_teologia' adicionada com sucesso!")
            else:
                print("✓ Coluna 'curso_teologia' já existe.")
            
            # Adiciona nivel_teologia se não existir
            if 'nivel_teologia' not in colunas_existentes:
                print("Adicionando coluna 'nivel_teologia'...")
                db.session.execute(text("""
                    ALTER TABLE membros 
                    ADD COLUMN nivel_teologia VARCHAR(20)
                """))
                print("✓ Coluna 'nivel_teologia' adicionada com sucesso!")
            else:
                print("✓ Coluna 'nivel_teologia' já existe.")
            
            # Adiciona instituto se não existir
            if 'instituto' not in colunas_existentes:
                print("Adicionando coluna 'instituto'...")
                db.session.execute(text("""
                    ALTER TABLE membros 
                    ADD COLUMN instituto VARCHAR(200)
                """))
                print("✓ Coluna 'instituto' adicionada com sucesso!")
            else:
                print("✓ Coluna 'instituto' já existe.")
            
            # Adiciona deseja_servir se não existir
            if 'deseja_servir' not in colunas_existentes:
                print("Adicionando coluna 'deseja_servir'...")
                db.session.execute(text("""
                    ALTER TABLE membros 
                    ADD COLUMN deseja_servir BOOLEAN DEFAULT 0
                """))
                print("✓ Coluna 'deseja_servir' adicionada com sucesso!")
            else:
                print("✓ Coluna 'deseja_servir' já existe.")
            
            # Adiciona area_servir se não existir
            if 'area_servir' not in colunas_existentes:
                print("Adicionando coluna 'area_servir'...")
                db.session.execute(text("""
                    ALTER TABLE membros 
                    ADD COLUMN area_servir VARCHAR(200)
                """))
                print("✓ Coluna 'area_servir' adicionada com sucesso!")
            else:
                print("✓ Coluna 'area_servir' já existe.")
            
            db.session.commit()
            print("\n✅ Todas as alterações foram aplicadas com sucesso!")
            print("\nNovos campos disponíveis:")
            print("  📋 CPF (formato: XXX.XXX.XXX-XX)")
            print("  🏠 Número e Bairro (endereço completo)")
            print("  💍 Estado Civil (Solteiro, Casado, Divorciado, Viúvo)")
            print("  🎓 Curso de Teologia (Sim/Não)")
            print("  📚 Nível de Teologia (Básico, Médio, Pleno)")
            print("  🏫 Instituto (nome do seminário)")
            print("  🙏 Deseja Servir (Sim/Não)")
            print("  ⛪ Área de Serviço (ministério de interesse)")
            
        except Exception as e:
            db.session.rollback()
            print(f"\n❌ Erro ao adicionar campos: {e}")
            raise

if __name__ == "__main__":
    adicionar_campos_membros()
