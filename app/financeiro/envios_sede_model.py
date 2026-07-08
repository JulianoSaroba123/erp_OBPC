from app.extensoes import db
from datetime import datetime, date
from sqlalchemy import extract, func


class EnvioSede(db.Model):
    """Registra pagamentos efetivos de repasse a sede por competencia."""
    __tablename__ = 'envios_sede'

    id = db.Column(db.Integer, primary_key=True)
    data_pagamento = db.Column(db.Date, nullable=False, index=True)
    valor = db.Column(db.Float, nullable=False)
    forma_pagamento = db.Column(db.String(50), nullable=False, default='PIX')
    competencia = db.Column(db.String(150), nullable=False)
    competencia_mes_ref = db.Column(db.Integer, nullable=True)
    competencia_ano_ref = db.Column(db.Integer, nullable=True)
    lancamento_financeiro_id = db.Column(db.Integer, db.ForeignKey('lancamentos.id'), nullable=True, unique=True, index=True)
    comprovante = db.Column(db.String(300), nullable=True)
    observacao = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    lancamento_financeiro = db.relationship('Lancamento', foreign_keys=[lancamento_financeiro_id], uselist=False)

    def to_dict(self):
        return {
            'id': self.id,
            'data_pagamento': self.data_pagamento.strftime('%Y-%m-%d') if self.data_pagamento else None,
            'valor': float(self.valor or 0),
            'forma_pagamento': self.forma_pagamento,
            'competencia': self.competencia,
            'competencia_mes_ref': self.competencia_mes_ref,
            'competencia_ano_ref': self.competencia_ano_ref,
            'lancamento_financeiro_id': self.lancamento_financeiro_id,
            'comprovante': self.comprovante,
            'observacao': self.observacao,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None,
            'updated_at': self.updated_at.strftime('%Y-%m-%d %H:%M:%S') if self.updated_at else None,
        }

    @classmethod
    def somar_pagamentos_mes(cls, mes, ano):
        return db.session.query(func.sum(cls.valor)).filter(
            extract('month', cls.data_pagamento) == mes,
            extract('year', cls.data_pagamento) == ano
        ).scalar() or 0.0

    @classmethod
    def somar_pagamentos_antes_do_mes(cls, mes, ano):
        data_inicio = date(ano, mes, 1)
        return db.session.query(func.sum(cls.valor)).filter(
            cls.data_pagamento < data_inicio
        ).scalar() or 0.0

    @classmethod
    def listar_pagamentos_mes(cls, mes, ano):
        return cls.query.filter(
            extract('month', cls.data_pagamento) == mes,
            extract('year', cls.data_pagamento) == ano
        ).order_by(cls.data_pagamento.asc(), cls.id.asc()).all()
