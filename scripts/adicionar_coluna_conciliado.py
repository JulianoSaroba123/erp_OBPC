import sqlite3
import os

base_dir = os.path.dirname(os.path.dirname(__file__))
# Possíveis caminhos do banco
candidates = [
    os.path.join(base_dir, 'igreja.db'),
    os.path.join(base_dir, 'database.db'),
    os.path.join(base_dir, 'instance', 'igreja.db'),
    os.path.join(base_dir, 'instance', 'database.db'),
]
DB_PATH = None
for c in candidates:
    if os.path.exists(c):
        DB_PATH = c
        break

print('Usando DB:', DB_PATH)
if not DB_PATH:
    print('Nenhum arquivo de banco encontrado entre os candidatos.')
    raise SystemExit(1)

conn = sqlite3.connect(DB_PATH)
cur = conn.cursor()

# Verificar se coluna já existe
cur.execute("PRAGMA table_info(lancamentos);")
cols = [r[1] for r in cur.fetchall()]
print('Colunas atuais:', cols)
if 'conciliado' in cols:
    print('Coluna conciliado já existe. Nada a fazer.')
else:
    try:
        cur.execute("ALTER TABLE lancamentos ADD COLUMN conciliado INTEGER DEFAULT 0;")
        conn.commit()
        print('Coluna conciliado adicionada com sucesso.')
    except Exception as e:
        print('Erro ao adicionar coluna conciliado:', e)
        conn.rollback()

# Mostrar contagem de pendentes
cur.execute("SELECT COUNT(*) FROM lancamentos WHERE conciliado IS NULL OR conciliado = 0")
count = cur.fetchone()[0]
print('Total de lançamentos não conciliados:', count)

conn.close()
