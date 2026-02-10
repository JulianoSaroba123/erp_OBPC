"""
Sistema de tarefas agendadas para notificações automáticas
"""
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

# Instância global do scheduler
scheduler = None


def iniciar_scheduler(app):
    """Inicia o scheduler de tarefas agendadas"""
    global scheduler
    
    if scheduler is not None:
        return
    
    try:
        scheduler = BackgroundScheduler()
        
        # Adicionar tarefa de verificação de aniversariantes
        # Executa diariamente às 08:00 da manhã
        scheduler.add_job(
            func=verificar_e_notificar_aniversariantes,
            trigger=CronTrigger(hour=8, minute=0),
            id='verificar_aniversariantes',
            name='Verificar e notificar aniversariantes',
            replace_existing=True,
            args=[app]
        )
        
        scheduler.start()
        logger.info("✅ Scheduler iniciado - Notificações de aniversariantes agendadas para 08:00 diariamente")
    
    except Exception as e:
        logger.error(f"❌ Erro ao iniciar scheduler: {str(e)}")


def parar_scheduler():
    """Para o scheduler"""
    global scheduler
    
    if scheduler is not None:
        try:
            scheduler.shutdown()
            scheduler = None
            logger.info("Scheduler parado")
        except Exception as e:
            logger.error(f"Erro ao parar scheduler: {str(e)}")


def verificar_e_notificar_aniversariantes(app):
    """Verifica e notifica sobre aniversariantes do dia"""
    try:
        with app.app_context():
            from app.membros.membros_model import Membro
            from app.notificacoes.notificacoes_service import ServicoNotificacoes
            from sqlalchemy import extract
            from datetime import date
            
            hoje = date.today()
            mes_atual = hoje.month
            dia_atual = hoje.day
            
            # Buscar aniversariantes de hoje
            aniversariantes_hoje = Membro.query.filter(
                extract('month', Membro.data_nascimento) == mes_atual,
                extract('day', Membro.data_nascimento) == dia_atual,
                Membro.status == 'Ativo'
            ).all()
            
            if not aniversariantes_hoje:
                logger.info(f"[{hoje}] Nenhum aniversariante hoje")
                return
            
            logger.info(f"[{hoje}] {len(aniversariantes_hoje)} aniversariante(s) encontrado(s) hoje")
            
            config = ServicoNotificacoes.obter_configuracao()
            
            if not config.notificar_admin:
                logger.info("Notificação de admin desabilitada")
                return
            
            if not config.email_admin and not config.whatsapp_habilitado:
                logger.warning("Nenhum canal de notificação configurado para admin")
                return
            
            # Preparar lista de aniversariantes
            lista_aniversariantes = []
            for membro in aniversariantes_hoje:
                if membro.data_nascimento:
                    idade = hoje.year - membro.data_nascimento.year
                    lista_aniversariantes.append({
                        'nome': membro.nome,
                        'idade': idade,
                        'email': membro.email,
                        'telefone': membro.telefone
                    })
            
            # ========== Notificar via Email ==========
            if config.email_habilitado and config.email_admin:
                try:
                    corpo_html = _gerar_email_aniversariantes(lista_aniversariantes, hoje)
                    
                    resultado = ServicoNotificacoes.enviar_email(
                        destinatario=config.email_admin,
                        assunto=f'📢 {len(lista_aniversariantes)} Aniversariante(s) Hoje - {hoje.strftime("%d/%m/%Y")}',
                        corpo_html=corpo_html
                    )
                    
                    if resultado['sucesso']:
                        logger.info(f"✅ Email de aniversariantes enviado para {config.email_admin}")
                    else:
                        logger.error(f"❌ Erro ao enviar email: {resultado['mensagem']}")
                
                except Exception as e:
                    logger.error(f"❌ Erro ao enviar email de aniversariantes: {str(e)}")
            
            # ========== Notificar via WhatsApp ==========
            if config.whatsapp_habilitado and config.whatsapp_numero:
                try:
                    mensagem = _gerar_whatsapp_aniversariantes(lista_aniversariantes, hoje)
                    
                    resultado = ServicoNotificacoes.enviar_whatsapp(
                        numero=config.whatsapp_numero,
                        mensagem=mensagem
                    )
                    
                    if resultado['sucesso']:
                        logger.info(f"✅ WhatsApp de aniversariantes enviado para {config.whatsapp_numero}")
                    else:
                        logger.error(f"❌ Erro ao enviar WhatsApp: {resultado['mensagem']}")
                
                except Exception as e:
                    logger.error(f"❌ Erro ao enviar WhatsApp de aniversariantes: {str(e)}")
        
    except Exception as e:
        logger.error(f"❌ Erro na verificação de aniversariantes: {str(e)}")
        import traceback
        traceback.print_exc()


