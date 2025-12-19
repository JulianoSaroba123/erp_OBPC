from app import create_app
from app.eventos.eventos_model import Evento
from datetime import datetime

app = create_app()
with app.app_context():
    print('=== DEBUG EVENTOS ===')
    
    # Verificar total de eventos no banco
    total_eventos = Evento.query.count()
    print(f'Total de eventos no banco: {total_eventos}')
    
    # Verificar eventos próximos
    agora = datetime.now()
    print(f'Data/hora atual: {agora}')
    
    proximos = Evento.query.filter(
        Evento.data_inicio >= agora,
        Evento.status != 'Cancelado'
    ).order_by(Evento.data_inicio).limit(3).all()
    
    print(f'Eventos próximos encontrados: {len(proximos)}')
    
    if proximos:
        for evento in proximos:
            print(f'- {evento.titulo} em {evento.data_inicio}')
    
    # Verificar todos os eventos (independente da data)
    todos_eventos = Evento.query.all()
    print(f'\nTodos os eventos:')
    for evento in todos_eventos:
        print(f'- {evento.titulo} em {evento.data_inicio} (status: {evento.status})')
        
    # Criar evento de teste se não houver nenhum
    if total_eventos == 0:
        print('\n=== CRIANDO EVENTO DE TESTE ===')
        from datetime import timedelta
        evento_teste = Evento(
            titulo='Culto de Domingo',
            data_inicio=datetime.now() + timedelta(days=1),
            data_fim=datetime.now() + timedelta(days=1, hours=2),
            local='Igreja',
            status='Agendado'
        )
        from app.extensoes import db
        db.session.add(evento_teste)
        db.session.commit()
        print('Evento de teste criado!')