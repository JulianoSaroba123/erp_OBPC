from flask import Flask
from app.config import Config
from app.extensoes import db, login_manager
from app.usuario.usuario_routes import usuario_bp
from app.membros.membros_routes import membros_bp
from app.obreiros.obreiros_routes import obreiros_bp
from app.departamentos.departamentos_routes import departamentos_bp
from app.financeiro.financeiro_routes import financeiro_bp
from app.eventos.eventos_routes import eventos_bp
from app.configuracoes.configuracoes_routes import configuracoes_bp

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # Inicializa extensões
    db.init_app(app)
    login_manager.init_app(app)

    # Configurações do login
    login_manager.login_view = "usuario.login"
    login_manager.login_message_category = "info"

    # Registro dos Blueprints
    app.register_blueprint(usuario_bp)
    app.register_blueprint(membros_bp)
    app.register_blueprint(obreiros_bp)
    app.register_blueprint(departamentos_bp)
    app.register_blueprint(financeiro_bp)
    app.register_blueprint(eventos_bp)
    app.register_blueprint(configuracoes_bp)

    # Cria as tabelas no primeiro uso (pode depois mover isso pro script separado)
    with app.app_context():
        db.create_all()

    return app
