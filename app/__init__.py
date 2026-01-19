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
from app.secretaria.atas.atas_routes import atas_bp
from app.secretaria.inventario.inventario_routes import inventario_bp
from app.secretaria.oficios.oficios_routes import oficios_bp
from app.secretaria.participacao.participacao_routes import participacao_bp
from app.midia.midia_routes import midia_bp
from app.escala_ministerial.escala_routes import escala_ministerial_bp
from app.financeiro.routes_conciliacao import conciliacao_bp
from app.agenda_pastoral.agenda_pastoral_routes import agenda_pastoral_bp

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
    app.register_blueprint(atas_bp)
    app.register_blueprint(inventario_bp)
    app.register_blueprint(oficios_bp)
    app.register_blueprint(participacao_bp)
    app.register_blueprint(midia_bp)
    app.register_blueprint(escala_ministerial_bp)
    app.register_blueprint(conciliacao_bp)
    app.register_blueprint(agenda_pastoral_bp)

    # Registro de filtros Jinja2
    @app.template_filter('mes_nome_completo')
    def mes_nome_completo(mes):
        """Converte número do mês para nome completo em português"""
        meses = {
            1: 'Janeiro', 2: 'Fevereiro', 3: 'Março', 4: 'Abril',
            5: 'Maio', 6: 'Junho', 7: 'Julho', 8: 'Agosto', 
            9: 'Setembro', 10: 'Outubro', 11: 'Novembro', 12: 'Dezembro'
        }
        return meses.get(mes, f'Mês {mes}')

    @app.template_filter('valor_com_cor')
    def valor_com_cor(valor):
        """Formata valor com cor vermelha se negativo"""
        valor_formatado = "R$ {:.2f}".format(valor).replace(".", ",")
        if valor < 0:
            return f'<span class="text-danger fw-bold">{valor_formatado}</span>'
        else:
            return valor_formatado

    @app.template_filter('valor_negativo_vermelho')
    def valor_negativo_vermelho(valor):
        """Aplica classe CSS vermelha para valores negativos"""
        if valor < 0:
            return "text-danger"
        return ""

    # Context processor para disponibilizar configurações em todos os templates
    @app.context_processor
    def inject_config():
        """Injeta as configurações da igreja em todos os templates"""
        from app.configuracoes.configuracoes_model import Configuracao
        try:
            config = Configuracao.obter_configuracao()
            return dict(igreja_config=config)
        except Exception as e:
            app.logger.warning(f'Erro ao carregar configurações para template: {str(e)}')
            return dict(igreja_config=None)

    # Cria as tabelas no primeiro uso (pode depois mover isso pro script separado)
    with app.app_context():
        db.create_all()

    return app
