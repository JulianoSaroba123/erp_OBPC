from app import create_app, db
from app.notificacoes.notificacoes_model import ConfiguracaoNotificacoes
from sqlalchemy import inspect, text

app = create_app()
ctx = app.app_context()
ctx.push()

# Criar todas as tabelas
print("Criando tabelas...")
db.create_all()

# Verificar se a coluna existe
inspector = inspect(db.engine)
columns = [col['name'] for col in inspector.get_columns('configuracao_notificacoes')]
print(f"Colunas: {columns}")

# Adicionar coluna se não existir
if 'hora_notificacao_automatica' not in columns:
    print("Adicionando coluna hora_notificacao_automatica...")
    db.session.execute(text("ALTER TABLE configuracao_notificacoes ADD COLUMN hora_notificacao_automatica VARCHAR(5) DEFAULT '08:00'"))
    db.session.commit()
    print("Coluna adicionada!")

# Verificar configuração
config = ConfiguracaoNotificacoes.query.first()
if not config:
    print("Criando configuração padrão...")
    config = ConfiguracaoNotificacoes(
        email_habilitado=False,
        whatsapp_habilitado=False,
        notificar_aniversariantes=True,
        notificar_admin=True,
        dias_antes=0,
        hora_notificacao_automatica='08:00'
    )
    db.session.add(config)
    db.session.commit()
    print("Configuração criada!")
else:
    print(f"Configuração existe! Hora: {config.hora_notificacao_automatica}")
    if config.hora_notificacao_automatica is None:
        config.hora_notificacao_automatica = '08:00'
        db.session.commit()
        print("Hora atualizada para 08:00")

print("\n✅ Processo concluído! Atualize a página do navegador.")
