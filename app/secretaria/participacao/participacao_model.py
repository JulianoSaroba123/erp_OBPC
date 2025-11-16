from app.extensoes import db
from datetime import datetime

class ParticipacaoObreiro(db.Model):
    """Modelo para registrar a participação de obreiros em reuniões"""
    __tablename__ = 'participacao_obreiro'
    
    id = db.Column(db.Integer, primary_key=True)
    obreiro_id = db.Column(db.Integer, db.ForeignKey('obreiros.id'), nullable=False)
    data_reuniao = db.Column(db.Date, nullable=False)
    tipo_reuniao = db.Column(db.String(50), nullable=False)  # Sede, Superintendência, Local, Conselho
    presenca = db.Column(db.String(20), nullable=False, default='Presente')  # Presente, Ausente, Justificado
    observacao = db.Column(db.Text)
    criado_em = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relacionamento
    obreiro = db.relationship("Obreiro", backref="participacoes")
    
    def __repr__(self):
        return f'<ParticipacaoObreiro {self.obreiro.nome if self.obreiro else ""} - {self.data_reuniao}>'
    
    @staticmethod
    def get_tipos_reuniao():
        """Retorna os tipos de reunião disponíveis"""
        return ["Sede", "Superintendência", "Local", "Conselho"]
    
    @staticmethod
    def get_status_presenca():
        """Retorna os status de presença disponíveis"""
        return ["Presente", "Ausente", "Justificado"]
    
    def to_dict(self):
        """Converte o objeto para dicionário"""
        return {
            'id': self.id,
            'obreiro_id': self.obreiro_id,
            'obreiro_nome': self.obreiro.nome if self.obreiro else '',
            'data_reuniao': self.data_reuniao.strftime('%Y-%m-%d') if self.data_reuniao else '',
            'tipo_reuniao': self.tipo_reuniao,
            'presenca': self.presenca,
            'observacao': self.observacao,
            'criado_em': self.criado_em.strftime('%d/%m/%Y %H:%M') if self.criado_em else ''
        }