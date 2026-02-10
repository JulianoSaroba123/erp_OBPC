from app.extensoes import db
from datetime import datetime

class ConfiguracaoNotificacoes(db.Model):
    """Modelo para armazenar configurações de notificações"""
    __tablename__ = 'configuracao_notificacoes'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Email
    email_habilitado = db.Column(db.Boolean, default=False)
    email_remetente = db.Column(db.String(120))  # Email que envia as notificações
    smtp_server = db.Column(db.String(255))
    smtp_porta = db.Column(db.Integer, default=587)
    smtp_usuario = db.Column(db.String(255))
    smtp_senha = db.Column(db.Text)  # Criptografado idealmente
    email_admin = db.Column(db.String(120))  # Email administrativo
    
    # WhatsApp
    whatsapp_habilitado = db.Column(db.Boolean, default=False)
    whatsapp_provider = db.Column(db.String(50))  # 'twilio', 'uma-msg', 'gupshup', etc
    whatsapp_account_sid = db.Column(db.String(255))
    whatsapp_auth_token = db.Column(db.Text)
    whatsapp_numero = db.Column(db.String(20))  # Número de origem
    whatsapp_api_key = db.Column(db.Text)
    whatsapp_api_url = db.Column(db.String(500))
    
    # Configurações gerais
    notificar_aniversariantes = db.Column(db.Boolean, default=False)  # Notificar membros sobre seu próprio aniversário
    notificar_admin = db.Column(db.Boolean, default=True)  # Notificar admin sobre aniversários
    dias_antes = db.Column(db.Integer, default=1)  # Notificar quantos dias antes
    
    # Auditoria
    criado_em = db.Column(db.DateTime, default=datetime.utcnow)
    atualizado_em = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return '<ConfiguracaoNotificacoes>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'email_habilitado': self.email_habilitado,
            'email_remetente': self.email_remetente,
            'email_admin': self.email_admin,
            'whatsapp_habilitado': self.whatsapp_habilitado,
            'whatsapp_provider': self.whatsapp_provider,
            'whatsapp_numero': self.whatsapp_numero,
            'notificar_aniversariantes': self.notificar_aniversariantes,
            'notificar_admin': self.notificar_admin,
            'dias_antes': self.dias_antes,
        }


class HistoricoNotificacoes(db.Model):
    """Modelo para rastrear notificações enviadas"""
    __tablename__ = 'historico_notificacoes'
    
    id = db.Column(db.Integer, primary_key=True)
    tipo = db.Column(db.String(20))  # 'email', 'whatsapp'
    destinatario = db.Column(db.String(255))  # Email ou número WhatsApp
    membro_id = db.Column(db.Integer, nullable=True)
    titulo = db.Column(db.String(255))
    mensagem = db.Column(db.Text)
    status = db.Column(db.String(20), default='enviando')  # 'enviando', 'enviado', 'erro'
    erro_mensagem = db.Column(db.Text)  # Mensagem de erro se houver
    enviado_em = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<HistoricoNotificacoes {self.tipo} - {self.status}>'