def _gerar_email_aniversariantes(lista, data):
    """Gera HTML do email de aniversariantes"""
    linhas_html = ""
    
    for aniver in lista:
        linhas_html += f"""
        <tr style="border-bottom: 1px solid #e0e6ed;">
            <td style="padding: 12px; color: #374151;">
                <strong>🎂 {aniver['nome']}</strong>
            </td>
            <td style="padding: 12px; color: #6b7280;">
                {aniver['idade']} anos
            </td>
            <td style="padding: 12px; color: #6b7280;">
                {aniver['email'] or 'N/A'}
            </td>
            <td style="padding: 12px; color: #6b7280;">
                {aniver['telefone'] or 'N/A'}
            </td>
        </tr>
        """
    
    return f"""
    <html>
        <body style="font-family: Arial, sans-serif; background: #f9fafb; padding: 20px;">
            <div style="max-width: 600px; margin: 0 auto; background: white; border-radius: 15px; overflow: hidden; box-shadow: 0 2px 10px rgba(0,0,0,0.1);">
                
                <!-- Header -->
                <div style="background: linear-gradient(135deg, #eab308, #fbbf24); padding: 30px; text-align: center;">
                    <h2 style="margin: 0; color: #000; font-size: 24px;">🎉 Aniversariantes de Hoje!</h2>
                    <p style="margin: 10px 0 0 0; color: #000; font-size: 16px; opacity: 0.8;">
                        {data.strftime('%d de %B de %Y')}
                    </p>
                </div>
                
                <!-- Conteúdo -->
                <div style="padding: 30px;">
                    <p style="color: #374151; margin-bottom: 20px;">
                        Olá administrador,<br><br>
                        Você tem <strong>{len(lista)} aniversariante(s)</strong> para comemorar hoje!
                    </p>
                    
                    <table style="width: 100%; border-collapse: collapse;">
                        <thead>
                            <tr style="background: #f3f4f6; border-bottom: 2px solid #e0e6ed;">
                                <th style="padding: 12px; text-align: left; color: #374151; font-weight: bold;">Nome</th>
                                <th style="padding: 12px; text-align: left; color: #374151; font-weight: bold;">Idade</th>
                                <th style="padding: 12px; text-align: left; color: #374151; font-weight: bold;">Email</th>
                                <th style="padding: 12px; text-align: left; color: #374151; font-weight: bold;">Telefone</th>
                            </tr>
                        </thead>
                        <tbody>
                            {linhas_html}
                        </tbody>
                    </table>
                    
                    <div style="margin-top: 30px; padding-top: 20px; border-top: 1px solid #e0e6ed;">
                        <p style="color: #6b7280; font-size: 14px;">
                            ⭐ <strong>Sugestão:</strong> Entre em contato com estos membros para enviar suas felicitações e demonstrar o cuidado da comunidade!
                        </p>
                    </div>
                </div>
                
                <!-- Footer -->
                <div style="background: #f9fafb; padding: 20px; text-align: center; border-top: 1px solid #e0e6ed;">
                    <p style="margin: 0; color: #9ca3af; font-size: 12px;">
                        Este é um email automático do Sistema OBPC.<br>
                        Enviado em {datetime.now().strftime('%d/%m/%Y às %H:%M')}
                    </p>
                </div>
            </div>
        </body>
    </html>
    """


def _gerar_whatsapp_aniversariantes(lista, data):
    """Gera mensagem WhatsApp de aniversariantes"""
    texto = f"""🎉 ANIVERSARIANTES DE HOJE - {data.strftime('%d/%m/%Y')}

"""
    
    for i, aniver in enumerate(lista, 1):
        texto += f"""{i}. {aniver['nome']} - {aniver['idade']} anos
"""
    
    texto += f"""
⭐ Não esqueça de enviar suas felicitações!

Que o Senhor abençoe a vida de nossos queridos membros! 🙏"""
    
    return texto
