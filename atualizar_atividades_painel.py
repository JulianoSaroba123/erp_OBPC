from app import create_app
from app.departamentos.departamentos_model import CronogramaDepartamento

app = create_app()
app.app_context().push()

print("=" * 60)
print("ATUALIZANDO ATIVIDADES PARA EXIBIR NO PAINEL")
print("=" * 60)

# Buscar todas as atividades ativas
atividades_ativas = CronogramaDepartamento.query.filter_by(ativo=True).all()

print(f"\nTotal de atividades ativas encontradas: {len(atividades_ativas)}")

if atividades_ativas:
    # Atualizar todas para exibir no painel
    contador = 0
    for atividade in atividades_ativas:
        if not atividade.exibir_no_painel:
            atividade.exibir_no_painel = True
            contador += 1
    
    # Salvar as alterações
    from app import db
    db.session.commit()
    
    print(f"✅ {contador} atividades atualizadas para exibir no painel!")
    
    print("\n" + "=" * 60)
    print("ATIVIDADES ATUALIZADAS:")
    print("=" * 60)
    for i, atividade in enumerate(atividades_ativas[:10], 1):
        print(f"\n{i}. {atividade.titulo}")
        print(f"   Data: {atividade.data_evento}")
        print(f"   Exibir no painel: {atividade.exibir_no_painel}")
        print(f"   Departamento: {atividade.departamento.nome if atividade.departamento else 'N/A'}")
else:
    print("\n⚠️ Nenhuma atividade ativa encontrada no banco de dados.")
    print("Você precisa criar atividades nos departamentos primeiro.")

print("\n" + "=" * 60)
print("CONCLUÍDO!")
print("=" * 60)
