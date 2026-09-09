from __future__ import annotations

import unicodedata
from typing import Any, Iterable

from app.extensoes import db
from app.financeiro.despesas_fixas_model import DespesaFixaConselho
from app.financeiro.obrigacoes_model import ObrigacaoFinanceira


RELATORIO_SEDE_TEMPLATE = "financeiro/relatorio_sede.html"
_CHAVES_FIXAS = (
    "contador_sede",
    "site",
    "projeto_filipe",
    "forca_para_viver",
    "oferta_voluntaria_conchas",
)


def _normalizar_texto(valor: Any) -> str:
    texto = str(valor or "").strip().lower()
    texto = unicodedata.normalize("NFKD", texto)
    return "".join(ch for ch in texto if not unicodedata.combining(ch))


def _chave_despesa_fixa(nome: Any) -> str | None:
    texto = _normalizar_texto(nome)
    if "contador" in texto:
        return "contador_sede"
    if "site" in texto:
        return "site"
    if "filipe" in texto:
        return "projeto_filipe"
    if "forca para viver" in texto:
        return "forca_para_viver"
    if "conchas" in texto:
        return "oferta_voluntaria_conchas"
    return None


def classificar_despesas_fixas_d23d53(itens: Iterable[dict[str, Any]]) -> dict[str, float]:
    """Converte despesas fixas nomeadas no formato já consumido pelo relatório da Sede."""
    resultado = {chave: 0.0 for chave in _CHAVES_FIXAS}
    for item in itens:
        chave = _chave_despesa_fixa(item.get("nome"))
        if chave:
            resultado[chave] += float(item.get("valor") or 0)
    return resultado


def _itens_obrigacoes_competencia(mes: int, ano: int) -> list[dict[str, Any]]:
    """Lê obrigações da competência sem alterar estado ou persistência."""
    linhas = (
        db.session.query(ObrigacaoFinanceira, DespesaFixaConselho)
        .outerjoin(
            DespesaFixaConselho,
            DespesaFixaConselho.id == ObrigacaoFinanceira.referencia_origem_id,
        )
        .filter(
            ObrigacaoFinanceira.tipo_obrigacao == "DESPESA_FIXA",
            ObrigacaoFinanceira.competencia_mes == int(mes),
            ObrigacaoFinanceira.competencia_ano == int(ano),
        )
        .order_by(ObrigacaoFinanceira.id.asc())
        .all()
    )

    itens: list[dict[str, Any]] = []
    for obrigacao, despesa in linhas:
        nome = getattr(despesa, "nome", None)
        if not nome:
            descricao = getattr(obrigacao, "descricao", "") or ""
            nome = descricao.split(" - Despesa Fixa", 1)[0].strip()
        itens.append(
            {
                "nome": nome,
                "valor": float(getattr(obrigacao, "valor_devido", 0) or 0),
            }
        )
    return itens


def _itens_fallback_contexto(contexto: dict[str, Any]) -> list[dict[str, Any]]:
    itens = []
    for item in contexto.get("despesas_fixas_lista") or []:
        if isinstance(item, dict):
            itens.append({"nome": item.get("nome"), "valor": item.get("valor")})
        else:
            itens.append(
                {
                    "nome": getattr(item, "nome", None),
                    "valor": getattr(item, "valor", getattr(item, "valor_padrao", 0)),
                }
            )
    return itens


def corrigir_contexto_relatorio_sede_d23d53(contexto: dict[str, Any]) -> dict[str, Any]:
    """Corrige o detalhamento e o total histórico das despesas fixas do relatório oficial."""
    mes = int(contexto.get("mes"))
    ano = int(contexto.get("ano"))

    itens_competencia = _itens_obrigacoes_competencia(mes, ano)
    itens = itens_competencia or _itens_fallback_contexto(contexto)
    fixas = classificar_despesas_fixas_d23d53(itens)
    total_fixas = sum(float(item.get("valor") or 0) for item in itens)

    envios = contexto.get("envios")
    if isinstance(envios, dict):
        for chave, valor in fixas.items():
            envios[chave] = valor
    else:
        contexto["envios"] = fixas

    # Quando a competência possui obrigações, elas são o retrato histórico oficial.
    # Isso evita que uma futura alteração em valor_padrao reescreva relatórios antigos.
    if itens_competencia:
        totais_sede = contexto.get("totais_sede")
        if isinstance(totais_sede, dict):
            totais_sede["despesas_fixas"] = total_fixas
            valor_admin = float(totais_sede.get("valor_conselho") or 0)
            totais_sede["total_envio_sede"] = valor_admin + total_fixas
        contexto["despesas_fixas_lista"] = itens_competencia

    contexto["despesas_fixas_sede_detalhadas"] = itens
    return contexto


def instalar_correcao_relatorio_sede_d23d53() -> bool:
    """Encadeia um adaptador read-only no render do relatório oficial da Sede."""
    import app.financeiro.financeiro_routes as routes

    atual = routes.render_template
    if getattr(atual, "_d23d53_relatorio_sede", False):
        return False

    render_template_original = atual

    def render_template_d23d53(template_name, *args, **contexto):
        if template_name == RELATORIO_SEDE_TEMPLATE:
            try:
                corrigir_contexto_relatorio_sede_d23d53(contexto)
            except Exception:
                try:
                    from flask import current_app

                    current_app.logger.exception(
                        "D23D53: falha ao corrigir detalhamento de despesas fixas do relatório da Sede"
                    )
                except Exception:
                    pass
        return render_template_original(template_name, *args, **contexto)

    render_template_d23d53._d23d53_relatorio_sede = True
    render_template_d23d53._d23d53_original = render_template_original
    routes.render_template = render_template_d23d53
    return True
