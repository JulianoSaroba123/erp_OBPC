import sqlite3

conn = sqlite3.connect('instance/igreja.db')
cursor = conn.cursor()

cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tabelas = cursor.fetchall()

print("\nTabelas no banco de dados:")
print("-" * 40)
for tabela in tabelas:
    print(f"- {tabela[0]}")

conn.close()
