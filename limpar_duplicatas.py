from app import create_app, db
from app.departamentos.departamentos_model import CronogramaDepartamento
from datetime import date

app = create_app()
ctx = app.app_context()
ctx.push()

print("=" * 70)
print("REMOVENDO DUPLICATAS DE ATIVIDADES")
print("=" * 70)

# Buscar todas as atividades
todas_atividades = CronogramaDepartamento.query.order_by(
    CronogramaDepartamento.titulo, 
    CronogramaDepartamento.data_evento
).all()

print(f"\nTotal de atividades no banco: {len(todas_atividades)}")

# Agrupar por titulo e data para encontrar duplicatas
atividades_unicas = {}
duplicatas = []

for atividade in todas_atividades:
    chave = f"{atividade.titulo}_{atividade.data_evento}"
    if chave in atividades_unicas:
        duplicatas.append(atividade)
    else:
        atividades_unicas[chave] = atividade

print(f"Atividades únicas: {len(atividades_unicas)}")
print(f"Duplicatas encontradas: {len(duplicatas)}")

if duplicatas:
    print("\nRemovendo duplicatas...")
    for atividade in duplicatas:
        print(f"  - Removendo: {atividade.titulo} ({atividade.data_evento})")
        db.session.delete(atividade)
    
    db.session.commit()
    print(f"\n{len(duplicatas)} duplicatas removidas com sucesso!")
else:
    print("\nNenhuma duplicata encontrada.")

# Verificar resultado final
atividades_finais = CronogramaDepartamento.query.filter(
    CronogramaDepartamento.ativo == True,
    CronogramaDepartamento.exibir_no_painel == True,
    CronogramaDepartamento.data_evento >= date.today()
).order_by(CronogramaDepartamento.data_evento.asc()).all()

print("\n" + "=" * 70)
print("ATIVIDADES QUE APARECERAO NO PAINEL:")
print("=" * 70)
for i, ativ in enumerate(atividades_finais, 1):
    print(f"{i}. {ativ.titulo} - {ativ.data_evento.strftime('%d/%m/%Y')} as {ativ.horario}")

ctx.pop()
