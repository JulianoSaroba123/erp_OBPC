"""
Script para adicionar coluna logo_version à tabela configuracoes
"""
import sqlite3

def adicionar_coluna_logo_version():
    try:
        # Conectar ao banco
        conn = sqlite3.connect('instance/igreja.db')
        cursor = conn.cursor()
        
        # Verificar se a coluna já existe
        cursor.execute("PRAGMA table_info(configuracoes)")
        colunas = [coluna[1] for coluna in cursor.fetchall()]
        
        if 'logo_version' in colunas:
            print("✓ Coluna 'logo_version' já existe na tabela configuracoes")
        else:
            # Adicionar coluna logo_version
            cursor.execute("""
                ALTER TABLE configuracoes 
                ADD COLUMN logo_version INTEGER NOT NULL DEFAULT 1
            """)
            print("✓ Coluna 'logo_version' adicionada com sucesso!")
        
        # Garantir que o registro existente tenha logo_version = 1
        cursor.execute("UPDATE configuracoes SET logo_version = 1 WHERE logo_version IS NULL OR logo_version = 0")
        rows_updated = cursor.rowcount
        
        if rows_updated > 0:
            print(f"✓ {rows_updated} registro(s) atualizado(s) com logo_version = 1")
        
        conn.commit()
        conn.close()
        
        print("\n✅ Migração concluída com sucesso!")
        
    except Exception as e:
        print(f"❌ Erro ao adicionar coluna: {str(e)}")
        if 'conn' in locals():
            conn.rollback()
            conn.close()

if __name__ == '__main__':
    adicionar_coluna_logo_version()
