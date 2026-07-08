from datetime import datetime

from app.extensoes import db


class ObservacaoRelatorio(db.Model):
    """Armazena observações informativas por competência de relatório."""
    __tablename__ = 'observacoes_relatorio'

    id = db.Column(db.Integer, primary_key=True)
    mes = db.Column(db.Integer, nullable=False, index=True)
    ano = db.Column(db.Integer, nullable=False, index=True)
    tipo_relatorio = db.Column(db.String(40), nullable=False, default='repasses_sede', index=True)
    observacao = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        db.UniqueConstraint('mes', 'ano', 'tipo_relatorio', name='uq_observacoes_relatorio_mes_ano_tipo'),
    )

    @classmethod
    def obter(cls, mes, ano, tipo_relatorio='repasses_sede'):
        return cls.query.filter_by(mes=mes, ano=ano, tipo_relatorio=tipo_relatorio).first()

    @classmethod
    def obter_texto(cls, mes, ano, tipo_relatorio='repasses_sede'):
        registro = cls.obter(mes, ano, tipo_relatorio)
        return registro.observacao if registro else None

    @classmethod
    def salvar_texto(cls, mes, ano, observacao, tipo_relatorio='repasses_sede'):
        registro = cls.obter(mes, ano, tipo_relatorio)
        texto = (observacao or '').strip()

        if registro is None:
            registro = cls(
                mes=mes,
                ano=ano,
                tipo_relatorio=tipo_relatorio,
                observacao=texto,
            )
            db.session.add(registro)
        else:
            registro.observacao = texto

        return registro

    @classmethod
    def excluir_texto(cls, mes, ano, tipo_relatorio='repasses_sede'):
        registro = cls.obter(mes, ano, tipo_relatorio)
        if registro:
            db.session.delete(registro)
            return True
        return False
