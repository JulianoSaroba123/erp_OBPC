import sqlite3

conn = sqlite3.connect('igreja.db')
cursor = conn.cursor()

# Verificar todas as tabelas
cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
tabelas = cursor.fetchall()

print("📋 TABELAS NO BANCO:")
for tabela in tabelas:
    print(f"   - {tabela[0]}")

conn.close()