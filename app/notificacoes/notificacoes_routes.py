from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required
from functools import wraps
from app.extensoes import db
from app.notificacoes.notificacoes_model import ConfiguracaoNotificacoes, HistoricoNotificacoes
from app.notificacoes.notificacoes_service import ServicoNotificacoes

notificacoes_bp = Blueprint('notificacoes', __name__, template_folder='templates')


def requer_admin(f):
    """Decorator para verificar se é admin"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        from flask_login import current_user
        # Aqui você pode adicionar lógica para verificar permissões
        # Por enquanto, apenas verifica se está logado
        if not current_user.is_authenticated:
            return redirect(url_for('usuario.login'))
        return f(*args, **kwargs)
    return decorated_function


@notificacoes_bp.route('/notificacoes/configuracoes', methods=['GET', 'POST'])
@login_required
@requer_admin
def configurar_notificacoes():
    """Página de configuração de notificações"""
    try:
        config = ServicoNotificacoes.obter_configuracao()
        
        if request.method == 'POST':
            # Atualizar configurações de email
            config.email_habilitado = request.form.get('email_habilitado') == 'on'
            config.email_remetente = request.form.get('email_remetente', '').strip()
            config.email_admin = request.form.get('email_admin', '').strip()
            config.smtp_server = request.form.get('smtp_server', '').strip()
            
            try:
                config.smtp_porta = int(request.form.get('smtp_porta', 587))
            except:
                config.smtp_porta = 587
            
            config.smtp_usuario = request.form.get('smtp_usuario', '').strip()
            
            if request.form.get('smtp_senha'):
                config.smtp_senha = request.form.get('smtp_senha')
            
            # Atualizar configurações de WhatsApp
            config.whatsapp_habilitado = request.form.get('whatsapp_habilitado') == 'on'
            config.whatsapp_provider = request.form.get('whatsapp_provider', 'twilio')
            config.whatsapp_account_sid = request.form.get('whatsapp_account_sid', '').strip()
            
            if request.form.get('whatsapp_auth_token'):
                config.whatsapp_auth_token = request.form.get('whatsapp_auth_token')
            
            config.whatsapp_numero = request.form.get('whatsapp_numero', '').strip()
            
            if request.form.get('whatsapp_api_key'):
                config.whatsapp_api_key = request.form.get('whatsapp_api_key')
            
            config.whatsapp_api_url = request.form.get('whatsapp_api_url', '').strip()
            
            # Configurações gerais
            config.notificar_aniversariantes = request.form.get('notificar_aniversariantes') == 'on'
            config.notificar_admin = request.form.get('notificar_admin') == 'on'
            
            try:
                config.dias_antes = int(request.form.get('dias_antes', 1))
            except:
                config.dias_antes = 1
            
            # Nova: hora de notificação automática
            try:
                config.hora_notificacao_automatica = request.form.get('hora_notificacao_automatica', '08:00')
            except:
                config.hora_notificacao_automatica = '08:00'
            
            db.session.commit()
            flash('Configurações salvas com sucesso!', 'success')
            return redirect(url_for('notificacoes.configurar_notificacoes'))
        
        return render_template('notificacoes/configurar_notificacoes.html', config=config)
    
    except Exception as e:
        flash(f'Erro ao carregar configurações: {str(e)}', 'danger')
        return render_template('notificacoes/configurar_notificacoes.html', config=None)


@notificacoes_bp.route('/notificacoes/testar-email', methods=['POST'])
@login_required
@requer_admin
def testar_email():
    """Testa envio de email"""
    try:
        email_teste = request.form.get('email_teste', '').strip()
        
        if not email_teste:
            return jsonify({
                'sucesso': False,
                'mensagem': 'Email de teste não informado'
            }), 400
        
        corpo_html = """
        <html>
            <body style="font-family: Arial, sans-serif;">
                <div style="background: linear-gradient(135deg, #228b22, #0d5450); color: white; padding: 20px; border-radius: 10px;">
                    <h2>🧪 Teste de Email - Sistema OBPC</h2>
                    <p>Este é um email de teste para verificar se a configuração de notificações está funcionando corretamente.</p>
                    <p><strong>Data:</strong> 10/02/2026</p>
                    <p style="margin-top: 30px; font-size: 12px; opacity: 0.8;">
                        Este é um email automático. Não responda.
                    </p>
                </div>
            </body>
        </html>
        """
        
        resultado = ServicoNotificacoes.enviar_email(
            destinatario=email_teste,
            assunto='🧪 Teste de Email - Sistema OBPC',
            corpo_html=corpo_html
        )
        
        if resultado['sucesso']:
            return jsonify({
                'sucesso': True,
                'mensagem': f'Email de teste enviado para {email_teste}'
            })
        else:
            return jsonify({
                'sucesso': False,
                'mensagem': resultado['mensagem']
            }), 400
    
    except Exception as e:
        return jsonify({
            'sucesso': False,
            'mensagem': f'Erro ao testar email: {str(e)}'
        }), 500


@notificacoes_bp.route('/notificacoes/testar-whatsapp', methods=['POST'])
@login_required
@requer_admin
def testar_whatsapp():
    """Testa envio de WhatsApp"""
    try:
        numero_teste = request.form.get('numero_teste', '').strip()
        
        if not numero_teste:
            return jsonify({
                'sucesso': False,
                'mensagem': 'Número de WhatsApp não informado'
            }), 400
        
        mensagem = "🧪 Teste de WhatsApp - Sistema OBPC\n\nEste é um teste para verificar se a configuração de notificações está funcionando corretamente."
        
        resultado = ServicoNotificacoes.enviar_whatsapp(
            numero=numero_teste,
            mensagem=mensagem
        )
        
        if resultado['sucesso']:
            return jsonify({
                'sucesso': True,
                'mensagem': f'WhatsApp de teste enviado para {numero_teste}'
            })
        else:
            return jsonify({
                'sucesso': False,
                'mensagem': resultado['mensagem']
            }), 400
    
    except Exception as e:
        return jsonify({
            'sucesso': False,
            'mensagem': f'Erro ao testar WhatsApp: {str(e)}'
        }), 500


@notificacoes_bp.route('/notificacoes/historico')
@login_required
@requer_admin
def historico_notificacoes():
    """Visualiza histórico de notificações enviadas"""
    try:
        filtro_tipo = request.args.get('tipo', '').strip()
        filtro_status = request.args.get('status', '').strip()
        
        historico = ServicoNotificacoes.obter_historico(
            filtro_tipo=filtro_tipo if filtro_tipo else None,
            filtro_status=filtro_status if filtro_status else None,
            limite=500
        )
        
        return render_template(
            'notificacoes/historico_notificacoes.html',
            historico=historico,
            filtro_tipo=filtro_tipo,
            filtro_status=filtro_status
        )
    
    except Exception as e:
        flash(f'Erro ao carregar histórico: {str(e)}', 'danger')
        return render_template('notificacoes/historico_notificacoes.html', historico=[])
