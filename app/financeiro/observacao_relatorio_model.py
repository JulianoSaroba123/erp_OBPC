from datetime import datetime
import logging

from app.extensoes import db
from sqlalchemy import inspect
from sqlalchemy.exc import OperationalError, ProgrammingError


class ObservacaoRelatorio(db.Model):
    """Armazena observações informativas por competência de relatório."""
    __tablename__ = 'observacoes_relatorio'

    _tabela_verificada = False

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
    def garantir_tabela(cls):
        """Garante que a tabela exista antes de consultar/salvar observações."""
        if cls._tabela_verificada:
            return True

        try:
            inspector = inspect(db.engine)
            if cls.__tablename__ not in inspector.get_table_names():
                cls.__table__.create(bind=db.engine, checkfirst=True)
                logging.getLogger(__name__).info('Tabela observacoes_relatorio criada automaticamente.')
            cls._tabela_verificada = True
            return True
        except Exception as exc:
            logging.getLogger(__name__).warning(
                'ObservacaoRelatorio indisponivel; usando fallback automatico. Motivo: %s',
                exc,
            )
            return False

    @classmethod
    def _executar_consulta_segura(cls, operacao):
        if not cls.garantir_tabela():
            return None

        try:
            return operacao()
        except (OperationalError, ProgrammingError) as exc:
            cls._tabela_verificada = False
            logging.getLogger(__name__).warning(
                'Falha ao acessar observacoes_relatorio; usando fallback automatico. Motivo: %s',
                exc,
            )
            return None

    @classmethod
    def obter(cls, mes, ano, tipo_relatorio='repasses_sede'):
        return cls._executar_consulta_segura(
            lambda: cls.query.filter_by(mes=mes, ano=ano, tipo_relatorio=tipo_relatorio).first()
        )

    @classmethod
    def obter_texto(cls, mes, ano, tipo_relatorio='repasses_sede'):
        registro = cls.obter(mes, ano, tipo_relatorio)
        return registro.observacao if registro else None

    @classmethod
    def salvar_texto(cls, mes, ano, observacao, tipo_relatorio='repasses_sede'):
        if not cls.garantir_tabela():
            return None

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
