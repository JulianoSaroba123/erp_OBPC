from run import app
from app import db
from app.financeiro.financeiro_model import Lancamento
from sqlalchemy import extract

app.app_context().push()

print('Meses com lançamentos:')
for mes in range(1, 13):
    count = Lancamento.query.filter(
        extract('month', Lancamento.data) == mes, 
        extract('year', Lancamento.data) == 2025
    ).count()
    if count > 0:
        print(f'  Mês {mes:02d}/2025: {count} lançamentos')

# Buscar mês com lançamentos que tenham comprovante
print('\nMeses com comprovantes:')
for mes in range(1, 13):
    count = Lancamento.query.filter(
        extract('month', Lancamento.data) == mes, 
        extract('year', Lancamento.data) == 2025,
        Lancamento.comprovante.isnot(None)
    ).count()
    if count > 0:
        print(f'  Mês {mes:02d}/2025: {count} comprovantes')