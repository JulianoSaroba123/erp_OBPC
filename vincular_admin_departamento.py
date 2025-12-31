import sqlite3

db_path = r"f:\Ano 2025\Ano 2025\ERP_OBPC\instance\igreja.db"

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

print("🔧 Vinculando usuário admin ao departamento 1...")

# Atualizar usuário admin para ter departamento_id = 1
cursor.execute("UPDATE usuarios SET departamento_id = 1 WHERE email = 'admin@obpc.com'")

conn.commit()

# Verificar
cursor.execute("SELECT nome, email, departamento_id FROM usuarios WHERE email = 'admin@obpc.com'")
user = cursor.fetchone()

print(f"\n✅ Usuário atualizado:")
print(f"   Nome: {user[0]}")
print(f"   Email: {user[1]}")
print(f"   Departamento ID: {user[2]}")

conn.close()

print("\n🎉 Pronto! Agora faça logout e login novamente para ver as atividades no painel.")
