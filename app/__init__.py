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
from app.secretaria.dashboard_routes import secretaria_bp
from app.midia.midia_routes import midia_bp
from app.escala_ministerial.escala_routes import escala_ministerial_bp
from app.financeiro.routes_conciliacao import conciliacao_bp
from app.agenda_pastoral.agenda_pastoral_routes import agenda_pastoral_bp
from app.notificacoes.notificacoes_routes import notificacoes_bp

# Importar modelos para garantir registro no SQLAlchemy
from app.financeiro.comprovante_model import Comprovante  # Necessário para relacionamento em Lancamento
from app.financeiro.envios_sede_model import EnvioSede  # Controle de pagamentos de envio a sede
from app.financeiro.observacao_relatorio_model import ObservacaoRelatorio  # Observações informativas dos repasses
from app.notificacoes.notificacoes_model import ConfiguracaoNotificacoes, HistoricoNotificacoes  # Modelos de notificações


def _garantir_schema_envios_sede(app):
    """Evolui a tabela envios_sede sem recriá-la e sem duplicar colunas."""
    from sqlalchemy import inspect, text

    try:
        inspector = inspect(db.engine)
        if 'envios_sede' not in inspector.get_table_names():
            return

        colunas_existentes = {col['name'] for col in inspector.get_columns('envios_sede')}
        dialect = (db.engine.dialect.name or '').lower()

        def ddl_add(coluna, tipo_sql, default_sql=None):
            if dialect == 'postgresql' and default_sql is not None:
                return f'ALTER TABLE envios_sede ADD COLUMN IF NOT EXISTS {coluna} {tipo_sql} DEFAULT {default_sql}'
            if default_sql is not None:
                return f'ALTER TABLE envios_sede ADD COLUMN {coluna} {tipo_sql} DEFAULT {default_sql}'
            return f'ALTER TABLE envios_sede ADD COLUMN {coluna} {tipo_sql}'

        comandos = []
        colunas = [
            ('lancamento_financeiro_id', 'INTEGER', None),
            ('valor_devido_competencia', 'FLOAT', '0'),
            ('pagamento_historico_sem_movimentacao', 'BOOLEAN' if dialect == 'postgresql' else 'INTEGER', 'FALSE' if dialect == 'postgresql' else '0'),
            ('data_pagamento_informada', 'BOOLEAN' if dialect == 'postgresql' else 'INTEGER', 'TRUE' if dialect == 'postgresql' else '1'),
            ('valor_administrativo', 'FLOAT', '0'),
            ('valor_despesas_fixas', 'FLOAT', '0'),
            ('valor_total', 'FLOAT', '0'),
            ('competencia_mes', 'INTEGER', None),
            ('competencia_ano', 'INTEGER', None),
            ('competencia_mes_ref', 'INTEGER', None),
            ('competencia_ano_ref', 'INTEGER', None),
            ('tipo_pagamento', 'VARCHAR(50)', None),
        ]

        for nome, tipo_sql, default_sql in colunas:
            if nome not in colunas_existentes:
                comandos.append(ddl_add(nome, tipo_sql, default_sql))

        if not comandos:
            return

        app.logger.info('Evolucao de schema envios_sede: adicionando colunas faltantes: %s', ', '.join([c.split()[5] if 'ADD COLUMN IF NOT EXISTS' in c else c.split()[4] for c in comandos]))
        with db.engine.begin() as conn:
            for comando in comandos:
                conn.execute(text(comando))

        try:
            with db.engine.begin() as conn:
                conn.execute(text("UPDATE envios_sede SET valor_total = COALESCE(valor_total, valor) WHERE valor_total IS NULL"))
                conn.execute(text("UPDATE envios_sede SET valor_devido_competencia = COALESCE(valor_devido_competencia, valor_total) WHERE valor_devido_competencia IS NULL AND valor_total IS NOT NULL"))
        except Exception as backfill_error:
            app.logger.warning('Falha ao aplicar backfill seguro em envios_sede: %s', backfill_error)
    except Exception as exc:
        app.logger.warning('Falha ao garantir schema de envios_sede: %s', exc)


