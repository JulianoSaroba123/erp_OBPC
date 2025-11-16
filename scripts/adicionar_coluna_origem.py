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

print('Procurando DB entre candidatos...')
print('\n'.join(candidates))
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
if 'origem' in cols:
    print('Coluna origem já existe. Nada a fazer.')
else:
    try:
        cur.execute("ALTER TABLE lancamentos ADD COLUMN origem TEXT DEFAULT 'manual';")
        conn.commit()
        print('Coluna origem adicionada com sucesso.')
    except Exception as e:
        print('Erro ao adicionar coluna:', e)
        conn.rollback()

# Mostrar contagem e alguns registros para verificar
cur.execute('SELECT COUNT(*) FROM lancamentos')
count = cur.fetchone()[0]
print('Total de lançamentos:', count)

cur.execute('SELECT id, data, descricao, valor, origem FROM lancamentos ORDER BY id DESC LIMIT 10')
rows = cur.fetchall()
for r in rows:
    print(r)

conn.close()
