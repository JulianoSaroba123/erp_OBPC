"""
Modelo de Agenda Pastoral
Cada pastor tem sua agenda privada com atividades diárias
"""

from app.extensoes import db
from datetime import datetime

class AgendaPastoral(db.Model):
    __tablename__ = 'agenda_pastoral'
    
    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)  # Dono da agenda
    titulo = db.Column(db.String(200), nullable=False)
    descricao = db.Column(db.Text)
    data = db.Column(db.Date, nullable=False)
    hora_inicio = db.Column(db.Time)
    hora_fim = db.Column(db.Time)
    local = db.Column(db.String(200))
    tipo_atividade = db.Column(db.String(50))  # Visita, Reunião, Estudo, Aconselhamento, Culto, Administrativo, Outros
    prioridade = db.Column(db.String(20), default='Normal')  # Baixa, Normal, Alta, Urgente
    status = db.Column(db.String(20), default='Pendente')  # Pendente, Em Andamento, Concluída, Cancelada
    observacoes = db.Column(db.Text)
    concluida = db.Column(db.Boolean, default=False)
    data_conclusao = db.Column(db.DateTime)
    data_cadastro = db.Column(db.DateTime, default=datetime.utcnow)
    data_atualizacao = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relacionamento
    usuario = db.relationship('Usuario', backref='agenda_pastoral')
    
    def __repr__(self):
        return f'<AgendaPastoral {self.titulo} - {self.data}>'
    
    def to_dict(self):
        """Converte o objeto para dicionário"""
        return {
            'id': self.id,
            'usuario_id': self.usuario_id,
            'titulo': self.titulo,
            'descricao': self.descricao,
            'data': self.data.strftime('%Y-%m-%d') if self.data else None,
            'hora_inicio': self.hora_inicio.strftime('%H:%M') if self.hora_inicio else None,
            'hora_fim': self.hora_fim.strftime('%H:%M') if self.hora_fim else None,
            'local': self.local,
            'tipo_atividade': self.tipo_atividade,
            'prioridade': self.prioridade,
            'status': self.status,
            'observacoes': self.observacoes,
            'concluida': self.concluida,
            'data_conclusao': self.data_conclusao.strftime('%Y-%m-%d %H:%M') if self.data_conclusao else None,
            'data_cadastro': self.data_cadastro.strftime('%Y-%m-%d %H:%M') if self.data_cadastro else None
        }
