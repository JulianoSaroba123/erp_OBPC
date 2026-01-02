from app import create_app, db
from app.departamentos.departamentos_model import CronogramaDepartamento

app = create_app()
ctx = app.app_context()
ctx.push()

print("=" * 70)
print("LIMPANDO ATIVIDADES - DEIXANDO APENAS UMA DE EXEMPLO")
print("=" * 70)

# Buscar todas as atividades
todas_atividades = CronogramaDepartamento.query.order_by(
    CronogramaDepartamento.data_evento.asc()
).all()

print(f"\nTotal de atividades no banco: {len(todas_atividades)}")

if len(todas_atividades) > 1:
    # Manter apenas a primeira (mais proxima)
    atividade_manter = todas_atividades[0]
    print(f"\nAtividade mantida:")
    print(f"  - {atividade_manter.titulo}")
    print(f"  - Data: {atividade_manter.data_evento.strftime('%d/%m/%Y')}")
    print(f"  - Horario: {atividade_manter.horario}")
    
    # Remover as outras
    atividades_remover = todas_atividades[1:]
    print(f"\nRemovendo {len(atividades_remover)} atividades...")
    
    for atividade in atividades_remover:
        print(f"  - Removendo: {atividade.titulo} ({atividade.data_evento.strftime('%d/%m/%Y')})")
        db.session.delete(atividade)
    
    db.session.commit()
    print(f"\n{len(atividades_remover)} atividades removidas com sucesso!")
    
elif len(todas_atividades) == 1:
    print("\nJa existe apenas 1 atividade no banco:")
    print(f"  - {todas_atividades[0].titulo} ({todas_atividades[0].data_evento.strftime('%d/%m/%Y')})")
else:
    print("\nNenhuma atividade encontrada no banco.")

print("\n" + "=" * 70)
print("CONCLUIDO!")
print("=" * 70)

ctx.pop()
