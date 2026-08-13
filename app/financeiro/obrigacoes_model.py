from datetime import date, datetime
from decimal import Decimal, ROUND_HALF_UP
from sqlalchemy import func
from sqlalchemy.orm import object_session

from app.extensoes import db
from app.financeiro.financeiro_model import Lancamento


DECIMAL_ZERO = Decimal("0.00")
DECIMAL_TOLERANCIA = Decimal("0.01")

TIPOS_OBRIGACAO = {"ADMIN_SEDE_30", "DESPESA_FIXA", "OUTRA"}
ORIGENS_OBRIGACAO = {"automatico", "manual", "migracao"}
STATUS_OBRIGACAO = {"PENDENTE", "PARCIAL", "PAGO", "BAIXADA_HISTORICA", "CANCELADA"}
TIPOS_PAGAMENTO = {"PAGAMENTO_BANCARIO", "HISTORICO_SEM_MOVIMENTACAO"}
EVENTOS_OBRIGACAO = {"CRIACAO", "RECALCULO", "PAGAMENTO", "BAIXA_HISTORICA", "REABERTURA", "AJUSTE", "CANCELAMENTO"}


def _to_decimal(valor) -> Decimal:
    if valor is None:
        return DECIMAL_ZERO
    if isinstance(valor, Decimal):
        return valor.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    return Decimal(str(valor)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


class ObrigacaoFinanceira(db.Model):
    __tablename__ = "obrigacoes_financeiras"

    id = db.Column(db.Integer, primary_key=True)
    tipo_obrigacao = db.Column(db.String(50), nullable=False, index=True)
    origem_obrigacao = db.Column(db.String(20), nullable=False, index=True)
    referencia_origem_tipo = db.Column(db.String(100), nullable=True)
    referencia_origem_id = db.Column(db.Integer, nullable=True)

    categoria = db.Column(db.String(100), nullable=True)
    descricao = db.Column(db.String(255), nullable=False)
    competencia_mes = db.Column(db.Integer, nullable=True, index=True)
    competencia_ano = db.Column(db.Integer, nullable=True, index=True)
    data_vencimento = db.Column(db.Date, nullable=True)

    valor_devido = db.Column(db.Numeric(12, 2), nullable=False)
    status = db.Column(db.String(30), nullable=False, default="PENDENTE", index=True)
    data_quitacao = db.Column(db.Date, nullable=True)
    historico_sem_movimentacao = db.Column(db.Boolean, nullable=False, default=False)
    observacao = db.Column(db.Text, nullable=True)

    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    criado_por = db.Column(db.String(100), nullable=True)
    atualizado_por = db.Column(db.String(100), nullable=True)

    pagamento_itens = db.relationship(
        "PagamentoObrigacaoItem",
        back_populates="obrigacao_financeira",
        lazy="select",
    )
    eventos = db.relationship(
        "ObrigacaoEvento",
        back_populates="obrigacao_financeira",
        lazy="select",
    )

    __table_args__ = (
        db.CheckConstraint("valor_devido > 0", name="ck_obrigacoes_valor_devido_positivo"),
        db.CheckConstraint("competencia_mes IS NULL OR (competencia_mes BETWEEN 1 AND 12)", name="ck_obrigacoes_competencia_mes"),
        db.CheckConstraint("competencia_ano IS NULL OR (competencia_ano BETWEEN 1900 AND 9999)", name="ck_obrigacoes_competencia_ano"),
        db.Index(
            "uq_obrigacoes_auto_admin_competencia",
            "tipo_obrigacao",
            "competencia_mes",
            "competencia_ano",
            unique=True,
            postgresql_where=db.text(
                "tipo_obrigacao = 'ADMIN_SEDE_30' "
                "AND origem_obrigacao = 'automatico' "
                "AND competencia_mes IS NOT NULL "
                "AND competencia_ano IS NOT NULL"
            ),
            sqlite_where=db.text(
                "tipo_obrigacao = 'ADMIN_SEDE_30' "
                "AND origem_obrigacao = 'automatico' "
                "AND competencia_mes IS NOT NULL "
                "AND competencia_ano IS NOT NULL"
            ),
        ),
        db.Index(
            "uq_obrigacoes_auto_despesa_ref_competencia",
            "tipo_obrigacao",
            "referencia_origem_tipo",
            "referencia_origem_id",
            "competencia_mes",
            "competencia_ano",
            unique=True,
            postgresql_where=db.text(
                "tipo_obrigacao = 'DESPESA_FIXA' "
                "AND origem_obrigacao = 'automatico' "
                "AND referencia_origem_tipo IS NOT NULL "
                "AND referencia_origem_id IS NOT NULL "
                "AND competencia_mes IS NOT NULL "
                "AND competencia_ano IS NOT NULL"
            ),
            sqlite_where=db.text(
                "tipo_obrigacao = 'DESPESA_FIXA' "
                "AND origem_obrigacao = 'automatico' "
                "AND referencia_origem_tipo IS NOT NULL "
                "AND referencia_origem_id IS NOT NULL "
                "AND competencia_mes IS NOT NULL "
                "AND competencia_ano IS NOT NULL"
            ),
        ),
    )

    def _session(self):
        return object_session(self) or db.session

    def _valor_pago_agregado(self, session=None) -> Decimal:
        session = session or self._session()

        if self.id is None:
            total_local = DECIMAL_ZERO
            for item in self.pagamento_itens or []:
                if item is not None:
                    total_local += _to_decimal(item.valor_alocado)
            return total_local.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

        total = session.query(
            func.coalesce(func.sum(PagamentoObrigacaoItem.valor_alocado), 0)
        ).filter(
            PagamentoObrigacaoItem.obrigacao_financeira_id == self.id
        ).scalar()

        return _to_decimal(total)

    @property
    def valor_pago(self) -> Decimal:
        return self._valor_pago_agregado()

    @property
    def valor_pendente(self) -> Decimal:
        pendente = _to_decimal(self.valor_devido) - self._valor_pago_agregado()
        if pendente < DECIMAL_ZERO:
            return DECIMAL_ZERO
        return pendente.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    @property
    def esta_quitada(self) -> bool:
        return self.status == "PAGO" and self.valor_pendente <= DECIMAL_ZERO

    def validar(self):
        if self.tipo_obrigacao not in TIPOS_OBRIGACAO:
            raise ValueError("tipo_obrigacao inválido")
        if self.origem_obrigacao not in ORIGENS_OBRIGACAO:
            raise ValueError("origem_obrigacao inválida")
        if self.status not in STATUS_OBRIGACAO:
            raise ValueError("status inválido")
        if not self.descricao or not self.descricao.strip():
            raise ValueError("descricao é obrigatória")
        if _to_decimal(self.valor_devido) <= DECIMAL_ZERO:
            raise ValueError("valor_devido deve ser maior que zero")
        if self.competencia_mes is not None and not (1 <= int(self.competencia_mes) <= 12):
            raise ValueError("competencia_mes deve estar entre 1 e 12")
        if self.competencia_ano is not None and not (1900 <= int(self.competencia_ano) <= 9999):
            raise ValueError("competencia_ano inválido")

        if self.origem_obrigacao == "automatico" and self.tipo_obrigacao == "ADMIN_SEDE_30":
            if not self.referencia_origem_tipo:
                raise ValueError("referencia_origem_tipo é obrigatória para ADMIN_SEDE_30 automático")
            if self.competencia_mes is None or self.competencia_ano is None:
                raise ValueError("competência é obrigatória para ADMIN_SEDE_30 automático")

        if self.origem_obrigacao == "automatico" and self.tipo_obrigacao == "DESPESA_FIXA":
            if not self.referencia_origem_tipo:
                raise ValueError("referencia_origem_tipo é obrigatória para DESPESA_FIXA automática")
            if self.referencia_origem_id is None:
                raise ValueError("referencia_origem_id é obrigatória para DESPESA_FIXA automática")
            if self.competencia_mes is None or self.competencia_ano is None:
                raise ValueError("competência é obrigatória para DESPESA_FIXA automática")

    def validar_duplicidade_automatica(self, session):
        if self.origem_obrigacao != "automatico":
            return

        if self.tipo_obrigacao not in {"ADMIN_SEDE_30", "DESPESA_FIXA"}:
            return

        if self.tipo_obrigacao == "ADMIN_SEDE_30":
            if self.competencia_mes is None or self.competencia_ano is None:
                return
            query = session.query(ObrigacaoFinanceira).filter(
                ObrigacaoFinanceira.tipo_obrigacao == "ADMIN_SEDE_30",
                ObrigacaoFinanceira.origem_obrigacao == "automatico",
                ObrigacaoFinanceira.competencia_mes == self.competencia_mes,
                ObrigacaoFinanceira.competencia_ano == self.competencia_ano,
            )
        else:
            if not all([
                self.referencia_origem_tipo,
                self.referencia_origem_id is not None,
                self.competencia_mes is not None,
                self.competencia_ano is not None,
            ]):
                return
            query = session.query(ObrigacaoFinanceira).filter(
                ObrigacaoFinanceira.tipo_obrigacao == "DESPESA_FIXA",
                ObrigacaoFinanceira.origem_obrigacao == "automatico",
                ObrigacaoFinanceira.referencia_origem_tipo == self.referencia_origem_tipo,
                ObrigacaoFinanceira.referencia_origem_id == self.referencia_origem_id,
                ObrigacaoFinanceira.competencia_mes == self.competencia_mes,
                ObrigacaoFinanceira.competencia_ano == self.competencia_ano,
            )

        if self.id is not None:
            query = query.filter(ObrigacaoFinanceira.id != self.id)

        if session.query(query.exists()).scalar():
            raise ValueError("obrigação automática duplicada para a mesma chave lógica")

    def recalcular_em_sessao(self, session=None, flush=False):
        session = session or self._session()
        if flush:
            session.flush()

        session.expire(self, ["pagamento_itens"])
        return self.atualizar_status(session=session)

    def atualizar_status(self, session=None):
        session = session or self._session()

        if self.status in {"CANCELADA", "BAIXADA_HISTORICA"}:
            return

        pago = self._valor_pago_agregado(session=session)
        devido = _to_decimal(self.valor_devido)

        if pago <= DECIMAL_ZERO:
            self.status = "PENDENTE"
            self.data_quitacao = None
        elif pago < devido:
            self.status = "PARCIAL"
            self.data_quitacao = None
        else:
            self.status = "PAGO"
            ultima_data = session.query(
                func.max(PagamentoObrigacao.data_pagamento)
            ).join(
                PagamentoObrigacaoItem,
                PagamentoObrigacaoItem.pagamento_obrigacao_id == PagamentoObrigacao.id,
            ).filter(
                PagamentoObrigacaoItem.obrigacao_financeira_id == self.id
            ).scalar()
            self.data_quitacao = ultima_data if ultima_data else date.today()

        return self.status


class PagamentoObrigacao(db.Model):
    __tablename__ = "pagamentos_obrigacao"

    id = db.Column(db.Integer, primary_key=True)
    data_pagamento = db.Column(db.Date, nullable=False, index=True)
    valor_pago = db.Column(db.Numeric(12, 2), nullable=False)
    forma_pagamento = db.Column(db.String(50), nullable=True)
    tipo_pagamento = db.Column(db.String(40), nullable=False, index=True)
    comprovante = db.Column(db.String(300), nullable=True)
    observacao = db.Column(db.Text, nullable=True)
    lancamento_financeiro_id = db.Column(db.Integer, db.ForeignKey("lancamentos.id"), nullable=True, index=True)

    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    criado_por = db.Column(db.String(100), nullable=True)
    atualizado_por = db.Column(db.String(100), nullable=True)

    lancamento_financeiro = db.relationship("Lancamento", foreign_keys=[lancamento_financeiro_id], uselist=False)
    envio_sede = db.relationship(
        "EnvioSede",
        back_populates="pagamento_obrigacao",
        uselist=False,
        foreign_keys="[EnvioSede.pagamento_obrigacao_id]",
        cascade="save-update, merge",
    )
    itens = db.relationship(
        "PagamentoObrigacaoItem",
        back_populates="pagamento_obrigacao",
        lazy="select",
    )

    __table_args__ = (
        db.CheckConstraint("valor_pago > 0", name="ck_pagamento_valor_pago_positivo"),
    )

    @property
    def valor_alocado_total(self) -> Decimal:
        total = DECIMAL_ZERO
        for item in self.itens or []:
            total += _to_decimal(item.valor_alocado)
        return total.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    def validar(self):
        if self.tipo_pagamento not in TIPOS_PAGAMENTO:
            raise ValueError("tipo_pagamento inválido")
        if self.data_pagamento is None:
            raise ValueError("data_pagamento é obrigatória")
        if _to_decimal(self.valor_pago) <= DECIMAL_ZERO:
            raise ValueError("valor_pago deve ser maior que zero")

    def validar_limite_alocacao(self, tolerancia: Decimal = DECIMAL_TOLERANCIA):
        if self.valor_alocado_total > (_to_decimal(self.valor_pago) + tolerancia):
            raise ValueError("somatório de alocações excede valor_pago")

    def adicionar_item(self, obrigacao_financeira: "ObrigacaoFinanceira", valor_alocado):
        session = object_session(self) or db.session
        valor = _to_decimal(valor_alocado)
        if valor <= DECIMAL_ZERO:
            raise ValueError("valor_alocado deve ser maior que zero")

        pendente = obrigacao_financeira.valor_pendente
        if valor > (pendente + DECIMAL_TOLERANCIA):
            raise ValueError("valor_alocado excede saldo pendente da obrigação")

        alocado_total_pos = self.valor_alocado_total + valor
        if alocado_total_pos > (_to_decimal(self.valor_pago) + DECIMAL_TOLERANCIA):
            raise ValueError("somatório de itens excede valor_pago")

        item = PagamentoObrigacaoItem(
            pagamento_obrigacao=self,
            obrigacao_financeira=obrigacao_financeira,
            valor_alocado=valor,
        )
        session.add(item)
        obrigacao_financeira.recalcular_em_sessao(session=session, flush=False)
        return item

    def remover_item(self, item: "PagamentoObrigacaoItem", flush=False):
        session = object_session(self) or db.session
        if item.pagamento_obrigacao_id != self.id:
            raise ValueError("item não pertence ao pagamento informado")

        obrigacao = item.obrigacao_financeira
        session.delete(item)
        if obrigacao is not None:
            obrigacao.recalcular_em_sessao(session=session, flush=flush)

    def alterar_item(self, item: "PagamentoObrigacaoItem", novo_valor_alocado, flush=False):
        session = object_session(self) or db.session
        if item.pagamento_obrigacao_id != self.id:
            raise ValueError("item não pertence ao pagamento informado")

        novo_valor = _to_decimal(novo_valor_alocado)
        if novo_valor <= DECIMAL_ZERO:
            raise ValueError("valor_alocado deve ser maior que zero")

        obrigacao = item.obrigacao_financeira
        if obrigacao is None:
            raise ValueError("item sem obrigação associada")

        pago_atual = obrigacao._valor_pago_agregado(session=session)
        pendente_ajustada = (_to_decimal(obrigacao.valor_devido) - (pago_atual - _to_decimal(item.valor_alocado)))
        if novo_valor > (pendente_ajustada + DECIMAL_TOLERANCIA):
            raise ValueError("valor_alocado excede saldo pendente da obrigação")

        total_sem_item = self.valor_alocado_total - _to_decimal(item.valor_alocado)
        if (total_sem_item + novo_valor) > (_to_decimal(self.valor_pago) + DECIMAL_TOLERANCIA):
            raise ValueError("somatório de itens excede valor_pago")

        item.valor_alocado = novo_valor
        obrigacao.recalcular_em_sessao(session=session, flush=flush)


class PagamentoObrigacaoItem(db.Model):
    __tablename__ = "pagamentos_obrigacao_itens"

    id = db.Column(db.Integer, primary_key=True)
    pagamento_obrigacao_id = db.Column(db.Integer, db.ForeignKey("pagamentos_obrigacao.id", ondelete="RESTRICT"), nullable=False, index=True)
    obrigacao_financeira_id = db.Column(db.Integer, db.ForeignKey("obrigacoes_financeiras.id", ondelete="RESTRICT"), nullable=False, index=True)
    valor_alocado = db.Column(db.Numeric(12, 2), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    pagamento_obrigacao = db.relationship("PagamentoObrigacao", back_populates="itens")
    obrigacao_financeira = db.relationship("ObrigacaoFinanceira", back_populates="pagamento_itens")

    __table_args__ = (
        db.CheckConstraint("valor_alocado > 0", name="ck_pagamento_item_valor_alocado_positivo"),
    )


class ObrigacaoEvento(db.Model):
    __tablename__ = "obrigacao_eventos"

    id = db.Column(db.Integer, primary_key=True)
    obrigacao_financeira_id = db.Column(db.Integer, db.ForeignKey("obrigacoes_financeiras.id", ondelete="RESTRICT"), nullable=False, index=True)
    evento_tipo = db.Column(db.String(40), nullable=False, index=True)
    payload_json = db.Column(db.Text, nullable=True)
    usuario = db.Column(db.String(100), nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    obrigacao_financeira = db.relationship("ObrigacaoFinanceira", back_populates="eventos")

    def validar(self):
        if self.evento_tipo not in EVENTOS_OBRIGACAO:
            raise ValueError("evento_tipo inválido")
