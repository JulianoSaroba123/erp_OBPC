from app import create_app
from app.extensoes import db

app = create_app()

with app.app_context():
    # Cria as tabelas que ainda não existem (incluindo conciliacao_pares)
    db.create_all()
    # Verifica existência
    inspector = None
    try:
        from sqlalchemy import inspect
        inspector = inspect(db.engine)
        tabelas = inspector.get_table_names()
    except Exception:
        tabelas = []

    print('Tabelas no banco:', tabelas)
    if 'conciliacao_pares' in tabelas:
        print('Tabela conciliacao_pares criada ou já existia.')
    else:
        print('Tabela conciliacao_pares NÃO encontrada.')
