from app.extensoes import db
from datetime import datetime, date
from sqlalchemy import extract, func, and_, or_


class EnvioSede(db.Model):
    """Registra pagamentos efetivos de repasse a sede por competencia."""
    __tablename__ = 'envios_sede'

    id = db.Column(db.Integer, primary_key=True)
    data_pagamento = db.Column(db.Date, nullable=False, index=True)
    valor = db.Column(db.Float, nullable=False)
    valor_administrativo = db.Column(db.Float, nullable=True)
    valor_despesas_fixas = db.Column(db.Float, nullable=True)
    valor_total = db.Column(db.Float, nullable=True)
    forma_pagamento = db.Column(db.String(50), nullable=False, default='PIX')
    competencia = db.Column(db.String(150), nullable=False)
    competencia_mes_ref = db.Column(db.Integer, nullable=True)
    competencia_ano_ref = db.Column(db.Integer, nullable=True)
    competencia_mes = db.Column(db.Integer, nullable=True)
    competencia_ano = db.Column(db.Integer, nullable=True)
    tipo_pagamento = db.Column(db.String(50), nullable=True)
    lancamento_financeiro_id = db.Column(db.Integer, db.ForeignKey('lancamentos.id'), nullable=True, unique=True, index=True)
    comprovante = db.Column(db.String(300), nullable=True)
    observacao = db.Column(db.Text, nullable=True)
    valor_devido_competencia = db.Column(db.Float, nullable=True)
    pagamento_historico_sem_movimentacao = db.Column(db.Boolean, nullable=False, default=False)
    data_pagamento_informada = db.Column(db.Boolean, nullable=False, default=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    lancamento_financeiro = db.relationship('Lancamento', foreign_keys=[lancamento_financeiro_id], uselist=False)

    def to_dict(self):
        competencia_mes = self.competencia_mes if self.competencia_mes is not None else self.competencia_mes_ref
        competencia_ano = self.competencia_ano if self.competencia_ano is not None else self.competencia_ano_ref
        valor_total = self.valor_total if self.valor_total is not None else self.valor
        return {
            'id': self.id,
            'data_pagamento': self.data_pagamento.strftime('%Y-%m-%d') if self.data_pagamento else None,
            'valor': float(self.valor or 0),
            'valor_administrativo': float(self.valor_administrativo or 0),
            'valor_despesas_fixas': float(self.valor_despesas_fixas or 0),
            'valor_total': float(valor_total or 0),
            'forma_pagamento': self.forma_pagamento,
            'competencia': self.competencia,
            'competencia_mes': competencia_mes,
            'competencia_ano': competencia_ano,
            'competencia_mes_ref': competencia_mes,
            'competencia_ano_ref': competencia_ano,
            'tipo_pagamento': self.tipo_pagamento,
            'lancamento_financeiro_id': self.lancamento_financeiro_id,
            'comprovante': self.comprovante,
            'observacao': self.observacao,
            'valor_devido_competencia': float(self.valor_devido_competencia or 0) if self.valor_devido_competencia is not None else None,
            'pagamento_historico_sem_movimentacao': bool(self.pagamento_historico_sem_movimentacao),
            'data_pagamento_informada': bool(self.data_pagamento_informada),
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None,
            'updated_at': self.updated_at.strftime('%Y-%m-%d %H:%M:%S') if self.updated_at else None,
        }

    @classmethod
    def somar_pagamentos_mes(cls, mes, ano):
        return db.session.query(func.sum(func.coalesce(cls.valor_total, cls.valor))).filter(
            extract('month', cls.data_pagamento) == mes,
            extract('year', cls.data_pagamento) == ano
        ).scalar() or 0.0

    @classmethod
    def somar_pagamentos_antes_do_mes(cls, mes, ano):
        data_inicio = date(ano, mes, 1)
        return db.session.query(func.sum(func.coalesce(cls.valor_total, cls.valor))).filter(
            cls.data_pagamento < data_inicio
        ).scalar() or 0.0

    @classmethod
    def listar_pagamentos_mes(cls, mes, ano):
        return cls.query.filter(
            extract('month', cls.data_pagamento) == mes,
            extract('year', cls.data_pagamento) == ano
        ).order_by(cls.data_pagamento.asc(), cls.id.asc()).all()

    @staticmethod
    def _competencia_ordem(mes, ano):
        return (ano * 100) + mes

    @classmethod
    def _ordem_competencia_registro(cls, pagamento):
        comp_mes = pagamento.competencia_mes if pagamento.competencia_mes is not None else pagamento.competencia_mes_ref
        comp_ano = pagamento.competencia_ano if pagamento.competencia_ano is not None else pagamento.competencia_ano_ref

        if comp_ano is not None and comp_mes is not None:
            return cls._competencia_ordem(int(comp_mes), int(comp_ano))

        if pagamento.data_pagamento:
            return cls._competencia_ordem(pagamento.data_pagamento.month, pagamento.data_pagamento.year)

        return None

    @classmethod
    def listar_pagamentos_por_competencia_ate(cls, mes, ano):
        limite = cls._competencia_ordem(mes, ano)
        pagamentos = []

        for pagamento in cls.query.order_by(cls.data_pagamento.asc(), cls.id.asc()).all():
            ordem = cls._ordem_competencia_registro(pagamento)
            if ordem is not None and ordem <= limite:
                pagamentos.append(pagamento)

        return pagamentos

    @classmethod
    def somar_pagamentos_por_competencia_ate(cls, mes, ano):
        return sum(float((pagamento.valor_total if pagamento.valor_total is not None else pagamento.valor) or 0) for pagamento in cls.listar_pagamentos_por_competencia_ate(mes, ano))

    @classmethod
    def somar_pagamentos_por_competencia_mes(cls, mes, ano):
        alvo = cls._competencia_ordem(mes, ano)
        total = 0.0

        for pagamento in cls.query.order_by(cls.data_pagamento.asc(), cls.id.asc()).all():
            ordem = cls._ordem_competencia_registro(pagamento)
            if ordem == alvo:
                total += float((pagamento.valor_total if pagamento.valor_total is not None else pagamento.valor) or 0)

        return total

    @staticmethod
    def _valor_administrativo_para_controle(pagamento):
        """Retorna o valor administrativo sem misturar despesas fixas no controle de repasse.

        Regras:
        - Se houver valor_administrativo explícito, usa-o.
        - Se não houver valor_administrativo, mas houver valor_despesas_fixas, deduz do total.
        - Sem separação de componentes (legado): usa o total legado (valor_total/valor).
        """
        valor_admin = getattr(pagamento, 'valor_administrativo', None)
        if valor_admin is not None:
            return float(valor_admin or 0)

        valor_total = float((getattr(pagamento, 'valor_total', None) if getattr(pagamento, 'valor_total', None) is not None else getattr(pagamento, 'valor', 0)) or 0)
        valor_fixas = getattr(pagamento, 'valor_despesas_fixas', None)

        if valor_fixas is not None:
            return max(valor_total - float(valor_fixas or 0), 0.0)

        return valor_total

    @classmethod
    def somar_pagamentos_administrativos_por_competencia_ate(cls, mes, ano):
        return sum(
            cls._valor_administrativo_para_controle(pagamento)
            for pagamento in cls.listar_pagamentos_por_competencia_ate(mes, ano)
        )

    @classmethod
    def somar_pagamentos_administrativos_por_competencia_mes(cls, mes, ano):
        alvo = cls._competencia_ordem(mes, ano)
        total = 0.0

        for pagamento in cls.query.order_by(cls.data_pagamento.asc(), cls.id.asc()).all():
            ordem = cls._ordem_competencia_registro(pagamento)
            if ordem == alvo:
                total += cls._valor_administrativo_para_controle(pagamento)

        return total
