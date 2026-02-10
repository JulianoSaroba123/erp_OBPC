"""
Serviço de notificações - Suporta Email e WhatsApp
"""
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
import logging
from app.extensoes import db
from app.notificacoes.notificacoes_model import ConfiguracaoNotificacoes, HistoricoNotificacoes

logger = logging.getLogger(__name__)


class ServicoNotificacoes:
    """Serviço centralizado de notificações"""
    
    @staticmethod
    def obter_configuracao():
        """Obtém configuração de notificações, criando padrão se necessário"""
        try:
            config = ConfiguracaoNotificacoes.query.first()
            if not config:
                try:
                    config = ConfiguracaoNotificacoes()
                    db.session.add(config)
                    db.session.commit()
                except Exception as e:
                    db.session.rollback()
                    # Se não conseguir criar no banco, retornar objeto em memória
                    config = ConfiguracaoNotificacoes()
                    config.id = 1
                    config.email_habilitado = False
                    config.whatsapp_habilitado = False
                    config.notificar_aniversariantes = True
                    config.notificar_admin = True
                    config.dias_antes = 0
                    config.hora_notificacao_automatica = '08:00'
                    logger.warning(f"Não conseguiu criar configuração no banco: {str(e)}")
            return config
        except Exception as e:
            logger.error(f"Erro ao obter configuração: {str(e)}")
            # Retornar objeto padrão em memória se falhar
            config = ConfiguracaoNotificacoes()
            config.id = 1
            config.email_habilitado = False
            config.whatsapp_habilitado = False
            config.notificar_aniversariantes = True
            config.notificar_admin = True
            config.dias_antes = 0
            config.hora_notificacao_automatica = '08:00'
            return config
    
    @staticmethod
    def enviar_email(destinatario, assunto, corpo_html, corpo_texto=None):
        """
        Envia email
        
        Args:
            destinatario: Email de destino
            assunto: Assunto do email
            corpo_html: Corpo em HTML
            corpo_texto: Corpo em texto puro (opcional)
        
        Returns:
            dict com status e mensagem
        """
        try:
            config = ServicoNotificacoes.obter_configuracao()
            
            if not config.email_habilitado:
                return {
                    'sucesso': False,
                    'mensagem': 'Email não está habilitado'
                }
            
            if not config.smtp_server or not config.smtp_usuario or not config.smtp_senha:
                return {
                    'sucesso': False,
                    'mensagem': 'Configuração de SMTP incompleta'
                }
            
            # Criar mensagem
            msg = MIMEMultipart('alternative')
            msg['Subject'] = assunto
            msg['From'] = config.email_remetente or config.smtp_usuario
            msg['To'] = destinatario
            
            # Adicionar corpo em texto
            if corpo_texto:
                msg.attach(MIMEText(corpo_texto, 'plain'))
            
            # Adicionar corpo em HTML
            msg.attach(MIMEText(corpo_html, 'html'))
            
            # Enviar email
            with smtplib.SMTP(config.smtp_server, config.smtp_porta) as server:
                server.starttls()
                server.login(config.smtp_usuario, config.smtp_senha)
                server.send_message(msg)
            
            # Registrar no histórico
            try:
                historico = HistoricoNotificacoes(
                    tipo='email',
                    destinatario=destinatario,
                    titulo=assunto,
                    mensagem=corpo_html[:500],  # Limitar tamanho
                    status='enviado',
                    erro_mensagem=None
                )
                db.session.add(historico)
                db.session.commit()
            except Exception as e_hist:
                db.session.rollback()
                logger.error(f"Erro ao registrar histórico: {str(e_hist)}")
            
            return {
                'sucesso': True,
                'mensagem': 'Email enviado com sucesso'
            }
        
        except smtplib.SMTPAuthenticationError:
            db.session.rollback()
            msg_erro = 'Erro de autenticação SMTP. Verifique usuário e senha'
            logger.error(msg_erro)
            return {
                'sucesso': False,
                'mensagem': msg_erro
            }
        
        except smtplib.SMTPException as e:
            db.session.rollback()
            msg_erro = f'Erro ao enviar email: {str(e)}'
            logger.error(msg_erro)
            
            # Tenta registrar no histórico
            try:
                historico = HistoricoNotificacoes(
                    tipo='email',
                    destinatario=destinatario,
                    titulo=assunto,
                    mensagem=corpo_html[:500],
                    status='erro',
                    erro_mensagem=msg_erro[:500]
                )
                db.session.add(historico)
                db.session.commit()
            except:
                db.session.rollback()
            
            return {
                'sucesso': False,
                'mensagem': msg_erro
            }
        
        except Exception as e:
            db.session.rollback()
            msg_erro = f'Erro desconhecido: {str(e)}'
            logger.error(msg_erro)
            return {
                'sucesso': False,
                'mensagem': msg_erro
            }
    
    @staticmethod
    def enviar_whatsapp(numero, mensagem, membro_id=None):
        """
        Envia mensagem via WhatsApp
        
        Args:
            numero: Número de WhatsApp (formato: 55XXXXXXXXXXX)
            mensagem: Corpo da mensagem
            membro_id: ID do membro (para referência)
        
        Returns:
            dict com status e mensagem
        """
        try:
            config = ServicoNotificacoes.obter_configuracao()
            
            if not config.whatsapp_habilitado:
                return {
                    'sucesso': False,
                    'mensagem': 'WhatsApp não está habilitado'
                }
            
            if config.whatsapp_provider == 'twilio':
                return ServicoNotificacoes._enviar_whatsapp_twilio(numero, mensagem, membro_id)
            
            elif config.whatsapp_provider == 'uma-msg':
                return ServicoNotificacoes._enviar_whatsapp_umamsg(numero, mensagem, membro_id)
            
            elif config.whatsapp_provider == 'gupshup':
                return ServicoNotificacoes._enviar_whatsapp_gupshup(numero, mensagem, membro_id)
            
            else:
                return {
                    'sucesso': False,
                    'mensagem': f'Provider {config.whatsapp_provider} não suportado'
                }
        
        except Exception as e:
            logger.error(f"Erro ao enviar WhatsApp: {str(e)}")
            return {
                'sucesso': False,
                'mensagem': f'Erro ao enviar WhatsApp: {str(e)}'
            }
    
    @staticmethod
    def _enviar_whatsapp_twilio(numero, mensagem, membro_id=None):
        """Envia WhatsApp via Twilio"""
        try:
            from twilio.rest import Client
            
            config = ServicoNotificacoes.obter_configuracao()
            
            client = Client(config.whatsapp_account_sid, config.whatsapp_auth_token)
            
            message = client.messages.create(
                from_=f'whatsapp:{config.whatsapp_numero}',
                body=mensagem,
                to=f'whatsapp:{numero}'
            )
            
            # Registrar no histórico
            historico = HistoricoNotificacoes(
                tipo='whatsapp',
                destinatario=numero,
                membro_id=membro_id,
                titulo='Notificação WhatsApp',
                mensagem=mensagem,
                status='enviado'
            )
            db.session.add(historico)
            db.session.commit()
            
            logger.info(f"WhatsApp enviado com sucesso para {numero}")
            return {
                'sucesso': True,
                'mensagem': 'WhatsApp enviado com sucesso',
                'message_id': message.sid
            }
        
        except Exception as e:
            logger.error(f"Erro ao enviar WhatsApp via Twilio: {str(e)}")
            
            historico = HistoricoNotificacoes(
                tipo='whatsapp',
                destinatario=numero,
                membro_id=membro_id,
                titulo='Notificação WhatsApp',
                mensagem=mensagem,
                status='erro',
                erro_mensagem=str(e)
            )
            db.session.add(historico)
            db.session.commit()
            
            return {
                'sucesso': False,
                'mensagem': f'Erro ao enviar WhatsApp via Twilio: {str(e)}'
            }
    
    @staticmethod
    def _enviar_whatsapp_umamsg(numero, mensagem, membro_id=None):
        """Envia WhatsApp via Uma-msg API"""
        try:
            import requests
            
            config = ServicoNotificacoes.obter_configuracao()
            
            headers = {
                'Authorization': f'Bearer {config.whatsapp_api_key}',
                'Content-Type': 'application/json'
            }
            
            payload = {
                'to': numero,
                'message': mensagem
            }
            
            response = requests.post(
                config.whatsapp_api_url,
                json=payload,
                headers=headers,
                timeout=10
            )
            
            if response.status_code in [200, 201]:
                # Registrar no histórico
                historico = HistoricoNotificacoes(
                    tipo='whatsapp',
                    destinatario=numero,
                    membro_id=membro_id,
                    titulo='Notificação WhatsApp',
                    mensagem=mensagem,
                    status='enviado'
                )
                db.session.add(historico)
                db.session.commit()
                
                logger.info(f"WhatsApp enviado com sucesso para {numero}")
                return {
                    'sucesso': True,
                    'mensagem': 'WhatsApp enviado com sucesso'
                }
            else:
                raise Exception(f"Erro na API: {response.text}")
        
        except Exception as e:
            logger.error(f"Erro ao enviar WhatsApp via Uma-msg: {str(e)}")
            
            historico = HistoricoNotificacoes(
                tipo='whatsapp',
                destinatario=numero,
                membro_id=membro_id,
                titulo='Notificação WhatsApp',
                mensagem=mensagem,
                status='erro',
                erro_mensagem=str(e)
            )
            db.session.add(historico)
            db.session.commit()
            
            return {
                'sucesso': False,
                'mensagem': f'Erro ao enviar WhatsApp via Uma-msg: {str(e)}'
            }
    
    @staticmethod
    def _enviar_whatsapp_gupshup(numero, mensagem, membro_id=None):
        """Envia WhatsApp via Gupshup API"""
        try:
            import requests
            
            config = ServicoNotificacoes.obter_configuracao()
            
            # Validar configuração
            if not config.whatsapp_api_key or not config.whatsapp_api_url:
                return {
                    'sucesso': False,
                    'mensagem': 'API Key ou URL do Gupshup não configurados'
                }
            
            # Headers para Gupshup - usar apiKey no formato correto
            headers = {
                'Authorization': f'apiKey {config.whatsapp_api_key}',
                'Content-Type': 'application/x-www-form-urlencoded'
            }
            
            # Garantir que o número está no formato correto (apenas dígitos + ou 55)
            numero_limpo = numero.replace('+', '').replace(' ', '').replace('-', '')
            if not numero_limpo.startswith('55'):
                numero_limpo = '55' + numero_limpo
            
            # Payload para Gupshup (usa form-data)
            payload = {
                'phone': numero_limpo,
                'message': mensagem
            }
            
            # URL pode ter ou não a barra final
            url = config.whatsapp_api_url.rstrip('/')
            
            response = requests.post(
                url,
                data=payload,
                headers=headers,
                timeout=10
            )
            
            if response.status_code in [200, 201, 202]:
                # Registrar no histórico
                historico = HistoricoNotificacoes(
                    tipo='whatsapp',
                    destinatario=numero,
                    membro_id=membro_id,
                    titulo='Notificação WhatsApp',
                    mensagem=mensagem,
                    status='enviado'
                )
                db.session.add(historico)
                db.session.commit()
                
                logger.info(f"WhatsApp enviado com sucesso para {numero} via Gupshup")
                return {
                    'sucesso': True,
                    'mensagem': 'WhatsApp enviado com sucesso'
                }
            else:
                raise Exception(f"Erro na API Gupshup: {response.status_code} - {response.text}")
        
        except Exception as e:
            logger.error(f"Erro ao enviar WhatsApp via Gupshup: {str(e)}")
            
            try:
                historico = HistoricoNotificacoes(
                    tipo='whatsapp',
                    destinatario=numero,
                    membro_id=membro_id,
                    titulo='Notificação WhatsApp',
                    mensagem=mensagem,
                    status='erro',
                    erro_mensagem=str(e)[:500]
                )
                db.session.add(historico)
                db.session.commit()
            except:
                db.session.rollback()
            
            return {
                'sucesso': False,
                'mensagem': f'Erro ao enviar WhatsApp via Gupshup: {str(e)}'
            }
    
    @staticmethod
    def obter_historico(filtro_tipo=None, filtro_status=None, limite=100):
        """Obtém histórico de notificações"""
        query = HistoricoNotificacoes.query
        
        if filtro_tipo:
            query = query.filter_by(tipo=filtro_tipo)
        
        if filtro_status:
            query = query.filter_by(status=filtro_status)
        
        return query.order_by(HistoricoNotificacoes.enviado_em.desc()).limit(limite).all()
