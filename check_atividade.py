from app import create_app, db
from app.departamentos.departamentos_model import CronogramaDepartamento
from datetime import date

app = create_app()
ctx = app.app_context()
ctx.push()

atividade = CronogramaDepartamento.query.first()
if atividade:
    print(f'Titulo: {atividade.titulo}')
    print(f'Data evento: {atividade.data_evento}')
    print(f'Hoje: {date.today()}')
    print(f'É futura? {atividade.data_evento >= date.today()}')
    print(f'Ativo: {atividade.ativo}')
    print(f'Exibir no painel: {atividade.exibir_no_painel}')
    print(f'Departamento ID: {atividade.departamento_id}')
    if atividade.departamento:
        print(f'Departamento nome: {atividade.departamento.nome}')
    else:
        print('Departamento: None')
else:
    print('Nenhuma atividade encontrada')

ctx.pop()
