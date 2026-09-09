from __future__ import annotations

from typing import Any

from sqlalchemy import func

from app.extensoes import db
from app.financeiro.obrigacoes_model import ObrigacaoFinanceira, PagamentoObrigacaoItem


DASHBOARD_TEMPLATE = "financeiro/dashboard_moderno.html"


def resumir_obrigacoes_dashboard(tipo_obrigacao: str, mes: int | None = None, ano: int | None = None) -> dict[str, float]:
    """Resume obrigação e pagamentos sem multiplicar valor_devido por JOIN 1:N.

    D23D50: pagamentos são agregados por obrigação em uma subquery antes do JOIN.
    A consulta é somente leitura e preserva os filtros do dashboard existente.
    """
    pagamentos_por_obrigacao = (
        db.session.query(
            PagamentoObrigacaoItem.obrigacao_financeira_id.label("obrigacao_id"),
            func.coalesce(func.sum(PagamentoObrigacaoItem.valor_alocado), 0).label("valor_pago"),
        )
        .group_by(PagamentoObrigacaoItem.obrigacao_financeira_id)
        .subquery()
    )

    query = (
        db.session.query(
            func.coalesce(func.sum(ObrigacaoFinanceira.valor_devido), 0).label("devido_total"),
            func.coalesce(func.sum(func.coalesce(pagamentos_por_obrigacao.c.valor_pago, 0)), 0).label("pago_total"),
        )
        .outerjoin(
            pagamentos_por_obrigacao,
            pagamentos_por_obrigacao.c.obrigacao_id == ObrigacaoFinanceira.id,
        )
        .filter(ObrigacaoFinanceira.tipo_obrigacao == tipo_obrigacao)
    )

    if mes is not None:
        query = query.filter(ObrigacaoFinanceira.competencia_mes == int(mes))
    if ano is not None:
        query = query.filter(ObrigacaoFinanceira.competencia_ano == int(ano))

    row = query.first()
    devido = float((row.devido_total if row is not None else 0) or 0)
    pago = float((row.pago_total if row is not None else 0) or 0)

    return {
        "devido_total": devido,
        "pago_total": pago,
        "saldo_pendente": max(0.0, devido - pago),
    }


def corrigir_contexto_dashboard_d23d50(contexto: dict[str, Any]) -> dict[str, Any]:
    """Corrige apenas os resumos afetados pela agregação 1:N do dashboard."""
    mes = int(contexto.get("mes_selecionado"))
    ano = int(contexto.get("ano_selecionado"))

    repasse = resumir_obrigacoes_dashboard("ADMIN_SEDE_30")
    despesas_fixas = resumir_obrigacoes_dashboard("DESPESA_FIXA", mes=mes, ano=ano)

    resumo_repasse = contexto.get("resumo_repasse")
    if isinstance(resumo_repasse, dict):
        resumo_repasse["saldo_pendente_total"] = repasse["saldo_pendente"]

    resumo_fixas = contexto.get("despesas_fixas_resumo")
    if isinstance(resumo_fixas, dict):
        resumo_fixas.update(
            {
                "obrigacao_competencia": despesas_fixas["devido_total"],
                "pago_competencia": despesas_fixas["pago_total"],
                "saldo_pendente": despesas_fixas["saldo_pendente"],
            }
        )

    metricas = contexto.get("metricas")
    if isinstance(metricas, dict):
        metricas["repasse_pendente"] = repasse["saldo_pendente"]
        metricas["despesas_fixas_pendentes"] = despesas_fixas["saldo_pendente"]

    return contexto


def instalar_correcao_dashboard_d23d50() -> bool:
    """Instala adaptador de contexto sem alterar regras financeiras ou persistência."""
    import app.financeiro.financeiro_routes as routes

    atual = routes.render_template
    if getattr(atual, "_d23d50_dashboard", False):
        return False

    render_template_original = atual

    def render_template_d23d50(template_name, *args, **contexto):
        if template_name == DASHBOARD_TEMPLATE:
            try:
                corrigir_contexto_dashboard_d23d50(contexto)
            except Exception:
                # O dashboard continua disponível mesmo se o adaptador falhar;
                # o erro fica explícito no log para diagnóstico.
                try:
                    from flask import current_app

                    current_app.logger.exception("D23D50: falha ao corrigir agregação do dashboard financeiro")
                except Exception:
                    pass
        return render_template_original(template_name, *args, **contexto)

    render_template_d23d50._d23d50_dashboard = True
    render_template_d23d50._d23d50_original = render_template_original
    routes.render_template = render_template_d23d50
    return True
