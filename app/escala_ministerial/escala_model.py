from app.extensoes import db
from datetime import datetime

class EscalaMinisterial(db.Model):
    """Modelo para Agenda Pastoral"""
    __tablename__ = "escala_ministerial"

    id = db.Column(db.Integer, primary_key=True)
    evento_id = db.Column(db.Integer, db.ForeignKey("agenda_semanal.id"))  # Vinculado à agenda semanal
    data_evento = db.Column(db.Date, nullable=False)
    pregador = db.Column(db.String(120))
    dirigente = db.Column(db.String(120))
    louvor = db.Column(db.String(120))
    intercessor = db.Column(db.String(120))
    diaconia = db.Column(db.String(120))
    observacoes = db.Column(db.Text)
    ativo = db.Column(db.Boolean, default=True)
    criado_em = db.Column(db.DateTime, default=datetime.utcnow)
    atualizado_em = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relacionamento com agenda semanal (mídia)
    evento = db.relationship("AgendaSemanal", backref="escala_ministerial", lazy=True)

    def __repr__(self):
        return f'<EscalaMinisterial {self.data_evento} - {self.pregador}>'

    def to_dict(self):
        """Converte o objeto para dicionário"""
        return {
            'id': self.id,
            'evento_id': self.evento_id,
            'data_evento': self.data_evento.strftime('%Y-%m-%d') if self.data_evento else None,
            'pregador': self.pregador,
            'dirigente': self.dirigente,
            'louvor': self.louvor,
            'intercessor': self.intercessor,
            'diaconia': self.diaconia,
            'observacoes': self.observacoes,
            'ativo': self.ativo,
            'criado_em': self.criado_em.strftime('%Y-%m-%d %H:%M:%S') if self.criado_em else None,
            'evento_titulo': self.evento.titulo if self.evento else None
        }

    @property
    def data_formatada(self):
        """Retorna a data formatada em português"""
        if self.data_evento:
            return self.data_evento.strftime('%d/%m/%Y')
        return ""

    @property
    def dia_semana(self):
        """Retorna o dia da semana em português"""
        if self.data_evento:
            dias = ['Segunda', 'Terça', 'Quarta', 'Quinta', 'Sexta', 'Sábado', 'Domingo']
            return dias[self.data_evento.weekday()]
        return ""

    @property
    def evento_titulo_resumido(self):
        """Retorna título do evento resumido"""
        if self.evento and self.evento.titulo:
            return self.evento.titulo[:50] + '...' if len(self.evento.titulo) > 50 else self.evento.titulo
        return "Evento não vinculado"

    @property
    def status_completo(self):
        """Verifica se a escala está completa (todos os campos preenchidos)"""
        campos_obrigatorios = [self.pregador, self.dirigente, self.louvor]
        return all(campo and campo.strip() for campo in campos_obrigatorios)

    @property
    def badge_status(self):
        """Retorna badge HTML para status"""
        if self.status_completo:
            return '<span class="badge bg-success"><i class="fas fa-check me-1"></i>Completa</span>'
        else:
            return '<span class="badge bg-warning"><i class="fas fa-exclamation me-1"></i>Incompleta</span>'
