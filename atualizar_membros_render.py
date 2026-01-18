"""
Script para atualizar a tabela de membros no PostgreSQL do Render
Adiciona os novos campos: CPF, número, bairro, estado civil, teologia e serviço
"""

import os
from sqlalchemy import create_engine, text, inspect

def atualizar_tabela_membros():
    """Atualiza a tabela membros no PostgreSQL do Render"""
    
    # Pega a URL do banco de dados do Render
    database_url = os.environ.get('DATABASE_URL')
    
    if not database_url:
        print("❌ Variável DATABASE_URL não encontrada!")
        print("Configure a variável de ambiente DATABASE_URL com a string de conexão do PostgreSQL")
        return
    
    # Corrige URL do Render (postgres:// -> postgresql://)
    if database_url.startswith('postgres://'):
        database_url = database_url.replace('postgres://', 'postgresql://', 1)
    
    print(f"🔗 Conectando ao banco de dados do Render...")
    
    try:
        engine = create_engine(database_url)
        
        with engine.connect() as connection:
            # Verifica quais colunas já existem
            inspector = inspect(engine)
            colunas_existentes = [col['name'] for col in inspector.get_columns('membros')]
            
            print("\n📋 Verificando e adicionando campos na tabela membros...")
            
            # Lista de colunas para adicionar
            novas_colunas = [
                ('cpf', 'VARCHAR(14)', '📋 CPF'),
                ('numero', 'VARCHAR(10)', '🏠 Número'),
                ('bairro', 'VARCHAR(100)', '🏘️ Bairro'),
                ('estado_civil', 'VARCHAR(20)', '💍 Estado Civil'),
                ('curso_teologia', 'BOOLEAN DEFAULT FALSE', '🎓 Curso de Teologia'),
                ('nivel_teologia', 'VARCHAR(20)', '📚 Nível de Teologia'),
                ('instituto', 'VARCHAR(200)', '🏫 Instituto'),
                ('deseja_servir', 'BOOLEAN DEFAULT FALSE', '🙏 Deseja Servir'),
                ('area_servir', 'VARCHAR(200)', '⛪ Área de Serviço')
            ]
            
            # Adiciona cada coluna se não existir
            for coluna, tipo, descricao in novas_colunas:
                if coluna not in colunas_existentes:
                    try:
                        sql = text(f"ALTER TABLE membros ADD COLUMN {coluna} {tipo}")
                        connection.execute(sql)
                        connection.commit()
                        print(f"   ✅ {descricao} ({coluna}) adicionado")
                    except Exception as e:
                        print(f"   ⚠️  Erro ao adicionar {coluna}: {e}")
                else:
                    print(f"   ✓ {descricao} ({coluna}) já existe")
            
            print("\n✅ Atualização concluída com sucesso!")
            print("\n📊 Novos campos disponíveis:")
            print("   • CPF com máscara automática")
            print("   • Endereço completo (número e bairro)")
            print("   • Estado Civil")
            print("   • Formação em Teologia (curso, nível, instituto)")
            print("   • Interesse em servir (área de ministério)")
            
    except Exception as e:
        print(f"\n❌ Erro ao conectar ou atualizar banco de dados:")
        print(f"   {e}")
        raise

if __name__ == "__main__":
    print("=" * 60)
    print("🔧 ATUALIZAÇÃO DA TABELA MEMBROS - RENDER")
    print("=" * 60)
    atualizar_tabela_membros()
    print("=" * 60)
