from flask import Flask, redirect, request
from werkzeug.middleware.proxy_fix import ProxyFix
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
from app.notificacoes.notificacoes_routes import notificacoes_bp

# Importar modelos para garantir registro no SQLAlchemy
from app.financeiro.comprovante_model import Comprovante  # Necessário para relacionamento em Lancamento
from app.notificacoes.notificacoes_model import ConfiguracaoNotificacoes, HistoricoNotificacoes  # Modelos de notificações

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # Ajusta cabecalhos de proxy (Render) para preservar HTTPS
    app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

    # Inicializa extensões
    db.init_app(app)
    login_manager.init_app(app)

    # Configurações do login
    login_manager.login_view = "usuario.login"
    login_manager.login_message = "Por favor, faça login para acessar esta página."
    login_manager.login_message_category = "info"
    login_manager.session_protection = "basic"  # Proteção básica de sessão (menos restritiva que "strong")
    login_manager.refresh_view = "usuario.login"

    # Debug: Log de cookies e sessão
    @app.after_request
    def log_cookies_and_session(response):
        try:
            from flask import session
            import sys
            # Log apenas se houver user_id na sessão (usuário logado)
            if '_user_id' in session:
                cookies = response.headers.getlist('Set-Cookie')
                if cookies:
                    print(f"COOKIES_SET: {len(cookies)} cookies", flush=True)
                    for cookie in cookies:
                        # Não logar o valor completo do cookie por segurança
                        cookie_name = cookie.split('=')[0]
                        print(f"  - {cookie_name}", flush=True)
                sys.stdout.flush()
        except:
            pass
        return response

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
    app.register_blueprint(notificacoes_bp)

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
    
    @app.template_filter('data_por_extenso')
    def data_por_extenso(data):
        """Formata data por extenso em português (ex: 22 de Janeiro de 2026)"""
        if not data:
            return ''
        
        meses = {
            1: 'janeiro', 2: 'fevereiro', 3: 'março', 4: 'abril',
            5: 'maio', 6: 'junho', 7: 'julho', 8: 'agosto',
            9: 'setembro', 10: 'outubro', 11: 'novembro', 12: 'dezembro'
        }
        
        try:
            dia = data.day
            mes = meses.get(data.month, '')
            ano = data.year
            return f'{dia} de {mes} de {ano}'
        except:
            return str(data)

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
            # Forçar refresh da sessão para obter dados mais recentes
            if config:
                db.session.refresh(config)
            return dict(igreja_config=config)
        except Exception as e:
            app.logger.warning(f'Erro ao carregar configurações para template: {str(e)}')
            return dict(igreja_config=None)

    # Cria as tabelas no primeiro uso (pode depois mover isso pro script separado)
    with app.app_context():
        try:
            db.create_all()
        except Exception as e:
            app.logger.warning(f"⚠️  Erro ao criar tabelas: {str(e)}")
        
        # Verificar e adicionar coluna se falte (simples, sem quebrar inicialização)
        try:
            from sqlalchemy import inspect, text
            inspector = inspect(db.engine)
            
            if 'configuracao_notificacoes' in inspector.get_table_names():
                colunas = {col['name'] for col in inspector.get_columns('configuracao_notificacoes')}
                if 'hora_notificacao_automatica' not in colunas:
                    try:
                        db.session.execute(text("ALTER TABLE configuracao_notificacoes ADD COLUMN hora_notificacao_automatica VARCHAR(5) DEFAULT '08:00'"))
                        db.session.commit()
                    except:
                        db.session.rollback()
        except Exception as e:
            pass  # Silenciosamente ignora erros de schema
        
        # Iniciar scheduler de tarefas agendadas
        try:
            from app.notificacoes.tarefas_agendadas import iniciar_scheduler
            iniciar_scheduler(app)
        except Exception as e:
            app.logger.warning(f"⚠️  Erro ao iniciar scheduler: {str(e)}")
        
        # DEBUG: Listar usuários e permissões (apenas em produção com DATABASE_URL)
        if app.config.get('SQLALCHEMY_DATABASE_URI', '').startswith('postgresql'):
            try:
                from app.usuario.usuario_model import Usuario
                import sys
                usuarios = Usuario.query.all()
                print("\n" + "="*70, flush=True)
                print("DEBUG: USUARIOS E PERMISSOES NO BANCO:", flush=True)
                print("="*70, flush=True)
                for u in usuarios:
                    pode_gerenciar = u.pode_gerenciar_usuarios()
                    print(f"ID={u.id} | Email={u.email} | Nivel='{u.nivel_acesso}' | PodeGerenciar={pode_gerenciar}", flush=True)
                print("="*70 + "\n", flush=True)
                sys.stdout.flush()
            except Exception as e:
                print(f"DEBUG: Erro ao listar usuarios: {str(e)}", flush=True)

    return app

