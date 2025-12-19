from app import create_app
from app.eventos.eventos_model import Evento
from app.extensoes import db
from datetime import datetime, timedelta

app = create_app()
with app.app_context():
    print('=== CRIANDO EVENTOS FUTUROS ===')
    
    # Criar eventos futuros
    eventos_futuros = [
        {
            'titulo': 'Culto de Domingo',
            'data_inicio': datetime.now() + timedelta(days=3),
            'data_fim': datetime.now() + timedelta(days=3, hours=2),
            'local': 'Templo Principal',
            'responsavel': 'Pastor Dirigente',
            'status': 'Agendado',
            'descricao': 'Culto dominical com pregação e louvor'
        },
        {
            'titulo': 'Escola Bíblica Dominical',
            'data_inicio': datetime.now() + timedelta(days=3, hours=-1),
            'data_fim': datetime.now() + timedelta(days=3),
            'local': 'Salas de Aula',
            'responsavel': 'Superintendente',
            'status': 'Agendado',
            'descricao': 'Estudo bíblico por faixa etária'
        },
        {
            'titulo': 'Reunião de Oração',
            'data_inicio': datetime.now() + timedelta(days=1),
            'data_fim': datetime.now() + timedelta(days=1, hours=1),
            'local': 'Salão Social',
            'responsavel': 'Pastora',
            'status': 'Agendado',
            'descricao': 'Momento de oração e intercessão'
        },
        {
            'titulo': 'Ensaio do Coral',
            'data_inicio': datetime.now() + timedelta(days=5),
            'data_fim': datetime.now() + timedelta(days=5, hours=2),
            'local': 'Templo Principal',
            'responsavel': 'Regente',
            'status': 'Agendado',
            'descricao': 'Ensaio para o culto de domingo'
        }
    ]
    
    for dados_evento in eventos_futuros:
        evento = Evento(**dados_evento)
        db.session.add(evento)
        print(f'Criado: {dados_evento["titulo"]} em {dados_evento["data_inicio"]}')
    
    db.session.commit()
    print('\\n✅ Eventos futuros criados com sucesso!')
    
    # Verificar eventos próximos novamente
    proximos = Evento.query.filter(
        Evento.data_inicio >= datetime.now(),
        Evento.status != 'Cancelado'
    ).order_by(Evento.data_inicio).limit(3).all()
    
    print(f'\\nEventos próximos agora: {len(proximos)}')
    for evento in proximos:
        print(f'- {evento.titulo} em {evento.data_inicio}')