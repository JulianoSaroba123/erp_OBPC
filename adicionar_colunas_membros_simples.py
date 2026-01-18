"""
Script simplificado para verificar e adicionar colunas à tabela membros
"""
import sqlite3
import os

# Caminho do banco de dados
db_path = 'instance/database.db'

if not os.path.exists(db_path):
    print(f"❌ Banco de dados não encontrado: {db_path}")
    exit(1)

print(f"📂 Conectando ao banco: {db_path}\n")

# Conectar ao banco
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Verificar estrutura atual
cursor.execute("PRAGMA table_info(membros)")
colunas_atuais = {col[1]: col for col in cursor.fetchall()}

print("📋 Colunas existentes:")
for nome in colunas_atuais.keys():
    print(f"   • {nome}")

# Definir novas colunas que precisam ser adicionadas
novas_colunas = {
    'cpf': 'VARCHAR(14)',
    'numero': 'VARCHAR(10)',
    'bairro': 'VARCHAR(100)',
    'estado_civil': 'VARCHAR(20)',
    'curso_teologia': 'BOOLEAN DEFAULT 0',
    'nivel_teologia': 'VARCHAR(20)',
    'instituto': 'VARCHAR(200)',
    'deseja_servir': 'BOOLEAN DEFAULT 0',
    'area_servir': 'VARCHAR(200)'
}

print("\n🔧 Adicionando colunas faltantes...\n")

colunas_adicionadas = 0
for nome_coluna, tipo_coluna in novas_colunas.items():
    if nome_coluna not in colunas_atuais:
        try:
            sql = f"ALTER TABLE membros ADD COLUMN {nome_coluna} {tipo_coluna}"
            cursor.execute(sql)
            print(f"   ✅ Coluna '{nome_coluna}' adicionada")
            colunas_adicionadas += 1
        except Exception as e:
            print(f"   ❌ Erro ao adicionar '{nome_coluna}': {e}")
    else:
        print(f"   ⏭️  Coluna '{nome_coluna}' já existe")

# Salvar mudanças
conn.commit()

# Verificar estrutura final
cursor.execute("PRAGMA table_info(membros)")
colunas_finais = cursor.fetchall()

print(f"\n✅ Processo concluído!")
print(f"📊 Total de colunas adicionadas: {colunas_adicionadas}")
print(f"📊 Total de colunas na tabela: {len(colunas_finais)}")

conn.close()