def _migrar_lancamentos_repasse_sede_legado(app):
    """Normaliza lançamentos antigos de 30% administrativo que ficaram em DESP. VARIÁVEIS."""
    from sqlalchemy import inspect, text

    try:
        inspector = inspect(db.engine)
        if 'lancamentos' not in inspector.get_table_names():
            return 0

        with db.engine.begin() as conn:
            result = conn.execute(text("""
                UPDATE lancamentos
                   SET categoria = 'CONTRIB. SEDE'
                 WHERE (categoria = 'DESP. VARIÁVEIS' OR categoria = 'DESP. VARIAVEIS')
                                     AND LOWER(COALESCE(descricao, '')) LIKE '30\\% administrativo - conselho sede%' ESCAPE '\\'
            """))
            return result.rowcount or 0
    except Exception as exc:
        app.logger.warning('Falha ao migrar lançamentos legados de repasse à sede: %s', exc)
        return 0

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # ProxyFix configurado corretamente para Render.com
    app.wsgi_app = ProxyFix(
        app.wsgi_app,
        x_for=1,
        x_proto=1,
        x_host=1,
        x_prefix=1
    )

    # Inicializa extensões
    db.init_app(app)
    login_manager.init_app(app)

    # Flask-Login configurações
    login_manager.login_view = "usuario.login"
    login_manager.login_message = "Por favor, faça login para acessar esta página."
    login_manager.login_message_category = "info"
    login_manager.session_protection = None  # Desabilitar para evitar conflitos com proxy
    
    # Handler crítico: Garantir sessão permanente
    @app.before_request
    def ensure_session_permanent():
        from flask import session
        if not session.permanent:
            session.permanent = True

    # Handler de erro 500 para diagnóstico em produção
    @app.errorhandler(500)
    def internal_error(error):
        import traceback
        from flask import jsonify, request as req
        tb = traceback.format_exc()
        app.logger.error(f"ERRO 500 em {req.path}:\n{tb}")
        # Se vier de /usuarios, retornar JSON com detalhes
        if '/usuarios' in req.path:
            return jsonify({
                'error': str(error),
                'path': req.path,
                'traceback': tb
            }), 500
        return f"<h1>Erro Interno</h1><pre>{tb}</pre>", 500

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
    app.register_blueprint(secretaria_bp)
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
        from datetime import datetime
        try:
            config = Configuracao.query.filter_by(id=1).first()
            return dict(igreja_config=config, current_year=datetime.now().year)
        except Exception as e:
            app.logger.warning(f'Erro ao carregar configurações para template: {str(e)}')
            return dict(igreja_config=None, current_year=datetime.now().year)

    # Cria as tabelas no primeiro uso (pode depois mover isso pro script separado)
    with app.app_context():
        try:
            tabelas_controladas_etapa_a = {
                'obrigacoes_financeiras',
                'pagamentos_obrigacao',
                'pagamentos_obrigacao_itens',
                'obrigacao_eventos',
            }
            tabelas_startup = [
                tabela
                for nome, tabela in db.metadata.tables.items()
                if nome not in tabelas_controladas_etapa_a
            ]
            db.metadata.create_all(bind=db.engine, tables=tabelas_startup)
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

        try:
            from sqlalchemy import inspect, text
            inspector = inspect(db.engine)

            if 'envios_sede' in inspector.get_table_names():
                colunas = {col['name'] for col in inspector.get_columns('envios_sede')}
                dialect = (db.engine.dialect.name or '').lower()
                comandos = []

                if 'lancamento_financeiro_id' not in colunas:
                    comandos.append('ALTER TABLE envios_sede ADD COLUMN lancamento_financeiro_id INTEGER')
                if 'valor_devido_competencia' not in colunas:
                    comandos.append('ALTER TABLE envios_sede ADD COLUMN valor_devido_competencia FLOAT')
                if 'pagamento_historico_sem_movimentacao' not in colunas:
                    if dialect == 'postgresql':
                        comandos.append('ALTER TABLE envios_sede ADD COLUMN pagamento_historico_sem_movimentacao BOOLEAN NOT NULL DEFAULT FALSE')
                    else:
                        comandos.append('ALTER TABLE envios_sede ADD COLUMN pagamento_historico_sem_movimentacao INTEGER NOT NULL DEFAULT 0')
                if 'data_pagamento_informada' not in colunas:
                    if dialect == 'postgresql':
                        comandos.append('ALTER TABLE envios_sede ADD COLUMN data_pagamento_informada BOOLEAN NOT NULL DEFAULT TRUE')
                    else:
                        comandos.append('ALTER TABLE envios_sede ADD COLUMN data_pagamento_informada INTEGER NOT NULL DEFAULT 1')
                if 'valor_administrativo' not in colunas:
                    comandos.append('ALTER TABLE envios_sede ADD COLUMN valor_administrativo FLOAT')
                if 'valor_despesas_fixas' not in colunas:
                    comandos.append('ALTER TABLE envios_sede ADD COLUMN valor_despesas_fixas FLOAT')
                if 'valor_total' not in colunas:
                    comandos.append('ALTER TABLE envios_sede ADD COLUMN valor_total FLOAT')
                if 'competencia_mes' not in colunas:
                    comandos.append('ALTER TABLE envios_sede ADD COLUMN competencia_mes INTEGER')
                if 'competencia_ano' not in colunas:
                    comandos.append('ALTER TABLE envios_sede ADD COLUMN competencia_ano INTEGER')
                if 'tipo_pagamento' not in colunas:
                    comandos.append('ALTER TABLE envios_sede ADD COLUMN tipo_pagamento VARCHAR(50)')

                if comandos:
                    for comando in comandos:
                        db.session.execute(text(comando))
                    db.session.commit()
        except Exception:
            db.session.rollback()

        try:
            _garantir_schema_envios_sede(app)
        except Exception as e:
            app.logger.warning(f'⚠️  Erro ao garantir schema de envios_sede: {str(e)}')

        try:
            migrados = _migrar_lancamentos_repasse_sede_legado(app)
            if migrados:
                app.logger.info('Migração de repasse à sede concluída: %s lançamentos atualizados para CONTRIB. SEDE', migrados)
        except Exception as e:
            app.logger.warning(f'⚠️  Erro ao migrar lançamentos legados de repasse à sede: {str(e)}')

        try:
            ObservacaoRelatorio.garantir_tabela()
        except Exception:
            pass
        
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

