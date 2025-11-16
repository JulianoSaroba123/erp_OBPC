import sqlite3

# Conectar diretamente ao banco
conn = sqlite3.connect('instance/database.db')
cursor = conn.cursor()

print("=== LISTANDO TABELAS DO BANCO ===")

# Listar todas as tabelas
cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
tabelas = cursor.fetchall()

for tabela in tabelas:
    print(f"Tabela: {tabela[0]}")

# Verificar estrutura das tabelas relacionadas a lançamentos
print(f"\n=== PROCURANDO TABELAS COM 'LANC' ===")
for tabela in tabelas:
    nome = tabela[0].lower()
    if 'lanc' in nome or 'entrada' in nome or 'saida' in nome or 'financeiro' in nome:
        print(f"\nTabela encontrada: {tabela[0]}")
        
        # Mostrar estrutura
        cursor.execute(f"PRAGMA table_info({tabela[0]})")
        colunas = cursor.fetchall()
        print("Colunas:")
        for coluna in colunas:
            print(f"  - {coluna[1]} ({coluna[2]})")

conn.close()