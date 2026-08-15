from flask import Blueprint, render_template, request, redirect, url_for, flash, send_file, current_app, session
from flask_login import login_required, current_user
from app.extensoes import db
from app.financeiro.financeiro_model import Lancamento
from app.financeiro.financeiro_model import ConciliacaoHistorico, ConciliacaoPar
from app.financeiro.projeto_model import Projeto
from app.financeiro.despesas_fixas_model import DespesaFixaConselho
from app.financeiro.envios_sede_model import EnvioSede
from app.financeiro.obrigacoes_model import (
    ObrigacaoFinanceira,
    ObrigacaoEvento,
    PagamentoObrigacao,
    PagamentoObrigacaoItem,
)
from app.financeiro.observacao_relatorio_model import ObservacaoRelatorio
from app.financeiro.recibo_model import Recibo
from app.configuracoes.configuracoes_model import Configuracao
from app.utils.gerar_pdf_reportlab import RelatorioFinanceiro, gerar_nome_arquivo_relatorio
from datetime import datetime, date
from sqlalchemy import extract, or_, and_, func, inspect, text
from sqlalchemy.exc import OperationalError, ProgrammingError
from decimal import Decimal, ROUND_HALF_UP
import json
import os
from werkzeug.utils import secure_filename
import io
import csv
import re
from flask import Response
from difflib import SequenceMatcher
from pathlib import Path

financeiro_bp = Blueprint('financeiro', __name__, template_folder='templates')

_ENVIO_SEDE_REGULARIZACAO_SCHEMA_OK = False
_MONEY_QUANTIZE = Decimal('0.01')


def _decimal_monetario(valor):
    if valor is None:
        return Decimal('0')
    if isinstance(valor, Decimal):
        return valor
    return Decimal(str(valor))


def _quantizar_monetario(valor):
    return _decimal_monetario(valor).quantize(_MONEY_QUANTIZE, rounding=ROUND_HALF_UP)


def _valor_total_pagamento_sede(pagamento):
    return _decimal_monetario(getattr(pagamento, 'valor_total', None) if getattr(pagamento, 'valor_total', None) is not None else getattr(pagamento, 'valor', 0))


def _valor_administrativo_pagamento_sede(pagamento):
    if getattr(pagamento, 'valor_administrativo', None) is not None:
        return _decimal_monetario(pagamento.valor_administrativo or 0)
    return _valor_total_pagamento_sede(pagamento)


def _valor_despesas_fixas_pagamento_sede(pagamento):
    return _decimal_monetario((getattr(pagamento, 'valor_despesas_fixas', None) or 0) or 0)


def _competencia_ref_pagamento_sede(pagamento):
    mes_ref = getattr(pagamento, 'competencia_mes', None)
    if mes_ref is None:
        mes_ref = getattr(pagamento, 'competencia_mes_ref', None)
    ano_ref = getattr(pagamento, 'competencia_ano', None)
    if ano_ref is None:
        ano_ref = getattr(pagamento, 'competencia_ano_ref', None)
    return mes_ref, ano_ref


def _tipo_pagamento_sede(pagamento_historico_sem_movimentacao):
    return 'HISTORICO_SEM_MOVIMENTACAO' if bool(pagamento_historico_sem_movimentacao) else 'PAGAMENTO_BANCARIO'


def _descricao_repassa_sede_normalizada(descricao):
    texto = (descricao or '').strip().lower()
    return texto.startswith('30% administrativo - conselho sede')


def normalizar_categoria_lancamento(lancamento):
    categoria = (getattr(lancamento, 'categoria', '') or '').strip()
    if not categoria:
        return 'Sem categoria'

    # Regra centralizada: descrição padrão de 30% classifica exclusivamente como CONTRIB. SEDE.
    if _descricao_repassa_sede_normalizada(getattr(lancamento, 'descricao', '')):
        return 'CONTRIB. SEDE'

    if categoria.upper() in {'CONTRIB. SEDE', 'REPASSE À SEDE'}:
        return 'CONTRIB. SEDE'

    return categoria


def _categoria_lancamento_normalizada_repasse_sede(lancamento):
    return normalizar_categoria_lancamento(lancamento)


def _criar_obrigacao_despesa_fixa_sem_commit(despesa, mes, ano):
    """Cria obrigação+evento para uma despesa fixa sem controlar transação."""
    chave_busca = {
        'tipo_obrigacao': 'DESPESA_FIXA',
        'origem_obrigacao': 'automatico',
        'referencia_origem_tipo': 'DESPESA_FIXA_CONSELHO',
        'referencia_origem_id': despesa.id,
        'competencia_mes': mes,
        'competencia_ano': ano,
    }

    existente = ObrigacaoFinanceira.query.filter_by(**chave_busca).first()
    if existente:
        return {
            'status': 'ja_existente',
            'obrigacao': None,
        }

    descricao = f'{despesa.nome} - Despesa Fixa {mes:02d}/{ano}'
    observacao = (despesa.descricao or '').strip() or 'Despesa fixa mensal'
    valor_devido = Decimal(str(despesa.valor_padrao or 0)).quantize(Decimal('0.01'))

    obrigacao = ObrigacaoFinanceira(
        tipo_obrigacao='DESPESA_FIXA',
        origem_obrigacao='automatico',
        referencia_origem_tipo='DESPESA_FIXA_CONSELHO',
        referencia_origem_id=despesa.id,
        categoria=despesa.categoria or 'DESP. FIXAS',
        descricao=descricao,
        competencia_mes=mes,
        competencia_ano=ano,
        valor_devido=valor_devido,
        status='PENDENTE',
        historico_sem_movimentacao=False,
        data_vencimento=None,
        observacao=observacao,
    )

    obrigacao.validar()
    obrigacao.validar_duplicidade_automatica(db.session)
    db.session.add(obrigacao)
    db.session.flush()

    evento = ObrigacaoEvento(
        obrigacao_financeira_id=obrigacao.id,
        evento_tipo='CRIACAO',
        payload_json=json.dumps(
            {
                'origem': 'automatico',
                'referencia_origem_tipo': 'DESPESA_FIXA_CONSELHO',
                'referencia_origem_id': despesa.id,
                'competencia': f'{mes:02d}/{ano}',
                'valor_devido': str(valor_devido),
            },
            ensure_ascii=False,
        ),
        usuario=None,
    )
    db.session.add(evento)
    db.session.flush()

    return {
        'status': 'criada',
        'obrigacao': obrigacao,
    }


def _calcular_admin_sede_30_legado(mes, ano, percentual_conselho):
    """Replica o cálculo legado do 30% administrativo sem efeitos colaterais."""
    lancamentos_mes = Lancamento.query.filter(
        extract('month', Lancamento.data) == mes,
        extract('year', Lancamento.data) == ano
    ).all()

    dizimos = 0.0
    ofertas_alcadas = 0.0

    for lancamento in lancamentos_mes:
        if (lancamento.tipo or '').strip().lower() != 'entrada':
            continue

        categoria_lower = (lancamento.categoria or '').lower()
        valor = float(lancamento.valor or 0.0)

        if 'dizimo' in categoria_lower or 'dízimo' in categoria_lower:
            dizimos += valor
        elif 'oferta' in categoria_lower:
            if 'omn' in categoria_lower or 'missionaria' in categoria_lower or 'missionária' in categoria_lower:
                continue
            if any(x in categoria_lower for x in ['outras', 'especial', 'voluntaria', 'voluntária']):
                continue
            ofertas_alcadas += valor

    base_calculo = dizimos + ofertas_alcadas
    valor_conselho = base_calculo * (float(percentual_conselho or 0) / 100.0)

    return {
        'dizimos': round(dizimos, 2),
        'ofertas_alcadas': round(ofertas_alcadas, 2),
        'base_calculo': round(base_calculo, 2),
        'valor_conselho': round(valor_conselho, 2),
    }


def _criar_obrigacao_admin_sede_sem_commit(mes, ano, percentual_conselho, calculo_legacy):
    """Cria obrigação+evento de 30% administrativo sem controlar transação."""
    existente = ObrigacaoFinanceira.query.filter(
        ObrigacaoFinanceira.tipo_obrigacao == 'ADMIN_SEDE_30',
        ObrigacaoFinanceira.origem_obrigacao == 'automatico',
        ObrigacaoFinanceira.competencia_mes == mes,
        ObrigacaoFinanceira.competencia_ano == ano,
    ).first()
    if existente:
        return {
            'status': 'ja_existente',
            'obrigacao': None,
            'valor_devido': Decimal('0.00'),
        }

    valor_devido = Decimal(str(calculo_legacy['valor_conselho'] or 0)).quantize(Decimal('0.01'))
    if valor_devido <= Decimal('0.00'):
        return {
            'status': 'sem_base',
            'obrigacao': None,
            'valor_devido': valor_devido,
        }

    referencia_origem_id = (int(ano) * 100) + int(mes)
    descricao = f"{float(percentual_conselho):.0f}% Administrativo - Conselho Sede {int(mes):02d}/{int(ano)}"
    observacao = (
        f"Base de cálculo: R$ {calculo_legacy['base_calculo']:.2f} "
        f"(Dízimos: R$ {calculo_legacy['dizimos']:.2f} + "
        f"Ofertas Alçadas: R$ {calculo_legacy['ofertas_alcadas']:.2f})"
    )

    obrigacao = ObrigacaoFinanceira(
        tipo_obrigacao='ADMIN_SEDE_30',
        origem_obrigacao='automatico',
        referencia_origem_tipo='FECHAMENTO_MENSAL',
        referencia_origem_id=referencia_origem_id,
        categoria='CONTRIB. SEDE',
        descricao=descricao,
        competencia_mes=mes,
        competencia_ano=ano,
        valor_devido=valor_devido,
        status='PENDENTE',
        historico_sem_movimentacao=False,
        data_vencimento=None,
        observacao=observacao,
    )

    obrigacao.validar()
    obrigacao.validar_duplicidade_automatica(db.session)
    db.session.add(obrigacao)
    db.session.flush()

    evento = ObrigacaoEvento(
        obrigacao_financeira_id=obrigacao.id,
        evento_tipo='CRIACAO',
        payload_json=json.dumps(
            {
                'tipo_obrigacao': 'ADMIN_SEDE_30',
                'competencia': f'{int(mes):02d}/{int(ano)}',
                'percentual': float(percentual_conselho or 0),
                'valor_devido': str(valor_devido),
                'base_calculo_resumida': {
                    'dizimos': calculo_legacy['dizimos'],
                    'ofertas_alcadas': calculo_legacy['ofertas_alcadas'],
                    'base_calculo': calculo_legacy['base_calculo'],
                },
            },
            ensure_ascii=False,
        ),
        usuario=None,
    )
    db.session.add(evento)
    db.session.flush()

    return {
        'status': 'criada',
        'obrigacao': obrigacao,
        'valor_devido': valor_devido,
    }


def gerar_obrigacao_admin_sede_30(mes=None, ano=None):
    """Orquestra a geração da obrigação ADMIN_SEDE_30 com commit único ao final."""
    mes = mes or datetime.now().month
    ano = ano or datetime.now().year

    config = Configuracao.obter_configuracao()
    percentual_conselho = config.percentual_conselho if config and hasattr(config, 'percentual_conselho') and config.percentual_conselho else 30.0
    calculo_legacy = _calcular_admin_sede_30_legado(mes, ano, percentual_conselho)

    resultado = {
        'status': 'erro',
        'erro': None,
        'mes': mes,
        'ano': ano,
        'percentual': float(percentual_conselho),
        'calculo_legacy': calculo_legacy,
        'valor_obrigacao': Decimal(str(calculo_legacy['valor_conselho'])).quantize(Decimal('0.01')),
    }

    try:
        retorno = _criar_obrigacao_admin_sede_sem_commit(
            mes=mes,
            ano=ano,
            percentual_conselho=percentual_conselho,
            calculo_legacy=calculo_legacy,
        )
        resultado['status'] = retorno['status']
        resultado['obrigacao'] = retorno.get('obrigacao')

        if retorno['status'] == 'criada':
            db.session.commit()
        return resultado
    except Exception as e:
        db.session.rollback()
        current_app.logger.exception(f'Erro ao gerar obrigação administrativa da sede: {e}')
        resultado['erro'] = str(e)
        return resultado


def gerar_obrigacoes_despesas_fixas(mes=None, ano=None):
    """Gera obrigações automáticas para despesas fixas ativas do mês informado."""
    mes = mes or datetime.now().month
    ano = ano or datetime.now().year

    resultado = {
        'criadas': [],
        'ja_existentes': [],
        'erros': [],
    }

    despesas_ativas = DespesaFixaConselho.obter_despesas_ativas()
    if not despesas_ativas:
        return resultado

    try:
        for despesa in despesas_ativas:
            retorno = _criar_obrigacao_despesa_fixa_sem_commit(despesa=despesa, mes=mes, ano=ano)
            if retorno['status'] == 'ja_existente':
                resultado['ja_existentes'].append(despesa.nome)
                continue

            resultado['criadas'].append(despesa.nome)

        db.session.commit()
        return resultado

    except Exception as e:
        db.session.rollback()
        current_app.logger.exception(f'Erro ao gerar obrigacoes de despesas fixas: {e}')
        resultado['erros'].append(str(e))
        return resultado


def _decimal_pagamento(valor) -> Decimal:
    return Decimal(str(valor or 0)).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)


def _descricao_lancamento_pagamento_obrigacao(obrigacao: ObrigacaoFinanceira) -> str:
    competencia = ""
    if obrigacao.competencia_mes is not None and obrigacao.competencia_ano is not None:
        competencia = f" {int(obrigacao.competencia_mes):02d}/{int(obrigacao.competencia_ano)}"
    return f"Pagamento obrigação #{obrigacao.id} - {obrigacao.tipo_obrigacao}{competencia}"


def _observacao_lancamento_pagamento_obrigacao(obrigacao: ObrigacaoFinanceira, observacao_pagamento: str | None = None) -> str:
    partes = [
        f"Obrigação ID: {obrigacao.id}",
        f"Tipo: {obrigacao.tipo_obrigacao}",
        f"Descrição: {(obrigacao.descricao or '').strip() or '-'}",
    ]
    if observacao_pagamento:
        partes.append(f"Obs pagamento: {observacao_pagamento}")
    return " | ".join(partes)


def _normalizar_texto_identidade_pagamento(valor: str | None) -> str | None:
    if valor is None:
        return None
    normalizado = " ".join(str(valor).split()).strip()
    if not normalizado:
        return None
    return normalizado.upper()


def _carregar_obrigacao_para_pagamento(obrigacao_id: int):
    query = db.session.query(ObrigacaoFinanceira).filter(
        ObrigacaoFinanceira.id == obrigacao_id,
    )
    query = query.with_for_update()
    return query.one_or_none()


def _detectar_replay_pagamento_obrigacao(
    obrigacao_id: int,
    data_pagamento,
    valor_pago: Decimal,
    tipo_pagamento: str,
    forma_pagamento: str | None,
):
    query = PagamentoObrigacao.query.join(
        PagamentoObrigacaoItem,
        PagamentoObrigacaoItem.pagamento_obrigacao_id == PagamentoObrigacao.id,
    ).filter(
        PagamentoObrigacaoItem.obrigacao_financeira_id == obrigacao_id,
        PagamentoObrigacao.data_pagamento == data_pagamento,
        PagamentoObrigacao.valor_pago == valor_pago,
        PagamentoObrigacao.tipo_pagamento == tipo_pagamento,
        PagamentoObrigacaoItem.valor_alocado == valor_pago,
    )

    if forma_pagamento is None:
        query = query.filter(PagamentoObrigacao.forma_pagamento.is_(None))
    else:
        query = query.filter(PagamentoObrigacao.forma_pagamento == forma_pagamento)

    return query.order_by(PagamentoObrigacao.id.asc()).first()


def _normalizar_alocacoes_pagamento_composto(alocacoes):
    if not alocacoes:
        raise ValueError("alocacoes não pode estar vazia")

    consolidado = {}
    for alloc in alocacoes:
        if not isinstance(alloc, dict):
            raise ValueError("cada alocação deve ser um dicionário")

        obrigacao_id = alloc.get("obrigacao_id")
        if obrigacao_id is None:
            raise ValueError("obrigacao_id é obrigatório em cada alocação")
        try:
            obrigacao_id = int(obrigacao_id)
        except (TypeError, ValueError):
            raise ValueError("obrigacao_id inválido")
        if obrigacao_id <= 0:
            raise ValueError("obrigacao_id deve ser positivo")

        valor = _decimal_pagamento(alloc.get("valor"))
        if valor <= Decimal("0.00"):
            raise ValueError("valor da alocação deve ser maior que zero")

        consolidado[obrigacao_id] = consolidado.get(obrigacao_id, Decimal("0.00")) + valor

    itens = [{"obrigacao_id": obrigacao_id, "valor": valor} for obrigacao_id, valor in sorted(consolidado.items())]
    valor_total = sum((item["valor"] for item in itens), Decimal("0.00")).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    return itens, valor_total


def _detectar_replay_pagamento_composto(
    data_pagamento,
    valor_total: Decimal,
    tipo_pagamento: str,
    forma_pagamento: str | None,
    alocacoes,
):
    forma = _normalizar_texto_identidade_pagamento(forma_pagamento)
    chave = tuple((int(item["obrigacao_id"]), _decimal_pagamento(item["valor"])) for item in alocacoes)

    for pagamento in PagamentoObrigacao.query.order_by(PagamentoObrigacao.id.asc()).all():
        if pagamento.data_pagamento != data_pagamento:
            continue
        if pagamento.valor_pago != valor_total:
            continue
        if pagamento.tipo_pagamento != tipo_pagamento:
            continue
        if pagamento.forma_pagamento != forma:
            continue

        itens = sorted(
            (item.obrigacao_financeira_id, _decimal_pagamento(item.valor_alocado))
            for item in (pagamento.itens or [])
        )
        if tuple(itens) == chave:
            return pagamento

    return None


def _parse_obrigacoes_alocadas_interface(alocacoes_payload):
    if not alocacoes_payload:
        raise ValueError("Selecione pelo menos uma obrigação para alocar o pagamento.")

    alocacoes = []
    vistos = set()
    for idx, item in enumerate(alocacoes_payload):
        if not isinstance(item, dict):
            raise ValueError(f"Alocação inválida na posição {idx}.")
        obrigacao_id = item.get("obrigacao_id")
        valor = item.get("valor")
        if obrigacao_id is None:
            raise ValueError("Obrigação da alocação não informada.")
        try:
            obrigacao_id_int = int(obrigacao_id)
        except (TypeError, ValueError):
            raise ValueError(f"Obrigação inválida na alocação {idx}.")
        if obrigacao_id_int <= 0:
            raise ValueError(f"Obrigação inválida na alocação {idx}.")
        valor_decimal = _decimal_pagamento(valor)
        if valor_decimal <= Decimal("0.00"):
            raise ValueError(f"Valor da alocação da obrigação {obrigacao_id_int} deve ser maior que zero.")
        if obrigacao_id_int in vistos:
            raise ValueError(f"Obrigação duplicada na alocação: {obrigacao_id_int}.")
        vistos.add(obrigacao_id_int)
        alocacoes.append({"obrigacao_id": obrigacao_id_int, "valor": valor_decimal})

    return alocacoes


def _validar_alocacoes_obrigacoes_compostas(alocacoes, *, competencia_mes_ref, competencia_ano_ref):
    if not alocacoes:
        raise ValueError("A alocação do repasse deve conter pelo menos uma obrigação válida.")

    obrigacoes = []
    for item in alocacoes:
        obrigacao_id = int(item["obrigacao_id"])
        obrigacao = db.session.get(ObrigacaoFinanceira, obrigacao_id)
        if obrigacao is None:
            raise ValueError(f"Obrigação inexistente para pagamento: {obrigacao_id}.")
        if obrigacao.tipo_obrigacao not in {"ADMIN_SEDE_30", "DESPESA_FIXA"}:
            raise ValueError(f"Obrigação {obrigacao_id} não pertence ao tipo permitido para repasse.")
        if obrigacao.origem_obrigacao != "automatico":
            raise ValueError(f"Obrigação {obrigacao_id} não é uma obrigação automática do repasse.")
        if obrigacao.competencia_mes != competencia_mes_ref or obrigacao.competencia_ano != competencia_ano_ref:
            raise ValueError(f"Obrigação {obrigacao_id} não pertence à competência {competencia_mes_ref:02d}/{competencia_ano_ref}.")
        obrigacoes.append(obrigacao)

    return obrigacoes


def _registrar_repasse_sede_composto_sem_commit(
    alocacoes,
    competencia_mes_ref,
    competencia_ano_ref,
    data_pagamento,
    forma_pagamento,
    tipo_pagamento,
    comprovante=None,
    observacao=None,
    usuario=None,
    valor_total=None,
    valor_administrativo=None,
    valor_despesas_fixas=None,
):
    if competencia_mes_ref is None or competencia_ano_ref is None:
        raise ValueError("Informe mês e ano de competência para registrar o repasse.")

    alocacoes_norm = _parse_obrigacoes_alocadas_interface(alocacoes)
    _validar_alocacoes_obrigacoes_compostas(alocacoes_norm, competencia_mes_ref=competencia_mes_ref, competencia_ano_ref=competencia_ano_ref)

    validado_tipo = (tipo_pagamento or "").strip().upper()
    if validado_tipo not in {"PAGAMENTO_BANCARIO", "HISTORICO_SEM_MOVIMENTACAO"}:
        raise ValueError("Tipo de pagamento inválido para o repasse à sede.")

    if data_pagamento is None:
        raise ValueError("Data do pagamento é obrigatória para o repasse à sede.")

    retorno = _registrar_pagamento_obrigacoes_sem_commit(
        alocacoes=alocacoes_norm,
        data_pagamento=data_pagamento,
        forma_pagamento=forma_pagamento,
        tipo_pagamento=validado_tipo,
        comprovante=comprovante,
        observacao=observacao,
        usuario=usuario,
    )

    if retorno["status"] == "ja_existente":
        return {
            "status": "ja_existente",
            "pagamento": retorno["pagamento"],
            "obrigacoes": retorno.get("obrigacoes", []),
            "itens": retorno.get("itens", []),
            "lancamento": retorno.get("lancamento"),
            "valor_pago": retorno.get("valor_pago"),
            "tipo_pagamento": validado_tipo,
        }

    competencia = f"Competência {int(competencia_mes_ref):02d}/{int(competencia_ano_ref)}"
    valor_pagamento = float(retorno["valor_pago"] or 0)
    valor_admin = 0.0
    valor_fixas = 0.0
    for item in retorno.get("itens") or []:
        obrigacao = item.obrigacao_financeira
        if obrigacao.tipo_obrigacao == "ADMIN_SEDE_30":
            valor_admin += float(item.valor_alocado or 0)
        elif obrigacao.tipo_obrigacao == "DESPESA_FIXA":
            valor_fixas += float(item.valor_alocado or 0)

    envio = EnvioSede(
        data_pagamento=data_pagamento,
        valor=valor_pagamento,
        valor_administrativo=valor_admin,
        valor_despesas_fixas=valor_fixas,
        valor_total=valor_pagamento,
        forma_pagamento=forma_pagamento or "PIX",
        competencia=competencia,
        competencia_mes_ref=competencia_mes_ref,
        competencia_ano_ref=competencia_ano_ref,
        competencia_mes=competencia_mes_ref,
        competencia_ano=competencia_ano_ref,
        tipo_pagamento=validado_tipo,
        pagamento_obrigacao_id=retorno["pagamento"].id,
        comprovante=comprovante,
        observacao=observacao,
        valor_devido_competencia=valor_pagamento,
        pagamento_historico_sem_movimentacao=(validado_tipo == "HISTORICO_SEM_MOVIMENTACAO"),
        data_pagamento_informada=True,
    )
    db.session.add(envio)
    db.session.flush()

    return {
        "status": "criado",
        "pagamento": retorno["pagamento"],
        "obrigacoes": retorno.get("obrigacoes", []),
        "itens": retorno.get("itens", []),
        "lancamento": retorno.get("lancamento"),
        "envio": envio,
        "valor_pago": retorno.get("valor_pago"),
        "tipo_pagamento": validado_tipo,
        "valor_total_operacao": retorno.get("valor_total_operacao"),
    }


def registrar_repasse_sede_composto(
    alocacoes,
    competencia_mes_ref,
    competencia_ano_ref,
    data_pagamento,
    forma_pagamento,
    tipo_pagamento,
    comprovante=None,
    observacao=None,
    usuario=None,
    valor_total=None,
    valor_administrativo=None,
    valor_despesas_fixas=None,
):
    resultado = {"status": "erro", "erro": None}
    try:
        retorno = _registrar_repasse_sede_composto_sem_commit(
            alocacoes=alocacoes,
            competencia_mes_ref=competencia_mes_ref,
            competencia_ano_ref=competencia_ano_ref,
            data_pagamento=data_pagamento,
            forma_pagamento=forma_pagamento,
            tipo_pagamento=tipo_pagamento,
            comprovante=comprovante,
            observacao=observacao,
            usuario=usuario,
            valor_total=valor_total,
            valor_administrativo=valor_administrativo,
            valor_despesas_fixas=valor_despesas_fixas,
        )
        if retorno["status"] == "ja_existente":
            resultado.update(retorno)
            return resultado
        db.session.commit()
        resultado.update(retorno)
        return resultado
    except Exception as e:
        db.session.rollback()
        current_app.logger.exception(f"Erro ao registrar repasse à sede composto: {e}")
        resultado["erro"] = str(e)
        return resultado


def _registrar_pagamento_obrigacoes_sem_commit(
    alocacoes,
    data_pagamento,
    forma_pagamento: str | None,
    tipo_pagamento: str,
    comprovante: str | None = None,
    observacao: str | None = None,
    usuario: str | None = None,
    forcar_erro_etapa: str | None = None,
):
    alocacoes_norm, valor_total = _normalizar_alocacoes_pagamento_composto(alocacoes)

    if data_pagamento is None:
        raise ValueError("data_pagamento é obrigatória")

    tipo = (tipo_pagamento or "").strip().upper()
    if tipo not in {"PAGAMENTO_BANCARIO", "HISTORICO_SEM_MOVIMENTACAO"}:
        raise ValueError("tipo_pagamento inválido")

    forma = _normalizar_texto_identidade_pagamento(forma_pagamento)
    obs = (observacao or "").strip() or None
    comp = (comprovante or "").strip() or None

    ids = sorted({int(item["obrigacao_id"]) for item in alocacoes_norm})
    query = db.session.query(ObrigacaoFinanceira).filter(ObrigacaoFinanceira.id.in_(ids))
    if hasattr(query, "with_for_update"):
        query = query.with_for_update()

    if hasattr(query, "all"):
        obrigacoes = query.all()
    else:
        obrigacoes = [
            db.session.get(ObrigacaoFinanceira, obrigacao_id)
            for obrigacao_id in ids
            if db.session.get(ObrigacaoFinanceira, obrigacao_id) is not None
        ]

    if len(obrigacoes) != len(ids):
        faltantes = sorted(set(ids) - {obrigacao.id for obrigacao in obrigacoes})
        raise ValueError(f"obrigacao_financeira não encontrada: {faltantes}")

    lookup = {obrigacao.id: obrigacao for obrigacao in obrigacoes}

    replay = _detectar_replay_pagamento_composto(
        data_pagamento=data_pagamento,
        valor_total=valor_total,
        tipo_pagamento=tipo,
        forma_pagamento=forma,
        alocacoes=alocacoes_norm,
    )
    if replay is not None:
        return {
            "status": "ja_existente",
            "pagamento": replay,
            "obrigacoes": [lookup[item.obrigacao_financeira_id] for item in (replay.itens or [])],
            "itens": list(replay.itens or []),
            "lancamento": replay.lancamento_financeiro,
            "valor_pago": valor_total,
            "tipo_pagamento": tipo,
        }

    for obrigacao in obrigacoes:
        if obrigacao.status in {"CANCELADA", "BAIXADA_HISTORICA"}:
            raise ValueError(f"obrigacao_financeira {obrigacao.id} não está ativa para pagamento")
        obrigacao.recalcular_em_sessao(session=db.session, flush=True)

    alocacoes_por_id = {int(item["obrigacao_id"]): _decimal_pagamento(item["valor"]) for item in alocacoes_norm}
    for obrigacao_id, valor_alocado in alocacoes_por_id.items():
        obrigacao = lookup[obrigacao_id]
        if valor_alocado > (_decimal_pagamento(obrigacao.valor_pendente) + Decimal("0.01")):
            raise ValueError(f"valor_alocado excede saldo pendente da obrigação {obrigacao_id}")

    pagamento = PagamentoObrigacao(
        data_pagamento=data_pagamento,
        valor_pago=valor_total,
        forma_pagamento=forma,
        tipo_pagamento=tipo,
        comprovante=comp,
        observacao=obs,
        criado_por=usuario,
        atualizado_por=usuario,
    )
    pagamento.validar()
    db.session.add(pagamento)
    db.session.flush()

    if forcar_erro_etapa == "apos_pagamento":
        raise RuntimeError("falha_forcada_apos_pagamento")

    itens = []
    for item in alocacoes_norm:
        obrigacao = lookup[int(item["obrigacao_id"])]
        item_db = PagamentoObrigacaoItem(
            pagamento_obrigacao=pagamento,
            obrigacao_financeira=obrigacao,
            valor_alocado=_decimal_pagamento(item["valor"]),
        )
        db.session.add(item_db)
        itens.append(item_db)
    db.session.flush()

    if forcar_erro_etapa == "apos_item":
        raise RuntimeError("falha_forcada_apos_item")

    lancamento = None
    if tipo == "PAGAMENTO_BANCARIO":
        categoria = (obrigacoes[0].categoria or "").strip() or "DESP. FIXAS"
        descricao = f"Pagamento composto de {len(alocacoes_norm)} obrigação(ões)"
        lancamento = Lancamento(
            data=data_pagamento,
            tipo="Saída",
            categoria=categoria,
            descricao=descricao,
            valor=float(valor_total),
            conta=_mapear_conta_repasse_sede(forma),
            observacoes=(obs or "Pagamento composto de obrigações")[:255],
            comprovante=comp,
            origem="manual",
        )
        db.session.add(lancamento)
        db.session.flush()
        pagamento.lancamento_financeiro_id = lancamento.id

    if forcar_erro_etapa == "apos_lancamento":
        raise RuntimeError("falha_forcada_apos_lancamento")

    for obrigacao in obrigacoes:
        obrigacao.recalcular_em_sessao(session=db.session, flush=True)

    if forcar_erro_etapa == "apos_status":
        raise RuntimeError("falha_forcada_apos_status")

    for obrigacao in obrigacoes:
        valor_alocado = alocacoes_por_id.get(obrigacao.id, Decimal("0.00"))
        evento = ObrigacaoEvento(
            obrigacao_financeira_id=obrigacao.id,
            evento_tipo="PAGAMENTO",
            payload_json=json.dumps(
                {
                    "pagamento_id": pagamento.id,
                    "valor_alocado": str(valor_alocado),
                    "valor_total_operacao": str(valor_total),
                    "tipo_pagamento": tipo,
                    "lancamento_financeiro_id": pagamento.lancamento_financeiro_id,
                },
                ensure_ascii=False,
            ),
            usuario=usuario,
        )
        evento.validar()
        db.session.add(evento)
    db.session.flush()

    return {
        "status": "criado",
        "pagamento": pagamento,
        "obrigacoes": obrigacoes,
        "itens": itens,
        "lancamento": lancamento,
        "valor_pago": valor_total,
        "tipo_pagamento": tipo,
        "valor_total_operacao": valor_total,
    }


def _registrar_pagamento_obrigacao_sem_commit(
    obrigacao_id: int,
    valor_pago,
    data_pagamento,
    forma_pagamento: str | None,
    tipo_pagamento: str,
    comprovante: str | None = None,
    observacao: str | None = None,
    usuario: str | None = None,
    forcar_erro_etapa: str | None = None,
):
    retorno = _registrar_pagamento_obrigacoes_sem_commit(
        alocacoes=[{"obrigacao_id": obrigacao_id, "valor": valor_pago}],
        data_pagamento=data_pagamento,
        forma_pagamento=forma_pagamento,
        tipo_pagamento=tipo_pagamento,
        comprovante=comprovante,
        observacao=observacao,
        usuario=usuario,
        forcar_erro_etapa=forcar_erro_etapa,
    )

    if retorno["status"] == "ja_existente":
        pagamento = retorno["pagamento"]
        return {
            "status": "ja_existente",
            "obrigacao": pagamento.itens[0].obrigacao_financeira if pagamento.itens else None,
            "pagamento": pagamento,
            "item": None,
            "lancamento": pagamento.lancamento_financeiro,
            "valor_pago": retorno["valor_pago"],
            "tipo_pagamento": retorno["tipo_pagamento"],
        }

    pagamento = retorno["pagamento"]
    obrigacao = retorno["obrigacoes"][0]
    item = retorno["itens"][0] if retorno.get("itens") else None
    retorno_compat = {
        "status": "criado",
        "obrigacao": obrigacao,
        "pagamento": pagamento,
        "item": item,
        "lancamento": retorno["lancamento"],
        "valor_pago": retorno["valor_pago"],
        "tipo_pagamento": retorno["tipo_pagamento"],
        "valor_pendente_pos": _decimal_pagamento(obrigacao.valor_pendente),
        "status_obrigacao_pos": obrigacao.status,
    }
    return retorno_compat


def registrar_pagamento_obrigacoes(
    alocacoes,
    data_pagamento,
    forma_pagamento: str | None,
    tipo_pagamento: str,
    comprovante: str | None = None,
    observacao: str | None = None,
    usuario: str | None = None,
    forcar_erro_etapa: str | None = None,
):
    resultado = {"status": "erro", "erro": None}
    try:
        retorno = _registrar_pagamento_obrigacoes_sem_commit(
            alocacoes=alocacoes,
            data_pagamento=data_pagamento,
            forma_pagamento=forma_pagamento,
            tipo_pagamento=tipo_pagamento,
            comprovante=comprovante,
            observacao=observacao,
            usuario=usuario,
            forcar_erro_etapa=forcar_erro_etapa,
        )
        if retorno["status"] == "ja_existente":
            resultado.update(retorno)
            return resultado
        db.session.commit()
        resultado.update(retorno)
        return resultado
    except Exception as e:
        db.session.rollback()
        current_app.logger.exception(f"Erro ao registrar pagamentos em lote: {e}")
        resultado["erro"] = str(e)
        return resultado


def registrar_pagamento_obrigacao(
    obrigacao_id: int,
    valor_pago,
    data_pagamento,
    forma_pagamento: str | None,
    tipo_pagamento: str,
    comprovante: str | None = None,
    observacao: str | None = None,
    usuario: str | None = None,
    forcar_erro_etapa: str | None = None,
):
    resultado = {
        "status": "erro",
        "erro": None,
    }

    try:
        retorno = _registrar_pagamento_obrigacao_sem_commit(
            obrigacao_id=obrigacao_id,
            valor_pago=valor_pago,
            data_pagamento=data_pagamento,
            forma_pagamento=forma_pagamento,
            tipo_pagamento=tipo_pagamento,
            comprovante=comprovante,
            observacao=observacao,
            usuario=usuario,
            forcar_erro_etapa=forcar_erro_etapa,
        )

        if retorno["status"] == "ja_existente":
            resultado.update(retorno)
            return resultado

        db.session.commit()
        resultado.update(retorno)
        return resultado
    except Exception as e:
        db.session.rollback()
        current_app.logger.exception(f"Erro ao registrar pagamento da obrigação {obrigacao_id}: {e}")
        resultado["erro"] = str(e)
        return resultado

def obter_filtros_ativos():
    """Função auxiliar para capturar os filtros ativos da query string ou form"""
    filtros = {}
    
    # Lista de filtros possíveis
    campos_filtro = ['categoria', 'tipo', 'conta', 'mes_ref', 'ano_ref', 'data_inicial', 'data_final', 
                     'valor_min', 'valor_max', 'busca_texto']
    
    # Tentar pegar dos argumentos da URL primeiro
    for campo in campos_filtro:
        valor = request.args.get(campo, '').strip()
        if valor:
            filtros[campo] = valor
    
    # Se não veio da URL, tentar pegar do formulário (POST)
    # Isso é útil quando salvamos um lançamento e queremos manter os filtros
    if not filtros:
        for campo in campos_filtro:
            valor = request.form.get(f'filtro_{campo}', '').strip()
            if valor:
                filtros[campo] = valor
    
    return filtros


    def _resolver_mes_ano_relatorio(mes=None, ano=None):
        """Normaliza mês/ano para os relatórios mensais."""
        hoje = datetime.now()
        mes = mes if mes is not None else request.args.get('mes', type=int)
        ano = ano if ano is not None else request.args.get('ano', type=int)

        if mes is None:
            mes = hoje.month
        if ano is None:
            ano = hoje.year

        if mes < 1 or mes > 12:
            mes = hoje.month
        if ano < 2020 or ano > 2035:
            ano = hoje.year

        return mes, ano


    def _eh_destinacao_relatorio(categoria):
        categoria = (categoria or '').lower()
        return any(x in categoria for x in [
            'destinação', 'destinacao',
            'transferência interna', 'transferencia interna'
        ])


    def _obter_lancamentos_relatorio_mensal(mes, ano):
        return Lancamento.query.filter(
            extract('month', Lancamento.data) == mes,
            extract('year', Lancamento.data) == ano
        ).order_by(
            Lancamento.data.asc(),
            Lancamento.id.asc()
        ).all()


    def _obter_dados_igreja_relatorio(config, saldo_anterior=0):
        return {
            'nome': (config.nome_igreja if config and hasattr(config, 'nome_igreja') and config.nome_igreja else 'OBPC - O Brasil para Cristo'),
            'cidade': (config.cidade if config and hasattr(config, 'cidade') and config.cidade else 'Tietê'),
            'bairro': (config.bairro if config and hasattr(config, 'bairro') and config.bairro else 'Centro'),
            'endereco': (config.endereco if config and hasattr(config, 'endereco') and config.endereco else ''),
            'dirigente': (config.presidente if config and hasattr(config, 'presidente') and config.presidente else 'Pastor Responsável'),
            'pastor': (config.presidente if config and hasattr(config, 'presidente') and config.presidente else 'Pastor Responsável'),
            'tesoureiro': (config.primeiro_tesoureiro if config and hasattr(config, 'primeiro_tesoureiro') and config.primeiro_tesoureiro else 'Tesoureiro(a)'),
            'logo': (config.logo if config and hasattr(config, 'logo') and config.logo else 'logo_obpc_novo.jpg'),
            'saldo_anterior': saldo_anterior
        }

def _gerar_descricao_lancamento_repasse_sede(pagamento):
    competencia = (pagamento.competencia or '').strip()
    if competencia:
        return f'Repasse à Sede - {competencia}'
    if pagamento.competencia_mes_ref and pagamento.competencia_ano_ref:
        return f'Repasse à Sede - {pagamento.competencia_mes_ref:02d}/{pagamento.competencia_ano_ref}'
    return 'Repasse à Sede'


def _rotulo_competencia_repasse(pagamento):
    competencia = (pagamento.competencia or '').strip()
    if competencia:
        return competencia if competencia.lower().startswith(('competência', 'competencia')) else f'Competência {competencia}'
    competencia_mes_ref, competencia_ano_ref = _competencia_ref_pagamento_sede(pagamento)
    if competencia_mes_ref and competencia_ano_ref:
        return f'Competência {int(competencia_mes_ref):02d}/{int(competencia_ano_ref)}'
    return ''


def _gerar_observacao_lancamento_repasse_sede(pagamento):
    partes = []
    competencia = _rotulo_competencia_repasse(pagamento)
    if competencia:
        partes.append(competencia)

    observacao = (pagamento.observacao or '').strip()
    if observacao:
        partes.append(observacao)

    partes.append(
        f"Administrativo: R$ {_valor_administrativo_pagamento_sede(pagamento):.2f} | "
        f"Despesas fixas: R$ {_valor_despesas_fixas_pagamento_sede(pagamento):.2f} | "
        f"Total: R$ {_valor_total_pagamento_sede(pagamento):.2f}"
    )

    if partes:
        return ' | '.join(partes)
    return 'Pagamento de repasse à sede'


def _obter_saldos_componentes_repasse_sede(mes, ano, excluir_pagamento_id=None):
    """Calcula os saldos restantes por componente para a competência informada."""
    config = Configuracao.obter_configuracao()
    percentual_conselho = 30
    if config and hasattr(config, 'percentual_conselho') and config.percentual_conselho:
        percentual_conselho = config.percentual_conselho

    obrigacao_administrativa = float(_calcular_obrigacao_30_mes(mes, ano, percentual_conselho) or 0.0)
    obrigacao_despesas_fixas = float(DespesaFixaConselho.obter_total_despesas_fixas() or 0.0)

    pagamentos = EnvioSede.query.order_by(EnvioSede.data_pagamento.asc(), EnvioSede.id.asc()).all()
    pago_administrativo = 0.0
    pago_despesas_fixas = 0.0

    for pagamento in pagamentos:
        if excluir_pagamento_id and pagamento.id == excluir_pagamento_id:
            continue

        competencia_mes, competencia_ano = _competencia_ref_pagamento_sede(pagamento)
        if competencia_mes is None or competencia_ano is None:
            continue

        if int(competencia_mes) == int(mes) and int(competencia_ano) == int(ano):
            pago_administrativo += _valor_administrativo_pagamento_sede(pagamento)
            pago_despesas_fixas += _valor_despesas_fixas_pagamento_sede(pagamento)

    return {
        'obrigacao_administrativa': round(obrigacao_administrativa, 2),
        'obrigacao_despesas_fixas': round(obrigacao_despesas_fixas, 2),
        'saldo_administrativo': round(obrigacao_administrativa - pago_administrativo, 2),
        'saldo_despesas_fixas': round(obrigacao_despesas_fixas - pago_despesas_fixas, 2),
    }


def _validar_limites_repasse_sede(mes, ano, valor_administrativo, valor_despesas_fixas, excluir_pagamento_id=None):
    saldos = _obter_saldos_componentes_repasse_sede(mes, ano, excluir_pagamento_id=excluir_pagamento_id)

    if saldos['obrigacao_administrativa'] <= 0 and saldos['obrigacao_despesas_fixas'] <= 0:
        return False, 'Não há obrigação de repasse cadastrada para esta competência.'

    if valor_administrativo > saldos['saldo_administrativo'] + 0.009:
        return False, 'O valor administrativo informado excede o saldo disponível da competência.'

    if valor_despesas_fixas > saldos['saldo_despesas_fixas'] + 0.009:
        return False, 'O valor de despesas fixas informado excede o saldo disponível da competência.'

    return True, saldos


def _mapear_conta_repasse_sede(forma_pagamento):
    forma = (forma_pagamento or '').strip().lower()
    if forma == 'dinheiro':
        return 'Dinheiro'
    if forma == 'pix':
        return 'Pix'
    return 'Banco'


def _garantir_colunas_envio_sede_regularizacao():
    """Garante colunas da rotina de regularização inicial sem depender de migrações externas."""
    global _ENVIO_SEDE_REGULARIZACAO_SCHEMA_OK
    if _ENVIO_SEDE_REGULARIZACAO_SCHEMA_OK:
        return

    insp = inspect(db.engine)
    tabelas = set(insp.get_table_names())
    if 'envios_sede' not in tabelas:
        _ENVIO_SEDE_REGULARIZACAO_SCHEMA_OK = True
        return

    colunas = {col['name'] for col in insp.get_columns('envios_sede')}
    dialect = (db.engine.dialect.name or '').lower()

    comandos = []
    if 'valor_devido_competencia' not in colunas:
        comandos.append('ALTER TABLE envios_sede ADD COLUMN valor_devido_competencia FLOAT')
    if 'pagamento_historico_sem_movimentacao' not in colunas:
        if dialect == 'postgresql':
            comandos.append('ALTER TABLE envios_sede ADD COLUMN pagamento_historico_sem_movimentacao BOOLEAN NOT NULL DEFAULT FALSE')
        else:
            comandos.append('ALTER TABLE envios_sede ADD COLUMN pagamento_historico_sem_movimentacao INTEGER NOT NULL DEFAULT 0')
    if 'data_pagamento_informada' not in colunas:
        if dialect == 'postgresql':
            comandos.append('ALTER TABLE envios_sede ADD COLUMN data_pagamento_informada BOOLEAN NOT NULL DEFAULT TRUE')
        else:
            comandos.append('ALTER TABLE envios_sede ADD COLUMN data_pagamento_informada INTEGER NOT NULL DEFAULT 1')
    if 'valor_administrativo' not in colunas:
        comandos.append('ALTER TABLE envios_sede ADD COLUMN valor_administrativo FLOAT')
    if 'valor_despesas_fixas' not in colunas:
        comandos.append('ALTER TABLE envios_sede ADD COLUMN valor_despesas_fixas FLOAT')
    if 'valor_total' not in colunas:
        comandos.append('ALTER TABLE envios_sede ADD COLUMN valor_total FLOAT')
    if 'competencia_mes' not in colunas:
        comandos.append('ALTER TABLE envios_sede ADD COLUMN competencia_mes INTEGER')
    if 'competencia_ano' not in colunas:
        comandos.append('ALTER TABLE envios_sede ADD COLUMN competencia_ano INTEGER')
    if 'tipo_pagamento' not in colunas:
        comandos.append('ALTER TABLE envios_sede ADD COLUMN tipo_pagamento VARCHAR(50)')

    if comandos:
        for comando in comandos:
            db.session.execute(text(comando))
        db.session.commit()

    _ENVIO_SEDE_REGULARIZACAO_SCHEMA_OK = True


def _envio_sede_tem_schema_moderno():
    """Indica se a tabela envios_sede já possui as colunas novas esperadas pelo ORM."""
    try:
        insp = inspect(db.engine)
        tabelas = set(insp.get_table_names())
        if 'envios_sede' not in tabelas:
            return False

        colunas = {col['name'] for col in insp.get_columns('envios_sede')}
        obrigatorias = {
            'valor_devido_competencia',
            'pagamento_historico_sem_movimentacao',
            'data_pagamento_informada',
            'valor_administrativo',
            'valor_despesas_fixas',
            'valor_total',
            'competencia_mes',
            'competencia_ano',
            'tipo_pagamento',
        }
        return obrigatorias.issubset(colunas)
    except Exception:
        return False


def _sincronizar_lancamento_repasse_sede(pagamento, *, commit=True):
    descricao = _gerar_descricao_lancamento_repasse_sede(pagamento)
    valor = _valor_total_pagamento_sede(pagamento)
    data_lancamento = pagamento.data_pagamento

    lancamento = None
    if pagamento.lancamento_financeiro_id:
        lancamento = Lancamento.query.get(pagamento.lancamento_financeiro_id)

    if bool(getattr(pagamento, 'pagamento_historico_sem_movimentacao', False)):
        if lancamento is not None:
            db.session.delete(lancamento)
        pagamento.lancamento_financeiro_id = None
        if commit:
            db.session.flush()
        return None

    if lancamento is None:
        lancamento = Lancamento(
            data=data_lancamento,
            tipo='Saída',
            descricao=descricao,
            valor=valor,
            categoria='REPASSE À SEDE',
            conta=_mapear_conta_repasse_sede(pagamento.forma_pagamento),
            observacoes=_gerar_observacao_lancamento_repasse_sede(pagamento),
            comprovante=pagamento.comprovante,
        )
        db.session.add(lancamento)
        db.session.flush()
        pagamento.lancamento_financeiro_id = lancamento.id
    else:
        lancamento.data = data_lancamento
        lancamento.tipo = 'Saída'
        lancamento.descricao = descricao
        lancamento.valor = valor
        lancamento.categoria = 'REPASSE À SEDE'
        lancamento.conta = _mapear_conta_repasse_sede(pagamento.forma_pagamento)
        lancamento.observacoes = _gerar_observacao_lancamento_repasse_sede(pagamento)
        lancamento.comprovante = pagamento.comprovante

    if commit:
        db.session.flush()
    return lancamento


    def _agrupar_por_categoria_relatorio(lancamentos):
        entradas = {}
        saidas = {}

        for lancamento in lancamentos:
            categoria = _categoria_lancamento_normalizada_repasse_sede(lancamento)
            valor = float(lancamento.valor or 0)

            if lancamento.tipo == 'Entrada':
                entradas[categoria] = entradas.get(categoria, 0) + valor
            elif lancamento.tipo == 'Saída' and not _eh_destinacao_relatorio(lancamento.categoria):
                saidas[categoria] = saidas.get(categoria, 0) + valor

        entradas_ordenadas = dict(sorted(entradas.items(), key=lambda item: item[0].lower()))
        saidas_ordenadas = dict(sorted(saidas.items(), key=lambda item: item[0].lower()))
        return entradas_ordenadas, saidas_ordenadas


    def _obter_comprovantes_lancamento_relatorio(lancamento):
        comprovantes = []

        if lancamento.comprovante and lancamento.comprovante.strip():
            comprovantes.append({
                'nome': lancamento.nome_arquivo_comprovante() or 'Comprovante',
                'url': lancamento.comprovante,
                'origem': 'legado'
            })

        try:
            for comprovante in lancamento.comprovantes.all():
                comprovantes.append({
                    'nome': comprovante.nome_original or comprovante.nome_arquivo() or 'Comprovante',
                    'url': comprovante.arquivo,
                    'origem': 'relacionado'
                })
        except Exception:
            pass

        return comprovantes


    def _montar_movimentacao_relatorio(lancamentos, saldo_anterior):
        movimentacao = []
        saldo_acumulado = float(saldo_anterior or 0)

        for lancamento in lancamentos:
            valor = float(lancamento.valor or 0)
            eh_destinacao = lancamento.tipo == 'Saída' and _eh_destinacao_relatorio(lancamento.categoria)

            entrada = valor if lancamento.tipo == 'Entrada' else 0.0
            saida = valor if lancamento.tipo == 'Saída' and not eh_destinacao else 0.0

            saldo_acumulado += entrada
            saldo_acumulado -= saida

            movimentacao.append({
                'id': lancamento.id,
                'data': lancamento.data,
                'tipo': lancamento.tipo,
                'categoria': lancamento.categoria or 'Sem categoria',
                'descricao': lancamento.descricao or '-',
                'conta': lancamento.conta or '-',
                'observacoes': lancamento.observacoes or '-',
                'valor': valor,
                'entrada': entrada,
                'saida': saida,
                'saldo_acumulado': saldo_acumulado,
                'origem': lancamento.origem or '-',
                'documento_ref': lancamento.documento_ref or '-',
                'eh_destinacao': eh_destinacao,
                'comprovantes': _obter_comprovantes_lancamento_relatorio(lancamento),
                'total_comprovantes': lancamento.total_comprovantes() if hasattr(lancamento, 'total_comprovantes') else 0
            })

        return movimentacao


    def _calcular_totais_relatorio_gerencial(lancamentos, mes, ano, config):
        totais = {
            'entradas_banco': 0,
            'entradas_dinheiro': 0,
            'dizimos_banco': 0,
            'dizimos_dinheiro': 0,
            'ofertas_banco': 0,
            'ofertas_dinheiro': 0,
            'outras_ofertas_banco': 0,
            'outras_ofertas_dinheiro': 0,
            'oferta_omn_banco': 0,
            'oferta_omn_dinheiro': 0,
            'saidas_banco': 0,
            'saidas_dinheiro': 0,
            'descontos': 0,
            'total_entradas': 0,
            'total_saidas': 0,
            'total_dizimos': 0,
            'total_ofertas': 0,
            'total_outras_ofertas': 0,
            'total_oferta_omn': 0,
            'total_dizimos_ofertas': 0,
            'percentual_30': 0,
            'saldo_anterior': Lancamento.calcular_saldo_ate_mes_anterior(mes, ano),
            'saldo_mes': 0,
            'saldo_acumulado': 0,
            'saldo_real_disponivel': 0,
            'trinta_porcento_conselho': 0,
            'despesas_fixas_conselho': 0,
            'total_envio_sede': 0
        }

        for lancamento in lancamentos:
            conta = lancamento.conta.lower() if lancamento.conta else 'dinheiro'
            categoria = lancamento.categoria.lower() if lancamento.categoria else ''
            valor = float(lancamento.valor or 0)

            if lancamento.tipo == 'Entrada':
                if 'banco' in conta or 'pix' in conta:
                    totais['entradas_banco'] += valor
                else:
                    totais['entradas_dinheiro'] += valor

                if 'dízimo' in categoria or 'dizimo' in categoria:
                    if 'banco' in conta or 'pix' in conta:
                        totais['dizimos_banco'] += valor
                    else:
                        totais['dizimos_dinheiro'] += valor
                elif 'omn' in categoria or 'missionaria' in categoria or 'missionária' in categoria:
                    if 'banco' in conta or 'pix' in conta:
                        totais['oferta_omn_banco'] += valor
                    else:
                        totais['oferta_omn_dinheiro'] += valor
                elif 'oferta' in categoria and any(x in categoria for x in ['outras', 'especial', 'voluntaria', 'voluntária']):
                    if 'banco' in conta or 'pix' in conta:
                        totais['outras_ofertas_banco'] += valor
                    else:
                        totais['outras_ofertas_dinheiro'] += valor
                elif 'oferta' in categoria:
                    if 'banco' in conta or 'pix' in conta:
                        totais['ofertas_banco'] += valor
                    else:
                        totais['ofertas_dinheiro'] += valor

                totais['total_entradas'] += valor

            elif lancamento.tipo == 'Saída' and not _eh_destinacao_relatorio(categoria):
                if 'banco' in conta or 'pix' in conta:
                    totais['saidas_banco'] += valor
                else:
                    totais['saidas_dinheiro'] += valor

                totais['total_saidas'] += valor

                if 'desconto' in categoria or 'taxa' in categoria:
                    totais['descontos'] += valor

        totais['total_dizimos'] = totais['dizimos_banco'] + totais['dizimos_dinheiro']
        totais['total_ofertas'] = totais['ofertas_banco'] + totais['ofertas_dinheiro']
        totais['total_outras_ofertas'] = totais['outras_ofertas_banco'] + totais['outras_ofertas_dinheiro']
        totais['total_oferta_omn'] = totais['oferta_omn_banco'] + totais['oferta_omn_dinheiro']
        totais['total_dizimos_ofertas'] = totais['total_dizimos'] + totais['total_ofertas']
        totais['percentual_30'] = totais['total_dizimos_ofertas'] * 0.30
        totais['saldo_mes'] = totais['total_entradas'] - totais['total_saidas']
        totais['saldo_acumulado'] = totais['saldo_anterior'] + totais['saldo_mes']

        percentual = config.percentual_conselho if config and hasattr(config, 'percentual_conselho') and config.percentual_conselho else 30
        valor_administrativo = totais['total_dizimos_ofertas'] * (percentual / 100)

        try:
            despesas_fixas = DespesaFixaConselho.obter_despesas_ativas()
            total_despesas_fixas = sum(d.valor_padrao for d in despesas_fixas) if despesas_fixas else 0
        except Exception:
            total_despesas_fixas = 0

        totais['trinta_porcento_conselho'] = valor_administrativo
        totais['despesas_fixas_conselho'] = total_despesas_fixas
        totais['total_envio_sede'] = valor_administrativo + total_despesas_fixas
        totais['saldo_real_disponivel'] = totais['saldo_acumulado']

        return totais


    def _montar_outras_entradas_relatorio(lancamentos):
        outras_entradas_detalhes = []

        for lancamento in lancamentos:
            if lancamento.tipo != 'Entrada':
                continue

            categoria = _categoria_lancamento_normalizada_repasse_sede(lancamento).lower()
            if 'dízimo' in categoria or 'dizimo' in categoria:
                continue
            if 'omn' in categoria or 'missionaria' in categoria or 'missionária' in categoria:
                continue
            if 'oferta' in categoria:
                continue

            outras_entradas_detalhes.append({
                'data': lancamento.data,
                'categoria': lancamento.categoria or 'Sem categoria',
                'descricao': lancamento.descricao or '-',
                'valor': float(lancamento.valor or 0)
            })

        return sorted(outras_entradas_detalhes, key=lambda item: item['data'])


    def _calcular_envios_relatorio_sede(lancamentos):
        envios = {
            'oferta_voluntaria_conchas': 0.0,
            'site': 0.0,
            'projeto_filipe': 0.0,
            'forca_para_viver': 0.0,
            'contador_sede': 0.0
        }

        envios_detalhados = {
            'oferta_voluntaria_conchas': [],
            'site': [],
            'projeto_filipe': [],
            'forca_para_viver': [],
            'contador_sede': [],
            'omn': []
        }

        mapeamento_envios = {
            'oferta_voluntaria_conchas': ['conchas', 'voluntaria conchas', 'oferta voluntaria conchas'],
            'site': ['site'],
            'projeto_filipe': ['projeto filipe', 'filipe'],
            'forca_para_viver': ['força para viver', 'forca para viver'],
            'contador_sede': ['contador sede', 'contador']
        }

        for lancamento in [item for item in lancamentos if item.tipo == 'Saída']:
            if not lancamento.descricao:
                continue

            descricao_lower = lancamento.descricao.lower()
            for chave, termos_busca in mapeamento_envios.items():
                encontrado = False
                for termo in termos_busca:
                    if termo in descricao_lower:
                        envios[chave] += float(lancamento.valor or 0)
                        envios_detalhados[chave].append({
                            'data': lancamento.data,
                            'descricao': lancamento.descricao,
                            'valor': float(lancamento.valor or 0),
                            'conta': lancamento.conta
                        })
                        encontrado = True
                        break
                if encontrado:
                    break

        for lancamento in lancamentos:
            if lancamento.tipo == 'Entrada' and lancamento.categoria:
                categoria_lower = lancamento.categoria.lower()
                if 'omn' in categoria_lower or 'missionaria' in categoria_lower:
                    envios_detalhados['omn'].append({
                        'data': lancamento.data,
                        'descricao': lancamento.categoria,
                        'conta': getattr(lancamento, 'conta', None),
                        'valor': float(lancamento.valor or 0)
                    })

        return envios, envios_detalhados, sum(envios.values())


    def _montar_despesas_fixas_relatorio():
        try:
            despesas_fixas = DespesaFixaConselho.obter_despesas_ativas()
        except Exception:
            despesas_fixas = []

        lista = [
            {
                'nome': despesa.nome,
                'valor': float(despesa.valor_padrao or 0)
            }
            for despesa in despesas_fixas
        ]
        total = sum(item['valor'] for item in lista)
        return lista, total


    def _montar_indicadores_financeiros_relatorio(totais):
        total_entradas = float(totais.get('total_entradas', 0) or 0)
        total_saidas = float(totais.get('total_saidas', 0) or 0)
        saldo_acumulado = float(totais.get('saldo_acumulado', 0) or 0)

        if total_entradas > 0:
            percentual_despesas = (total_saidas / total_entradas) * 100
            percentual_saldo = (saldo_acumulado / total_entradas) * 100
        else:
            percentual_despesas = 0
            percentual_saldo = 0

        return {
            'percentual_despesas': percentual_despesas,
            'percentual_saldo': percentual_saldo,
            'margem_operacional': total_entradas - total_saidas,
            'nivel_caixa': 'Saudável' if saldo_acumulado >= 0 else 'Atenção'
        }


    def _montar_distribuicao_percentual_relatorio(categorias, total_base):
        distribuicao = []
        total_base = float(total_base or 0)

        for nome, valor in categorias.items():
            percentual = (float(valor or 0) / total_base * 100) if total_base else 0
            distribuicao.append({
                'categoria': nome,
                'valor': float(valor or 0),
                'percentual': percentual
            })

        return sorted(distribuicao, key=lambda item: item['valor'], reverse=True)


    def _montar_evolucao_financeira_relatorio(lancamentos_todos, ano_referencia, mes_referencia, meses=6):
        inicio = max(1, mes_referencia - (meses - 1))
        evolucao = []

        for mes in range(inicio, mes_referencia + 1):
            entradas = 0
            saidas = 0

            for lancamento in lancamentos_todos:
                if not lancamento.data or lancamento.data.year != ano_referencia or lancamento.data.month != mes:
                    continue

                valor = float(lancamento.valor or 0)
                if lancamento.tipo == 'Entrada':
                    entradas += valor
                elif lancamento.tipo == 'Saída' and not _eh_destinacao_relatorio(lancamento.categoria):
                    saidas += valor

            evolucao.append({
                'mes': mes,
                'ano': ano_referencia,
                'entradas': entradas,
                'saidas': saidas,
                'saldo': entradas - saidas
            })

        return evolucao


    def _montar_resumo_executivo_relatorio(totais):
        saldo = float(totais.get('saldo_acumulado', 0) or 0)
        entradas = float(totais.get('total_entradas', 0) or 0)
        saidas = float(totais.get('total_saidas', 0) or 0)

        if entradas == 0 and saidas == 0:
            return 'Período sem movimentação financeira registrada.'
        if saldo >= 0 and entradas >= saidas:
            return 'O período fechou com superávit operacional e manutenção do caixa em nível estável.'
        if saldo >= 0:
            return 'O período fechou com saldo positivo, porém com pressão maior das despesas sobre o caixa.'
        return 'O período fechou com déficit operacional e requer atenção imediata sobre despesas e recomposição de caixa.'


    def gerar_dados_relatorio(tipo_relatorio='gerencial', mes=None, ano=None):
        """Centraliza a montagem de dados dos relatórios financeiros sem alterar as regras existentes."""
        tipo_relatorio = (tipo_relatorio or 'gerencial').lower()
        if tipo_relatorio not in {'gerencial', 'sede', 'auditoria'}:
            tipo_relatorio = 'gerencial'

        mes, ano = _resolver_mes_ano_relatorio(mes, ano)
        config = Configuracao.obter_configuracao()
        lancamentos = _obter_lancamentos_relatorio_mensal(mes, ano)
        todos_lancamentos = Lancamento.query.order_by(Lancamento.data.asc(), Lancamento.id.asc()).all()

        percentual_conselho = config.percentual_conselho if config and hasattr(config, 'percentual_conselho') and config.percentual_conselho else 30
        totais_gerencial = _calcular_totais_relatorio_gerencial(lancamentos, mes, ano, config)
        totais_sede = _calcular_totais_relatorio_sede(lancamentos, percentual_conselho)
        entradas_por_categoria, saidas_por_categoria = _agrupar_por_categoria_relatorio(lancamentos)
        movimentacao = _montar_movimentacao_relatorio(lancamentos, totais_gerencial['saldo_anterior'])
        outras_entradas_detalhes = _montar_outras_entradas_relatorio(lancamentos)
        envios, envios_detalhados, total_envio_sede = _calcular_envios_relatorio_sede(lancamentos)
        despesas_fixas_lista, total_despesas_fixas = _montar_despesas_fixas_relatorio()
        dados_igreja = _obter_dados_igreja_relatorio(config, totais_gerencial['saldo_anterior'])

        totais_sede_apresentacao = {
            'saldo_inicial': totais_gerencial['saldo_anterior'],
            'entradas': totais_gerencial['total_entradas'],
            'saidas': totais_gerencial['total_saidas'],
            'saldo_final': totais_gerencial['saldo_mes'],
            'saldo_acumulado': totais_gerencial['saldo_acumulado'],
            'dizimos': totais_sede['dizimos'],
            'ofertas_alcadas': totais_sede['ofertas_alcadas'],
            'outras_ofertas': totais_sede['outras_ofertas'],
            'oferta_omn': totais_sede['oferta_omn'],
            'outras_entradas': totais_sede['outras_entradas'],
            'despesas_financeiras': totais_sede['despesas_financeiras'],
            'valor_conselho': totais_sede['valor_conselho'],
            'percentual_30': percentual_conselho,
            'despesas_fixas': total_despesas_fixas,
            'total_envio_sede': totais_sede['valor_conselho'] + total_despesas_fixas
        }

        return {
            'tipo_relatorio': tipo_relatorio,
            'mes': mes,
            'ano': ano,
            'config': config,
            'data_geracao': datetime.now(),
            'dados_igreja': dados_igreja,
            'lancamentos': lancamentos,
            'movimentacao': movimentacao,
            'todas_movimentacoes': movimentacao,
            'entradas_por_categoria': entradas_por_categoria,
            'saidas_por_categoria': saidas_por_categoria,
            'totais_gerencial': totais_gerencial,
            'totais_sede': totais_sede_apresentacao,
            'totais': totais_gerencial,
            'outras_entradas_detalhes': outras_entradas_detalhes,
            'envios': envios,
            'envios_detalhados': envios_detalhados,
            'total_envio_sede': total_envio_sede,
            'despesas_fixas_lista': despesas_fixas_lista,
            'resumo_executivo': _montar_resumo_executivo_relatorio(totais_gerencial),
            'indicadores': _montar_indicadores_financeiros_relatorio(totais_gerencial),
            'distribuicao_receitas': _montar_distribuicao_percentual_relatorio(entradas_por_categoria, totais_gerencial['total_entradas']),
            'distribuicao_despesas': _montar_distribuicao_percentual_relatorio(saidas_por_categoria, totais_gerencial['total_saidas']),
            'evolucao_financeira': _montar_evolucao_financeira_relatorio(todos_lancamentos, ano, mes),
            'total_comprovantes': sum(item['total_comprovantes'] for item in movimentacao),
            'template_relatorio': f'financeiro/relatorio_{tipo_relatorio}.html'
        }

def gerar_dados_relatorio(tipo_relatorio='gerencial', mes=None, ano=None):
    """Centraliza a montagem de dados dos relatórios financeiros sem alterar as regras existentes."""
    tipo_relatorio = (tipo_relatorio or 'gerencial').lower()
    if tipo_relatorio not in {'gerencial', 'sede', 'auditoria'}:
        tipo_relatorio = 'gerencial'

    hoje = datetime.now()
    mes = mes if mes is not None else request.args.get('mes', type=int)
    ano = ano if ano is not None else request.args.get('ano', type=int)
    mes = mes if mes and 1 <= mes <= 12 else hoje.month
    ano = ano if ano and 2020 <= ano <= 2035 else hoje.year

    def eh_destinacao(categoria):
        categoria = (categoria or '').lower()
        return any(x in categoria for x in [
            'destinação', 'destinacao',
            'transferência interna', 'transferencia interna'
        ])

    def obter_comprovantes(lancamento):
        comprovantes = []

        if lancamento.comprovante and lancamento.comprovante.strip():
            comprovantes.append({
                'nome': lancamento.nome_arquivo_comprovante() or 'Comprovante',
                'url': lancamento.comprovante,
                'origem': 'legado'
            })

        try:
            for comprovante in lancamento.comprovantes.all():
                comprovantes.append({
                    'nome': comprovante.nome_original or comprovante.nome_arquivo() or 'Comprovante',
                    'url': comprovante.arquivo,
                    'origem': 'relacionado'
                })
        except Exception:
            pass

        return comprovantes

    config = Configuracao.obter_configuracao()
    lancamentos = Lancamento.query.filter(
        extract('month', Lancamento.data) == mes,
        extract('year', Lancamento.data) == ano
    ).order_by(Lancamento.data.asc(), Lancamento.id.asc()).all()
    todos_lancamentos = Lancamento.query.order_by(Lancamento.data.asc(), Lancamento.id.asc()).all()

    saldo_anterior = Lancamento.calcular_saldo_ate_mes_anterior(mes, ano)
    logo_configurada = (config.logo if config and hasattr(config, 'logo') and config.logo else 'logo_obpc_novo.jpg')
    logo_normalizada = str(logo_configurada).replace('\\', '/').strip()

    if '/static/' in logo_normalizada:
        logo_normalizada = logo_normalizada.split('/static/', 1)[1]
    if logo_normalizada.startswith('app/static/'):
        logo_normalizada = logo_normalizada[len('app/static/'):]
    if logo_normalizada.startswith('static/'):
        logo_normalizada = logo_normalizada[len('static/'):]
    logo_normalizada = logo_normalizada.lstrip('/')
    if not logo_normalizada:
        logo_normalizada = 'logo_obpc_novo.jpg'

    dados_igreja = {
        'nome': (config.nome_igreja if config and hasattr(config, 'nome_igreja') and config.nome_igreja else 'OBPC - O Brasil para Cristo'),
        'cidade': (config.cidade if config and hasattr(config, 'cidade') and config.cidade else 'Tietê'),
        'bairro': (config.bairro if config and hasattr(config, 'bairro') and config.bairro else 'Centro'),
        'endereco': (config.endereco if config and hasattr(config, 'endereco') and config.endereco else ''),
        'dirigente': (config.presidente if config and hasattr(config, 'presidente') and config.presidente else 'Pastor Responsável'),
        'pastor': (config.presidente if config and hasattr(config, 'presidente') and config.presidente else 'Pastor Responsável'),
        'tesoureiro': (config.primeiro_tesoureiro if config and hasattr(config, 'primeiro_tesoureiro') and config.primeiro_tesoureiro else 'Tesoureiro(a)'),
        'logo': logo_normalizada,
        'saldo_anterior': saldo_anterior
    }

    totais_gerencial = {
        'entradas_banco': 0,
        'entradas_dinheiro': 0,
        'dizimos_banco': 0,
        'dizimos_dinheiro': 0,
        'ofertas_banco': 0,
        'ofertas_dinheiro': 0,
        'outras_ofertas_banco': 0,
        'outras_ofertas_dinheiro': 0,
        'oferta_omn_banco': 0,
        'oferta_omn_dinheiro': 0,
        'saidas_banco': 0,
        'saidas_dinheiro': 0,
        'descontos': 0,
        'total_entradas': 0,
        'total_saidas': 0,
        'total_dizimos': 0,
        'total_ofertas': 0,
        'total_outras_ofertas': 0,
        'total_oferta_omn': 0,
        'total_dizimos_ofertas': 0,
        'percentual_30': 0,
        'saldo_anterior': saldo_anterior,
        'saldo_mes': 0,
        'saldo_acumulado': 0,
        'saldo_real_disponivel': 0,
        'trinta_porcento_conselho': 0,
        'despesas_fixas_conselho': 0,
        'total_envio_sede': 0
    }

    entradas_por_categoria = {}
    saidas_por_categoria = {}
    outras_entradas_detalhes = []
    movimentacao = []
    saldo_acumulado = float(saldo_anterior or 0)

    for lancamento in lancamentos:
        conta = lancamento.conta.lower() if lancamento.conta else 'dinheiro'
        categoria_original = lancamento.categoria or 'Sem categoria'
        categoria = _categoria_lancamento_normalizada_repasse_sede(lancamento).lower()
        valor = float(lancamento.valor or 0)
        destino = eh_destinacao(categoria)

        if lancamento.tipo == 'Entrada':
            entradas_por_categoria[categoria_original] = entradas_por_categoria.get(categoria_original, 0) + valor

            if 'banco' in conta or 'pix' in conta:
                totais_gerencial['entradas_banco'] += valor
            else:
                totais_gerencial['entradas_dinheiro'] += valor

            if 'dízimo' in categoria or 'dizimo' in categoria:
                if 'banco' in conta or 'pix' in conta:
                    totais_gerencial['dizimos_banco'] += valor
                else:
                    totais_gerencial['dizimos_dinheiro'] += valor
            elif 'omn' in categoria or 'missionaria' in categoria or 'missionária' in categoria:
                if 'banco' in conta or 'pix' in conta:
                    totais_gerencial['oferta_omn_banco'] += valor
                else:
                    totais_gerencial['oferta_omn_dinheiro'] += valor
            elif 'oferta' in categoria and any(x in categoria for x in ['outras', 'especial', 'voluntaria', 'voluntária']):
                if 'banco' in conta or 'pix' in conta:
                    totais_gerencial['outras_ofertas_banco'] += valor
                else:
                    totais_gerencial['outras_ofertas_dinheiro'] += valor
            elif 'oferta' in categoria:
                if 'banco' in conta or 'pix' in conta:
                    totais_gerencial['ofertas_banco'] += valor
                else:
                    totais_gerencial['ofertas_dinheiro'] += valor
            else:
                outras_entradas_detalhes.append({
                    'data': lancamento.data,
                    'categoria': categoria_original,
                    'descricao': lancamento.descricao or '-',
                    'valor': valor
                })

            totais_gerencial['total_entradas'] += valor
            saldo_acumulado += valor
        elif lancamento.tipo == 'Saída':
            if not destino:
                saidas_por_categoria[categoria_original] = saidas_por_categoria.get(categoria_original, 0) + valor
                if 'banco' in conta or 'pix' in conta:
                    totais_gerencial['saidas_banco'] += valor
                else:
                    totais_gerencial['saidas_dinheiro'] += valor

                totais_gerencial['total_saidas'] += valor
                saldo_acumulado -= valor

                if 'desconto' in categoria or 'taxa' in categoria:
                    totais_gerencial['descontos'] += valor

        movimentacao.append({
            'id': lancamento.id,
            'data': lancamento.data,
            'tipo': lancamento.tipo,
            'categoria': categoria_original,
            'descricao': lancamento.descricao or '-',
            'conta': lancamento.conta or '-',
            'observacoes': lancamento.observacoes or '-',
            'valor': valor,
            'entrada': valor if lancamento.tipo == 'Entrada' else 0.0,
            'saida': valor if lancamento.tipo == 'Saída' and not destino else 0.0,
            'saldo_acumulado': saldo_acumulado,
            'origem': lancamento.origem or '-',
            'documento_ref': lancamento.documento_ref or '-',
            'eh_destinacao': destino,
            'comprovantes': obter_comprovantes(lancamento),
            'total_comprovantes': lancamento.total_comprovantes() if hasattr(lancamento, 'total_comprovantes') else 0
        })

    totais_gerencial['total_dizimos'] = totais_gerencial['dizimos_banco'] + totais_gerencial['dizimos_dinheiro']
    totais_gerencial['total_ofertas'] = totais_gerencial['ofertas_banco'] + totais_gerencial['ofertas_dinheiro']
    totais_gerencial['total_outras_ofertas'] = totais_gerencial['outras_ofertas_banco'] + totais_gerencial['outras_ofertas_dinheiro']
    totais_gerencial['total_oferta_omn'] = totais_gerencial['oferta_omn_banco'] + totais_gerencial['oferta_omn_dinheiro']
    totais_gerencial['total_dizimos_ofertas'] = totais_gerencial['total_dizimos'] + totais_gerencial['total_ofertas']
    totais_gerencial['percentual_30'] = totais_gerencial['total_dizimos_ofertas'] * 0.30
    totais_gerencial['saldo_mes'] = totais_gerencial['total_entradas'] - totais_gerencial['total_saidas']
    totais_gerencial['saldo_acumulado'] = totais_gerencial['saldo_anterior'] + totais_gerencial['saldo_mes']
    totais_gerencial['saldo_real_disponivel'] = totais_gerencial['saldo_acumulado']

    percentual_conselho = config.percentual_conselho if config and hasattr(config, 'percentual_conselho') and config.percentual_conselho else 30
    totais_gerencial['trinta_porcento_conselho'] = totais_gerencial['total_dizimos_ofertas'] * (percentual_conselho / 100)

    despesas_fixas_lista = []
    try:
        despesas_fixas = DespesaFixaConselho.obter_despesas_ativas()
        for despesa in despesas_fixas:
            despesas_fixas_lista.append({'nome': despesa.nome, 'valor': float(despesa.valor_padrao or 0)})
    except Exception:
        despesas_fixas_lista = []

    totais_gerencial['despesas_fixas_conselho'] = sum(item['valor'] for item in despesas_fixas_lista)
    totais_gerencial['total_envio_sede'] = totais_gerencial['trinta_porcento_conselho'] + totais_gerencial['despesas_fixas_conselho']

    envios = {
        'oferta_voluntaria_conchas': 0.0,
        'site': 0.0,
        'projeto_filipe': 0.0,
        'forca_para_viver': 0.0,
        'contador_sede': 0.0
    }
    envios_detalhados = {
        'oferta_voluntaria_conchas': [],
        'site': [],
        'projeto_filipe': [],
        'forca_para_viver': [],
        'contador_sede': [],
        'omn': []
    }
    mapeamento_envios = {
        'oferta_voluntaria_conchas': ['conchas', 'voluntaria conchas', 'oferta voluntaria conchas'],
        'site': ['site'],
        'projeto_filipe': ['projeto filipe', 'filipe'],
        'forca_para_viver': ['força para viver', 'forca para viver'],
        'contador_sede': ['contador sede', 'contador']
    }
    for lancamento in [item for item in lancamentos if item.tipo == 'Saída' and item.descricao]:
        descricao_lower = lancamento.descricao.lower()
        for chave, termos in mapeamento_envios.items():
            matched = False
            for termo in termos:
                if termo in descricao_lower:
                    envios[chave] += float(lancamento.valor or 0)
                    envios_detalhados[chave].append({'data': lancamento.data, 'descricao': lancamento.descricao, 'valor': float(lancamento.valor or 0), 'conta': lancamento.conta})
                    matched = True
                    break
            if matched:
                break
    for lancamento in lancamentos:
        if lancamento.tipo == 'Entrada' and lancamento.categoria:
            categoria_lower = lancamento.categoria.lower()
            if 'omn' in categoria_lower or 'missionaria' in categoria_lower or 'missionária' in categoria_lower:
                envios_detalhados['omn'].append({'data': lancamento.data, 'descricao': lancamento.categoria, 'conta': getattr(lancamento, 'conta', None), 'valor': float(lancamento.valor or 0)})

    totais_sede_base = _calcular_totais_relatorio_sede(lancamentos, percentual_conselho)
    totais_sede = {
        'saldo_inicial': saldo_anterior,
        'entradas': totais_gerencial['total_entradas'],
        'saidas': totais_gerencial['total_saidas'],
        'saldo_final': totais_gerencial['saldo_mes'],
        'saldo_acumulado': totais_gerencial['saldo_acumulado'],
        'dizimos': totais_sede_base['dizimos'],
        'ofertas_alcadas': totais_sede_base['ofertas_alcadas'],
        'outras_ofertas': totais_sede_base['outras_ofertas'],
        'oferta_omn': totais_sede_base['oferta_omn'],
        'outras_entradas': totais_sede_base['outras_entradas'],
        'despesas_financeiras': totais_sede_base['despesas_financeiras'],
        'valor_conselho': totais_sede_base['valor_conselho'],
        'percentual_30': percentual_conselho,
        'despesas_fixas': totais_gerencial['despesas_fixas_conselho'],
        'total_envio_sede': totais_sede_base['valor_conselho'] + totais_gerencial['despesas_fixas_conselho']
    }

    controle_repasse_sede = _montar_controle_repasse_sede(mes, ano, percentual_conselho)
    observacao_repasse_sede, observacao_repasse_padrao, observacao_repasse_salva = _obter_observacao_repasse_sede(
        mes,
        ano,
        controle_repasse_sede,
        tipo_relatorio=tipo_relatorio
    )

    def percentual(categorias, total_base):
        total_base = float(total_base or 0)
        itens = []
        for nome, valor in categorias.items():
            itens.append({'categoria': nome, 'valor': float(valor or 0), 'percentual': ((float(valor or 0) / total_base) * 100) if total_base else 0})
        return sorted(itens, key=lambda item: item['valor'], reverse=True)

    evolucao_financeira = []
    inicio_mes = max(1, mes - 5)
    for mes_item in range(inicio_mes, mes + 1):
        entradas = 0
        saidas = 0
        for lancamento in todos_lancamentos:
            if not lancamento.data or lancamento.data.year != ano or lancamento.data.month != mes_item:
                continue
            valor = float(lancamento.valor or 0)
            if lancamento.tipo == 'Entrada':
                entradas += valor
            elif lancamento.tipo == 'Saída' and not eh_destinacao(lancamento.categoria):
                saidas += valor
        evolucao_financeira.append({'mes': mes_item, 'ano': ano, 'entradas': entradas, 'saidas': saidas, 'saldo': entradas - saidas})

    indicadores = {
        'percentual_despesas': ((totais_gerencial['total_saidas'] / totais_gerencial['total_entradas']) * 100) if totais_gerencial['total_entradas'] else 0,
        'percentual_saldo': ((totais_gerencial['saldo_acumulado'] / totais_gerencial['total_entradas']) * 100) if totais_gerencial['total_entradas'] else 0,
        'margem_operacional': totais_gerencial['total_entradas'] - totais_gerencial['total_saidas'],
        'nivel_caixa': 'Saudável' if totais_gerencial['saldo_acumulado'] >= 0 else 'Atenção'
    }

    if totais_gerencial['total_entradas'] == 0 and totais_gerencial['total_saidas'] == 0:
        resumo_executivo = 'Período sem movimentação financeira registrada.'
    elif totais_gerencial['saldo_acumulado'] >= 0 and totais_gerencial['total_entradas'] >= totais_gerencial['total_saidas']:
        resumo_executivo = 'O período fechou com superávit operacional e manutenção do caixa em nível estável.'
    elif totais_gerencial['saldo_acumulado'] >= 0:
        resumo_executivo = 'O período fechou com saldo positivo, porém com pressão maior das despesas sobre o caixa.'
    else:
        resumo_executivo = 'O período fechou com déficit operacional e requer atenção imediata sobre despesas e recomposição de caixa.'

    return {
        'tipo_relatorio': tipo_relatorio,
        'mes': mes,
        'ano': ano,
        'config': config,
        'data_geracao': datetime.now(),
        'dados_igreja': dados_igreja,
        'lancamentos': lancamentos,
        'movimentacao': movimentacao,
        'todas_movimentacoes': movimentacao,
        'entradas_por_categoria': dict(sorted(entradas_por_categoria.items(), key=lambda item: item[0].lower())),
        'saidas_por_categoria': dict(sorted(saidas_por_categoria.items(), key=lambda item: item[0].lower())),
        'totais_gerencial': totais_gerencial,
        'totais_sede': totais_sede,
        'totais': totais_gerencial,
        'outras_entradas_detalhes': sorted(outras_entradas_detalhes, key=lambda item: item['data']),
        'envios': envios,
        'envios_detalhados': envios_detalhados,
        'total_envio_sede': sum(envios.values()),
        'controle_repasse_sede': controle_repasse_sede,
        'observacao_repasse_sede': observacao_repasse_sede,
        'observacao_repasse_padrao': observacao_repasse_padrao,
        'observacao_repasse_salva': observacao_repasse_salva,
        'observacao_repasse_automatica': observacao_repasse_padrao,
        'despesas_fixas_lista': despesas_fixas_lista,
        'resumo_executivo': resumo_executivo,
        'indicadores': indicadores,
        'distribuicao_receitas': percentual(entradas_por_categoria, totais_gerencial['total_entradas']),
        'distribuicao_despesas': percentual(saidas_por_categoria, totais_gerencial['total_saidas']),
        'evolucao_financeira': evolucao_financeira,
        'total_comprovantes': sum(item['total_comprovantes'] for item in movimentacao),
        'template_relatorio': f'financeiro/relatorio_{tipo_relatorio}.html'
    }


@financeiro_bp.route('/financeiro/dashboard')
@login_required
def dashboard_moderno():
    """Dashboard financeiro com visual moderno e métricas"""
    try:
        # Obter mês e ano da URL ou usar atual
        hoje = datetime.now()
        mes_selecionado = request.args.get('mes', hoje.month, type=int)
        ano_selecionado = request.args.get('ano', hoje.year, type=int)
        
        # Calcular totais do mês selecionado
        lancamentos_mes = Lancamento.query.filter(
            extract('month', Lancamento.data) == mes_selecionado,
            extract('year', Lancamento.data) == ano_selecionado
        ).all()
        
        total_entradas = sum(l.valor for l in lancamentos_mes if l.tipo.lower() == 'entrada')
        total_saidas = sum(l.valor for l in lancamentos_mes if l.tipo.lower() in ['saída', 'saida'])
        total_nao_conciliados = len([l for l in lancamentos_mes if not l.conciliado])
        
        # Últimos 10 lançamentos
        ultimos_lancamentos = Lancamento.query.order_by(
            Lancamento.criado_em.desc()
        ).limit(10).all()
        
        # Entradas por categoria (top 5)
        categorias_entradas = db.session.query(
            Lancamento.categoria,
            func.sum(Lancamento.valor).label('total'),
            func.count(Lancamento.id).label('count')
        ).filter(
            Lancamento.tipo.ilike('entrada'),
            extract('month', Lancamento.data) == mes_selecionado,
            extract('year', Lancamento.data) == ano_selecionado
        ).group_by(Lancamento.categoria).order_by(
            func.sum(Lancamento.valor).desc()
        ).limit(5).all()
        
        # ========================================
        # INDICADORES DE DISTRIBUIÇÃO FINANCEIRA
        # ========================================
        config = Configuracao.obter_configuracao()
        indicadores_distribuicao = None
        
        # Verificar se deve exibir indicadores (default True se campo não existir)
        exibir_indicadores = True
        if config:
            try:
                exibir_indicadores = getattr(config, 'exibir_indicador_distribuicao', True)
            except:
                exibir_indicadores = True
        
        if config and exibir_indicadores:
            # Calcular total de Ofertas e Dízimos (entradas)
            total_ofertas_dizimos = sum(
                l.valor for l in lancamentos_mes 
                if l.tipo.lower() == 'entrada' and 
                l.categoria and 
                any(keyword in l.categoria.lower() for keyword in ['oferta', 'dízimo', 'dizimo'])
            )
            
            # Calcular valores ideais baseados nos percentuais configurados
            valor_ideal_administrativo = total_ofertas_dizimos * (config.percentual_administrativo / 100)
            valor_ideal_prebenda = total_ofertas_dizimos * (config.percentual_prebenda / 100)
            valor_ideal_cuidados = total_ofertas_dizimos * (config.percentual_cuidados_igreja / 100)
            
            # Calcular valores reais das despesas por categoria
            # Administrativo: despesas administrativas, sede, escritório, etc
            valor_real_administrativo = sum(
                l.valor for l in lancamentos_mes 
                if l.tipo.lower() in ['saída', 'saida'] and 
                l.categoria and 
                any(keyword in l.categoria.lower() for keyword in ['administrativo', 'sede', 'escritório', 'escritorio', 'material escritório', 'material escritorio'])
            )
            
            # Prebenda: salários pastorais, prebenda, honorários
            valor_real_prebenda = sum(
                l.valor for l in lancamentos_mes 
                if l.tipo.lower() in ['saída', 'saida'] and 
                l.categoria and 
                any(keyword in l.categoria.lower() for keyword in ['prebenda', 'salário', 'salario', 'honorário', 'honorario', 'pastoral'])
            )
            
            # Cuidados da Igreja: manutenção, contas, reformas, etc
            valor_real_cuidados = sum(
                l.valor for l in lancamentos_mes 
                if l.tipo.lower() in ['saída', 'saida'] and 
                l.categoria and 
                any(keyword in l.categoria.lower() for keyword in ['manutenção', 'manutencao', 'energia', 'água', 'agua', 'internet', 'telefone', 'limpeza', 'reforma', 'conservação', 'conservacao', 'aluguel'])
            )
            
            # Calcular percentuais reais
            percentual_real_administrativo = (valor_real_administrativo / total_ofertas_dizimos * 100) if total_ofertas_dizimos > 0 else 0
            percentual_real_prebenda = (valor_real_prebenda / total_ofertas_dizimos * 100) if total_ofertas_dizimos > 0 else 0
            percentual_real_cuidados = (valor_real_cuidados / total_ofertas_dizimos * 100) if total_ofertas_dizimos > 0 else 0
            
            # Calcular desvios
            desvio_administrativo = percentual_real_administrativo - config.percentual_administrativo
            desvio_prebenda = percentual_real_prebenda - config.percentual_prebenda
            desvio_cuidados = percentual_real_cuidados - config.percentual_cuidados_igreja
            
            # Determinar status de cada categoria
            def obter_status(desvio):
                if abs(desvio) <= 5:  # Tolerância de 5%
                    return 'ok'
                elif desvio > 5:
                    return 'acima'
                else:
                    return 'abaixo'
            
            # Gerar alertas
            alertas = []
            if abs(desvio_administrativo) > 5:
                alertas.append({
                    'tipo': 'warning' if desvio_administrativo > 0 else 'info',
                    'mensagem': f'Despesas administrativas {"acima" if desvio_administrativo > 0 else "abaixo"} do ideal ({abs(desvio_administrativo):.1f}%)'
                })
            
            if abs(desvio_prebenda) > 5:
                alertas.append({
                    'tipo': 'warning' if desvio_prebenda > 0 else 'info',
                    'mensagem': f'Prebenda pastoral {"acima" if desvio_prebenda > 0 else "abaixo"} do ideal ({abs(desvio_prebenda):.1f}%)'
                })
            
            if abs(desvio_cuidados) > 5:
                alertas.append({
                    'tipo': 'warning' if desvio_cuidados > 0 else 'info',
                    'mensagem': f'Cuidados da igreja {"acima" if desvio_cuidados > 0 else "abaixo"} do ideal ({abs(desvio_cuidados):.1f}%)'
                })
            
            indicadores_distribuicao = {
                'total_ofertas_dizimos': total_ofertas_dizimos,
                'categorias': [
                    {
                        'nome': 'Administrativo Sede',
                        'percentual_ideal': config.percentual_administrativo,
                        'percentual_real': percentual_real_administrativo,
                        'valor_ideal': valor_ideal_administrativo,
                        'valor_real': valor_real_administrativo,
                        'desvio': desvio_administrativo,
                        'status': obter_status(desvio_administrativo),
                        'fixo': True
                    },
                    {
                        'nome': 'Prebenda Pastoral',
                        'percentual_ideal': config.percentual_prebenda,
                        'percentual_real': percentual_real_prebenda,
                        'valor_ideal': valor_ideal_prebenda,
                        'valor_real': valor_real_prebenda,
                        'desvio': desvio_prebenda,
                        'status': obter_status(desvio_prebenda),
                        'fixo': False,
                        'min': 0,
                        'max': 30
                    },
                    {
                        'nome': 'Cuidados da Igreja',
                        'percentual_ideal': config.percentual_cuidados_igreja,
                        'percentual_real': percentual_real_cuidados,
                        'valor_ideal': valor_ideal_cuidados,
                        'valor_real': valor_real_cuidados,
                        'desvio': desvio_cuidados,
                        'status': obter_status(desvio_cuidados),
                        'fixo': True
                    }
                ],
                'alertas': alertas,
                'status_geral': 'ok' if len(alertas) == 0 else 'atencao' if len(alertas) <= 1 else 'critico'
            }
            
            # Log de debug
            current_app.logger.info(f'>>> INDICADORES: Total ofertas/dízimos = R$ {total_ofertas_dizimos:.2f}')
            current_app.logger.info(f'>>> INDICADORES: Exibir = {exibir_indicadores}, Status = {indicadores_distribuicao["status_geral"]}')
        else:
            current_app.logger.warning(f'>>> INDICADORES NÃO EXIBIDOS: config={config is not None}, exibir={exibir_indicadores}')
        
        return render_template('financeiro/dashboard_moderno.html',
                             total_entradas=total_entradas,
                             total_saidas=total_saidas,
                             total_nao_conciliados=total_nao_conciliados,
                             ultimos_lancamentos=ultimos_lancamentos,
                             categorias_entradas=categorias_entradas,
                             indicadores_distribuicao=indicadores_distribuicao,
                             mes_selecionado=mes_selecionado,
                             ano_selecionado=ano_selecionado)
                             
    except Exception as e:
        # Log detalhado do erro
        import traceback
        current_app.logger.error(f'ERRO NO DASHBOARD: {str(e)}')
        current_app.logger.error(f'TRACEBACK: {traceback.format_exc()}')
        flash(f'Erro ao carregar dashboard: {str(e)}', 'danger')
        return redirect(url_for('financeiro.lista_lancamentos'))

@financeiro_bp.route('/financeiro/lista-moderna')
@login_required
def lista_lancamentos_moderno():
    """Lista de lançamentos com visual moderno"""
    try:
        # Parâmetros de filtro
        search = request.args.get('search', '')
        tipo = request.args.get('tipo', '')
        categoria = request.args.get('categoria', '')
        data_inicio = request.args.get('data_inicio', '')
        data_fim = request.args.get('data_fim', '')
        page = request.args.get('page', 1, type=int)
        
        # Construir query
        query = Lancamento.query
        
        if search:
            query = query.filter(Lancamento.descricao.contains(search))
        if tipo:
            query = query.filter(Lancamento.tipo == tipo)
        if categoria:
            query = query.filter(Lancamento.categoria == categoria)
        if data_inicio:
            query = query.filter(Lancamento.data >= datetime.strptime(data_inicio, '%Y-%m-%d').date())
        if data_fim:
            query = query.filter(Lancamento.data <= datetime.strptime(data_fim, '%Y-%m-%d').date())
            
        # Paginação
        lancamentos = query.order_by(Lancamento.criado_em.desc()).paginate(
            page=page, per_page=20, error_out=False
        )
        
        # Métricas
        total_lancamentos = query.count()
        total_conciliados = query.filter(Lancamento.conciliado == True).count()
        total_pendentes = total_lancamentos - total_conciliados
        
        # Saldo total
        entradas = sum(l.valor for l in query.all() if l.tipo.lower() == 'entrada')
        saidas = sum(l.valor for l in query.all() if l.tipo.lower() in ['saída', 'saida'])
        saldo_total = entradas - saidas
        
        # Categorias disponíveis
        categorias_disponiveis = db.session.query(Lancamento.categoria).distinct().filter(
            Lancamento.categoria.isnot(None)
        ).all()
        categorias_disponiveis = [c[0] for c in categorias_disponiveis if c[0]]
        
        return render_template('financeiro/lista_lancamentos_moderno.html',
                             lancamentos=lancamentos,
                             total_lancamentos=total_lancamentos,
                             total_conciliados=total_conciliados,
                             total_pendentes=total_pendentes,
                             saldo_total=saldo_total,
                             categorias_disponiveis=categorias_disponiveis)
                             
    except Exception as e:
        flash(f'Erro ao carregar lançamentos: {str(e)}', 'danger')
        return redirect(url_for('financeiro.lista_lancamentos'))

@financeiro_bp.route('/financeiro/conciliacao-moderna')
@login_required
def conciliacao_moderno():
    """Conciliação com visual moderno"""
    try:
        # Buscar dados existentes (mesma lógica da rota original)
        importados = Lancamento.query.filter(
            Lancamento.origem == 'importado',
            Lancamento.conciliado == False
        ).all()
        
        historicos = ConciliacaoHistorico.query.order_by(
            ConciliacaoHistorico.data_conciliacao.desc()
        ).limit(10).all()
        
        # Buscar sugestões se existirem na sessão
        sugestoes = session.get('sugestoes_conciliacao', [])
        
        # Calcular taxa de conciliação
        total_lancamentos = Lancamento.query.count()
        total_conciliados = Lancamento.query.filter(Lancamento.conciliado == True).count()
        taxa_conciliacao = (total_conciliados / total_lancamentos * 100) if total_lancamentos > 0 else 0
        
        return render_template('financeiro/conciliacao_moderno.html',
                             importados=importados,
                             historicos=historicos,
                             sugestoes=sugestoes,
                             taxa_conciliacao=taxa_conciliacao)
                             
    except Exception as e:
        flash(f'Erro ao carregar conciliação: {str(e)}', 'danger')
        return redirect(url_for('financeiro.conciliacao'))

# Configurações para upload de arquivos
ALLOWED_EXTENSIONS = {'jpg', 'jpeg', 'png', 'pdf'}

def allowed_file(filename):
    """Verifica se o arquivo tem extensão permitida"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def processar_upload_comprovante(file):
    """Processa upload do arquivo de comprovante"""
    if not file or file.filename == '':
        return None
    
    if not allowed_file(file.filename):
        flash('Tipo de arquivo não permitido. Use: JPG, PNG ou PDF', 'danger')
        return None
    
    try:
        # Gerar nome único para o arquivo
        import uuid
        filename = secure_filename(file.filename)
        nome_unico = f"{uuid.uuid4().hex}_{filename}"
        
        # Criar diretório se não existir
        upload_dir = os.path.join(current_app.root_path, 'static', 'uploads', 'comprovantes')
        os.makedirs(upload_dir, exist_ok=True)
        
        # Salvar arquivo
        file_path = os.path.join(upload_dir, nome_unico)
        file.save(file_path)
        
        # Retornar caminho relativo para salvar no banco
        return f"/static/uploads/comprovantes/{nome_unico}"
        
    except Exception as e:
        flash(f'Erro ao fazer upload do comprovante: {str(e)}', 'danger')
        return None

# ========== ROTAS ESPECÍFICAS (devem vir ANTES de /financeiro) ==========

@financeiro_bp.route('/financeiro/caixa-destinacoes', endpoint='caixa_destinacoes')
@login_required
def caixa_destinacoes():
    """Caixa separado para controlar valores destinados a projetos específicos"""
    print(">>> ROTA CAIXA_DESTINACOES CHAMADA!")
    try:
        # Obter filtros
        mes = request.args.get('mes', type=int)
        ano = request.args.get('ano', type=int, default=datetime.now().year)
        projeto_id = request.args.get('projeto_id', type=int)
        
        # Buscar todos os projetos
        projetos = Projeto.query.order_by(Projeto.nome).all()
        
        # Calcular totais por projeto
        projetos_com_totais = []
        for projeto in projetos:
            totais_projeto = projeto.calcular_totais()
            
            # Filtrar lançamentos do projeto
            query = Lancamento.query.filter(Lancamento.projeto_id == projeto.id)
            
            # Aplicar filtro de período
            if mes:
                query = query.filter(
                    extract('month', Lancamento.data) == mes,
                    extract('year', Lancamento.data) == ano
                )
            elif ano:
                query = query.filter(extract('year', Lancamento.data) == ano)
            
            lancamentos_projeto = query.order_by(Lancamento.data.asc()).all()
            
            if lancamentos_projeto or (not mes and not projeto_id):  # Mostrar projetos sem lançamentos apenas na visão geral
                projetos_com_totais.append({
                    'projeto': projeto,
                    'totais': totais_projeto,
                    'lancamentos': lancamentos_projeto
                })
        
        # Buscar lançamentos sem projeto (legado)
        query_sem_projeto = Lancamento.query.filter(Lancamento.projeto_id == None)
        
        # Aplicar filtro de período
        if mes:
            query_sem_projeto = query_sem_projeto.filter(
                extract('month', Lancamento.data) == mes,
                extract('year', Lancamento.data) == ano
            )
        elif ano:
            query_sem_projeto = query_sem_projeto.filter(extract('year', Lancamento.data) == ano)
        
        # Filtrar apenas OUTRAS OFERTAS e DESTINAÇÃO para lançamentos sem projeto
        lancamentos_sem_projeto = query_sem_projeto.filter(
            or_(
                and_(
                    Lancamento.tipo == 'Entrada',
                    func.upper(Lancamento.categoria) == 'OUTRAS OFERTAS'
                ),
                and_(
                    Lancamento.tipo == 'Saída',
                    func.upper(Lancamento.categoria) == 'DESTINAÇÃO'
                )
            )
        ).order_by(Lancamento.data.asc()).all()
        
        # Calcular totais gerais
        totais_geral = {
            'entradas': sum(p['totais']['entradas'] for p in projetos_com_totais),
            'saidas': sum(p['totais']['saidas'] for p in projetos_com_totais),
            'saldo': sum(p['totais']['saldo'] for p in projetos_com_totais)
        }
        
        # Adicionar lançamentos sem projeto aos totais
        if lancamentos_sem_projeto:
            totais_sem_projeto = {
                'entradas': sum(l.valor for l in lancamentos_sem_projeto if l.tipo == 'Entrada'),
                'saidas': sum(l.valor for l in lancamentos_sem_projeto if l.tipo == 'Saída')
            }
            totais_sem_projeto['saldo'] = totais_sem_projeto['entradas'] - totais_sem_projeto['saidas']
            
            totais_geral['entradas'] += totais_sem_projeto['entradas']
            totais_geral['saidas'] += totais_sem_projeto['saidas']
            totais_geral['saldo'] += totais_sem_projeto['saldo']
        
        return render_template('financeiro/caixa_destinacoes.html',
                             projetos=projetos_com_totais,
                             lancamentos_sem_projeto=lancamentos_sem_projeto,
                             totais=totais_geral,
                             mes=mes,
                             ano=ano,
                             projeto_id=projeto_id,
                             todos_projetos=projetos)
    
    except Exception as e:
        import traceback
        print(f">>> ERRO em caixa_destinacoes: {str(e)}")
        print(traceback.format_exc())
        flash(f'Erro ao carregar caixa de destinações: {str(e)}', 'danger')
        return redirect(url_for('financeiro.lista_lancamentos'))

# ========== ROTAS DE CRUD DE PROJETOS ==========

@financeiro_bp.route('/financeiro/projetos', endpoint='lista_projetos')
@login_required
def lista_projetos():
    """Lista todos os projetos cadastrados"""
    print(">>> ROTA LISTA_PROJETOS CHAMADA!")
    try:
        projetos = Projeto.query.order_by(Projeto.status.desc(), Projeto.nome).all()
        
        # Calcular totais para cada projeto
        projetos_com_totais = []
        for projeto in projetos:
            totais = projeto.calcular_totais()
            projetos_com_totais.append({
                'projeto': projeto,
                'totais': totais
            })
        
        return render_template('financeiro/lista_projetos.html', 
                             projetos=projetos_com_totais)
    except Exception as e:
        import traceback
        print(f">>> ERRO em lista_projetos: {str(e)}")
        print(traceback.format_exc())
        flash(f'Erro ao listar projetos: {str(e)}', 'danger')
        return redirect(url_for('financeiro.lista_lancamentos'))

@financeiro_bp.route('/financeiro/projetos/novo', methods=['GET', 'POST'])
@login_required
def novo_projeto():
    """Cadastra novo projeto"""
    if request.method == 'POST':
        try:
            nome = request.form.get('nome', '').strip()
            descricao = request.form.get('descricao', '').strip()
            tipo = request.form.get('tipo', '').strip()
            status = request.form.get('status', 'Ativo')
            meta_valor_str = request.form.get('meta_valor', '').strip()
            
            # Validações
            if not nome:
                flash('Nome do projeto é obrigatório!', 'danger')
                return redirect(url_for('financeiro.novo_projeto'))
            
            # Verifica duplicidade
            existe = Projeto.query.filter_by(nome=nome).first()
            if existe:
                flash(f'Já existe um projeto com o nome "{nome}"!', 'danger')
                return redirect(url_for('financeiro.novo_projeto'))
            
            # Converter meta_valor
            meta_valor = None
            if meta_valor_str:
                try:
                    meta_valor = float(meta_valor_str.replace('.', '').replace(',', '.'))
                except:
                    pass
            
            # Criar projeto
            projeto = Projeto(
                nome=nome,
                descricao=descricao if descricao else None,
                tipo=tipo if tipo else None,
                status=status,
                meta_valor=meta_valor
            )
            
            db.session.add(projeto)
            db.session.commit()
            
            flash(f'Projeto "{nome}" cadastrado com sucesso!', 'success')
            return redirect(url_for('financeiro.lista_projetos'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao cadastrar projeto: {str(e)}', 'danger')
            return redirect(url_for('financeiro.novo_projeto'))
    
    return render_template('financeiro/cadastro_projeto.html')

@financeiro_bp.route('/financeiro/projetos/editar/<int:id>', methods=['GET', 'POST'])
@login_required
def editar_projeto(id):
    """Edita projeto existente"""
    projeto = Projeto.query.get_or_404(id)
    
    if request.method == 'POST':
        try:
            nome = request.form.get('nome', '').strip()
            descricao = request.form.get('descricao', '').strip()
            tipo = request.form.get('tipo', '').strip()
            status = request.form.get('status', 'Ativo')
            meta_valor_str = request.form.get('meta_valor', '').strip()
            
            if not nome:
                flash('Nome do projeto é obrigatório!', 'danger')
                return redirect(url_for('financeiro.editar_projeto', id=id))
            
            # Verifica duplicidade (exceto o próprio)
            existe = Projeto.query.filter(Projeto.nome == nome, Projeto.id != id).first()
            if existe:
                flash(f'Já existe outro projeto com o nome "{nome}"!', 'danger')
                return redirect(url_for('financeiro.editar_projeto', id=id))
            
            # Converter meta_valor
            meta_valor = None
            if meta_valor_str:
                try:
                    meta_valor = float(meta_valor_str.replace('.', '').replace(',', '.'))
                except:
                    pass
            
            # Atualizar
            projeto.nome = nome
            projeto.descricao = descricao if descricao else None
            projeto.tipo = tipo if tipo else None
            projeto.status = status
            projeto.meta_valor = meta_valor
            projeto.updated_at = datetime.now()
            
            db.session.commit()
            flash(f'Projeto "{nome}" atualizado com sucesso!', 'success')
            return redirect(url_for('financeiro.lista_projetos'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao atualizar projeto: {str(e)}', 'danger')
            return redirect(url_for('financeiro.editar_projeto', id=id))
    
    return render_template('financeiro/cadastro_projeto.html', projeto=projeto)

@financeiro_bp.route('/financeiro/projetos/excluir/<int:id>', methods=['POST'])
@login_required
def excluir_projeto(id):
    """Exclui projeto (apenas se não tiver lançamentos)"""
    try:
        projeto = Projeto.query.get_or_404(id)
        
        # Verifica se tem lançamentos
        if projeto.lancamentos.count() > 0:
            flash(f'Não é possível excluir o projeto "{projeto.nome}" pois existem lançamentos vinculados!', 'danger')
            return redirect(url_for('financeiro.lista_projetos'))
        
        nome = projeto.nome
        db.session.delete(projeto)
        db.session.commit()
        
        flash(f'Projeto "{nome}" excluído com sucesso!', 'success')
        
    except Exception as e:
        db.session.rollback()
        flash(f'Erro ao excluir projeto: {str(e)}', 'danger')
    
    return redirect(url_for('financeiro.lista_projetos'))

# ========== FIM ROTAS DE PROJETOS ==========

# ========== ROTA GENÉRICA (deve vir DEPOIS das específicas) ==========

@financeiro_bp.route('/financeiro/lancamentos')
@financeiro_bp.route('/financeiro')
@login_required
def lista_lancamentos():
    """Lista todos os lançamentos com filtros avançados - VERSÃO MODERNA"""
    try:
        # Obter filtros da query string
        categoria_filtro = request.args.get('categoria', '').strip()
        tipo_filtro = request.args.get('tipo', '').strip()
        conta_filtro = request.args.get('conta', '').strip()
        mes_ref = request.args.get('mes_ref', type=int)
        ano_ref = request.args.get('ano_ref', type=int)
        
        # Novos filtros avançados
        data_inicial = request.args.get('data_inicial', '').strip()
        data_final = request.args.get('data_final', '').strip()
        valor_min = request.args.get('valor_min', '').strip()
        valor_max = request.args.get('valor_max', '').strip()
        busca_texto = request.args.get('busca_texto', '').strip()
        importacao_recente = request.args.get('importacao_recente', '').strip()
        
        # Query base
        query = Lancamento.query
        
        # Se veio de uma importação recente, mostrar primeiro os importados
        mostrar_importados_primeiro = importacao_recente == 'true'
        
        # Aplicar filtro por categoria (com lógica especial para ofertas)
        if categoria_filtro:
            if categoria_filtro == 'Ofertas Alçadas':
                # Ofertas Alçadas = Ofertas normais do ofertório (30% para conselho)
                # Exclui: OMN, Outras Ofertas, Especiais, Voluntárias
                query = query.filter(
                    Lancamento.categoria.ilike('%oferta%')
                ).filter(
                    ~Lancamento.categoria.ilike('%omn%')
                ).filter(
                    ~Lancamento.categoria.ilike('%missionaria%')
                ).filter(
                    ~Lancamento.categoria.ilike('%outras%')
                ).filter(
                    ~Lancamento.categoria.ilike('%especial%')
                ).filter(
                    ~Lancamento.categoria.ilike('%voluntaria%')
                )
            elif categoria_filtro == 'Oferta OMN':
                # Buscar ofertas OMN
                query = query.filter(
                    or_(
                        Lancamento.categoria.ilike('%omn%'),
                        Lancamento.categoria.ilike('%missionaria%')
                    )
                )
            elif categoria_filtro == 'Outras Ofertas':
                # Buscar outras ofertas
                query = query.filter(
                    Lancamento.categoria.ilike('%oferta%')
                ).filter(
                    or_(
                        Lancamento.categoria.ilike('%outras%'),
                        Lancamento.categoria.ilike('%especial%'),
                        Lancamento.categoria.ilike('%voluntaria%')
                    )
                )
            elif categoria_filtro == 'CONTRIB. SEDE':
                # CONTRIB. SEDE + repasse + legados de 30% em DESP. VARIAVEIS.
                query = query.filter(
                    or_(
                        Lancamento.categoria.ilike('CONTRIB. SEDE'),
                        Lancamento.categoria.ilike('REPASSE À SEDE'),
                        Lancamento.descricao.ilike(r'30\% Administrativo - Conselho Sede%', escape='\\')
                    )
                ).filter(
                    Lancamento.tipo == 'Saída'
                )
            elif categoria_filtro in {'DESP. VARIAVEIS', 'DESP. VARIÁVEIS'}:
                # DESP. VARIAVEIS exclui legados 30% que são normalizados para CONTRIB. SEDE.
                query = query.filter(
                    or_(
                        Lancamento.categoria.ilike('DESP. VARIAVEIS'),
                        Lancamento.categoria.ilike('DESP. VARIÁVEIS')
                    )
                ).filter(
                    ~Lancamento.descricao.ilike(r'30\% Administrativo - Conselho Sede%', escape='\\')
                )
            else:
                # Filtro padrão para outras categorias
                query = query.filter(Lancamento.categoria.ilike(f'%{categoria_filtro}%'))
        
        # Aplicar filtro por tipo
        if tipo_filtro:
            query = query.filter(Lancamento.tipo == tipo_filtro)
        
        # Aplicar filtro por conta
        if conta_filtro:
            query = query.filter(Lancamento.conta.ilike(f'%{conta_filtro}%'))

        # Aplicar filtro por mês/ano de referência
        if mes_ref is not None:
            if 1 <= mes_ref <= 12:
                query = query.filter(extract('month', Lancamento.data) == mes_ref)
            else:
                flash('Mês de referência inválido', 'warning')

        if ano_ref is not None:
            if 2020 <= ano_ref <= 2035:
                query = query.filter(extract('year', Lancamento.data) == ano_ref)
            else:
                flash('Ano de referência inválido', 'warning')
            
        # Aplicar filtro por data inicial
        if data_inicial:
            try:
                from datetime import datetime
                data_ini = datetime.strptime(data_inicial, '%Y-%m-%d').date()
                query = query.filter(Lancamento.data >= data_ini)
            except ValueError:
                flash('Data inicial inválida', 'warning')
                
        # Aplicar filtro por data final
        if data_final:
            try:
                from datetime import datetime
                data_fim = datetime.strptime(data_final, '%Y-%m-%d').date()
                query = query.filter(Lancamento.data <= data_fim)
            except ValueError:
                flash('Data final inválida', 'warning')
                
        # Aplicar filtro por valor mínimo
        if valor_min:
            try:
                val_min = float(valor_min.replace(',', '.'))
                query = query.filter(Lancamento.valor >= val_min)
            except ValueError:
                flash('Valor mínimo inválido', 'warning')
                
        # Aplicar filtro por valor máximo
        if valor_max:
            try:
                val_max = float(valor_max.replace(',', '.'))
                query = query.filter(Lancamento.valor <= val_max)
            except ValueError:
                flash('Valor máximo inválido', 'warning')
                
        # Aplicar busca textual (descrição e observações)
        if busca_texto:
            query = query.filter(
                or_(
                    Lancamento.descricao.ilike(f'%{busca_texto}%'),
                    Lancamento.observacoes.ilike(f'%{busca_texto}%')
                )
            )
        
        # Buscar lançamentos filtrados com ordenação especial
        if mostrar_importados_primeiro:
            # Priorizar lançamentos importados no topo da lista
            from sqlalchemy import case
            order_by_clause = [
                case((Lancamento.origem == 'importado', 0), else_=1),
                Lancamento.data.desc(), 
                Lancamento.criado_em.desc()
            ]
            lancamentos_filtrados = query.order_by(*order_by_clause).all()
        else:
            lancamentos_filtrados = query.order_by(Lancamento.data.desc(), Lancamento.criado_em.desc()).all()
        
        # Calcular totais gerais (sem filtro)
        totais_gerais = Lancamento.calcular_totais()
        
        # Calcular totais dos lançamentos filtrados
        totais_filtrados = {
            'entradas': sum(l.valor for l in lancamentos_filtrados if l.tipo == 'Entrada'),
            'saidas': sum(l.valor for l in lancamentos_filtrados if l.tipo == 'Saída'),
            'saldo': 0
        }
        totais_filtrados['saldo'] = totais_filtrados['entradas'] - totais_filtrados['saidas']
        
        # Obter todas as categorias únicas para o filtro (organizadas)
        categorias_todas = db.session.query(Lancamento.categoria).distinct().filter(
            Lancamento.categoria.is_not(None), 
            Lancamento.categoria != ''
        ).order_by(Lancamento.categoria).all()
        
        # Organizar categorias de forma estruturada
        categorias_organizadas = []
        categorias_brutas = [cat[0] for cat in categorias_todas]
        
        # Separar e organizar por tipo
        # CATEGORIAS DE OFERTAS:
        # 1. Ofertas Alçadas = Ofertas do ofertório (30% para conselho)
        # 2. Oferta OMN = Ofertas missionárias (NÃO computa conselho)
        # 3. Outras Ofertas = Especiais, Voluntárias (NÃO computa conselho)
        for categoria in sorted(categorias_brutas):
            cat_lower = categoria.lower()
            
            # Verificar se é oferta e especificar o tipo
            if 'oferta' in cat_lower:
                if 'omn' in cat_lower or 'missionaria' in cat_lower:
                    # Oferta OMN - não computa para conselho
                    categorias_organizadas.append('Oferta OMN')
                elif any(x in cat_lower for x in ['outras', 'especial', 'voluntaria']):
                    # Outras Ofertas - não computa para conselho
                    categorias_organizadas.append('Outras Ofertas')
                else:
                    # Ofertas Alçadas (unifica "Oferta" e "Oferta Alçada")
                    # Computa 30% para conselho administrativo
                    categorias_organizadas.append('Ofertas Alçadas')
            else:
                # Padroniza contribuição/repasse à sede em uma única opção de filtro
                if ('sede' in cat_lower) and ('repasse' in cat_lower or 'contrib' in cat_lower or 'administrativo' in cat_lower):
                    categorias_organizadas.append('CONTRIB. SEDE')
                else:
                    # Não é oferta, manter como está
                    categorias_organizadas.append(categoria)
        
        # Remover duplicatas e manter ordem
        categorias_unicas = list(dict.fromkeys(categorias_organizadas))

        # Mantém a categoria de saída disponível para qualquer mês (ex.: 01) mesmo sem lançamentos no período.
        if 'CONTRIB. SEDE' not in categorias_unicas:
            categorias_unicas.append('CONTRIB. SEDE')
        
        # Obter todas as contas únicas para o filtro
        contas_todas = db.session.query(Lancamento.conta).distinct().filter(
            Lancamento.conta.is_not(None), 
            Lancamento.conta != ''
        ).order_by(Lancamento.conta).all()
        contas_unicas = [conta[0] for conta in contas_todas]
        
        # Obter todas as contas únicas para o filtro
        contas_todas = db.session.query(Lancamento.conta).distinct().filter(
            Lancamento.conta.is_not(None),
            Lancamento.conta != ''
        ).order_by(Lancamento.conta).all()
        contas_unicas = [conta[0] for conta in contas_todas]
        
        # Calcular totais por categoria para exibição
        totais_por_categoria = {}
        for categoria in categorias_unicas:
            # Função auxiliar para verificar se um lançamento pertence à categoria
            def pertence_categoria(lanc, cat):
                categoria_normalizada = normalizar_categoria_lancamento(lanc)
                lanc_cat_lower = lanc.categoria.lower() if lanc.categoria else ''
                
                if cat == 'Ofertas Alçadas':
                    # Ofertas Alçadas = Ofertas do ofertório (30% para conselho)
                    # Exclui: OMN, Outras Ofertas, Especiais, Voluntárias
                    return ('oferta' in lanc_cat_lower and 
                            'omn' not in lanc_cat_lower and 
                            'missionaria' not in lanc_cat_lower and
                            'outras' not in lanc_cat_lower and
                            'especial' not in lanc_cat_lower and
                            'voluntaria' not in lanc_cat_lower)
                elif cat == 'Oferta OMN':
                    # Ofertas OMN
                    return 'omn' in lanc_cat_lower or 'missionaria' in lanc_cat_lower
                elif cat == 'Outras Ofertas':
                    # Outras ofertas especiais
                    return ('oferta' in lanc_cat_lower and 
                            ('outras' in lanc_cat_lower or 'especial' in lanc_cat_lower or 'voluntaria' in lanc_cat_lower))
                else:
                    # Regra única para categorias financeiras comuns.
                    return categoria_normalizada == cat
            
            lancamentos_cat = [l for l in lancamentos_filtrados if pertence_categoria(l, categoria)]
            if lancamentos_cat:
                entradas_cat = sum(l.valor for l in lancamentos_cat if l.tipo == 'Entrada')
                saidas_cat = sum(l.valor for l in lancamentos_cat if l.tipo == 'Saída')
                totais_por_categoria[categoria] = {
                    'entradas': entradas_cat,
                    'saidas': saidas_cat,
                    'saldo': entradas_cat - saidas_cat,
                    'total_registros': len(lancamentos_cat)
                }
        
        # Última conciliação registrada
        ultima_conciliacao = ConciliacaoHistorico.query.order_by(ConciliacaoHistorico.data_conciliacao.desc()).first()
        conciliacao_info = {
            'total_conciliados': ultima_conciliacao.total_conciliados if ultima_conciliacao else 0,
            'total_pendentes': ultima_conciliacao.total_pendentes if ultima_conciliacao else 0,
            'ultima_data': ultima_conciliacao.data_conciliacao if ultima_conciliacao else None
        }

        return render_template('financeiro/lista_lancamentos.html', 
                             lancamentos=lancamentos_filtrados,
                             totais_gerais=totais_gerais,
                             totais_filtrados=totais_filtrados,
                             totais_por_categoria=totais_por_categoria,
                             categorias_unicas=categorias_unicas,
                             contas_unicas=contas_unicas,
                             filtros={
                                 'categoria': categoria_filtro,
                                 'tipo': tipo_filtro,
                                 'conta': conta_filtro,
                                 'mes_ref': mes_ref,
                                 'ano_ref': ano_ref,
                                 'data_inicial': data_inicial,
                                 'data_final': data_final,
                                 'valor_min': valor_min,
                                 'valor_max': valor_max,
                                 'busca_texto': busca_texto
                             },
                             conciliacao_info=conciliacao_info,
                             importacao_recente=mostrar_importados_primeiro)
                             
    except Exception as e:
        flash(f'Erro ao carregar lançamentos: {str(e)}', 'danger')
        return render_template('financeiro/lista_lancamentos.html', 
                             lancamentos=[], 
                             totais_gerais={'entradas': 0, 'saidas': 0, 'saldo': 0},
                             totais_filtrados={'entradas': 0, 'saidas': 0, 'saldo': 0},
                             totais_por_categoria={},
                             categorias_unicas=[],
                             contas_unicas=[],
                             filtros={
                                 'categoria': '', 'tipo': '', 'conta': '',
                                 'mes_ref': '', 'ano_ref': '',
                                 'data_inicial': '', 'data_final': '',
                                 'valor_min': '', 'valor_max': '', 'busca_texto': ''
                             },
                             conciliacao_info={'total_conciliados': 0, 'total_pendentes': 0, 'ultima_data': None},
                             importacao_recente=False)

@financeiro_bp.route('/financeiro/novo')
@login_required
def novo_lancamento():
    """Exibe formulário para cadastro de novo lançamento"""
    # Buscar projetos ativos para o dropdown
    projetos = Projeto.query.filter_by(status='Ativo').order_by(Projeto.nome).all()
    
    # Capturar filtros ativos para preservá-los após salvar
    filtros_ativos = obter_filtros_ativos()
    
    return render_template('financeiro/cadastro_lancamento.html', 
                         today=date.today(), 
                         projetos=projetos,
                         filtros_ativos=filtros_ativos)


@financeiro_bp.route('/financeiro/importar', methods=['GET', 'POST'])
@login_required
def importar_extrato():
    """Formulário para importar extrato bancário (CSV/XLSX)"""
    if request.method == 'POST':
        # Processar upload do arquivo
        if 'arquivo' not in request.files:
            flash('Nenhum arquivo selecionado', 'danger')
            return redirect(request.url)
        
        file = request.files['arquivo']
        if file.filename == '':
            flash('Nenhum arquivo selecionado', 'danger')
            return redirect(request.url)
        
        # Verificar tipo de arquivo
        tipo_arquivo = request.form.get('tipo_arquivo', '')
        if not tipo_arquivo:
            flash('Selecione o tipo de arquivo', 'warning')
            return redirect(request.url)
        
        # Redirecionar para preview com os dados
        try:
            # Criar um form data temporário para a função de preview
            from werkzeug.datastructures import FileStorage
            from io import BytesIO
            
            # Ler o arquivo
            file_content = file.read()
            file.seek(0)  # Reset para uso posterior
            
            # Criar novo FileStorage para preview
            temp_file = FileStorage(
                stream=BytesIO(file_content),
                filename=file.filename,
                content_type=file.content_type
            )
            
            # Chamar a função de preview diretamente
            return importar_extrato_preview_internal(temp_file, tipo_arquivo)
            
        except Exception as e:
            flash(f'Erro ao processar arquivo: {str(e)}', 'danger')
            return redirect(request.url)
    
    return render_template('financeiro/importar_extrato.html')


def importar_extrato_preview_internal(file, tipo_arquivo):
    """Função interna para processar preview de importação"""
    try:
        try:
            import pandas as pd
        except ImportError:
            flash('Pandas não está instalado no ambiente. A importação de extratos requer pandas.', 'warning')
            return redirect(url_for('financeiro.importar_extrato'))
        import io
        
        # Mapear tipo de arquivo para banco
        banco_map = {
            'extrato_bb': 'bancodobrasil',
            'extrato_itau': 'itau', 
            'extrato_caixa': 'caixa',
            'extrato_bradesco': 'bradesco',
            'extrato_santander': 'santander',
            'extrato_pagbank': 'pagbank',
            'ofx_generico': 'ofx',
            'csv_generico': 'generico',
            'txt_generico': 'generico'
        }
        banco = banco_map.get(tipo_arquivo, 'generico')
        
        # Ler arquivo baseado na extensão
        filename = file.filename.lower()
        try:
            if filename.endswith('.csv') or filename.endswith('.txt'):
                # Tentar diferentes encodings para CSV
                file.seek(0)
                content = file.read()
                
                # Tentar UTF-8 primeiro
                try:
                    content_str = content.decode('utf-8')
                    file_obj = io.StringIO(content_str)
                    df = pd.read_csv(file_obj, sep=';')
                    if len(df.columns) == 1:
                        file_obj = io.StringIO(content_str)
                        df = pd.read_csv(file_obj, sep=',')
                except UnicodeDecodeError:
                    # Tentar Latin-1
                    content_str = content.decode('latin-1')
                    file_obj = io.StringIO(content_str)
                    df = pd.read_csv(file_obj, sep=';')
                    if len(df.columns) == 1:
                        file_obj = io.StringIO(content_str)
                        df = pd.read_csv(file_obj, sep=',')
            else:
                file.seek(0)
                df = pd.read_excel(file)
        except Exception as e:
            flash(f'Erro ao ler arquivo: {str(e)}', 'danger')
            return redirect(url_for('financeiro.importar_extrato'))

        # Aplicar mapeamento específico do banco com detecção inteligente
        def encontrar_coluna(df, palavras_chave):
            """Encontra coluna baseada em palavras-chave"""
            # Primeiro tenta encontrar com nomes exatos (case insensitive)
            for col in df.columns:
                for palavra in palavras_chave:
                    if str(col).lower() == palavra.lower():
                        return col
            
            # Se não encontrou, tenta busca parcial sem espaços
            for col in df.columns:
                col_lower = str(col).lower().replace(' ', '').replace('_', '')
                for palavra in palavras_chave:
                    if palavra.lower().replace(' ', '') in col_lower:
                        return col
            return None
        
        # Mapeamento inteligente baseado no banco
        if banco in ['bancodobrasil', 'bb']:
            data_cols = ['data', 'dataoperacao', 'datamovimentacao']
            desc_cols = ['descricao', 'historico', 'memo', 'complemento']
            valor_cols = ['valor', 'valormovimentacao', 'amount']
            tipo_cols = ['natureza', 'tipo', 'credito', 'debito']
        elif banco == 'itau':
            data_cols = ['data', 'dataoperacao', 'date']
            desc_cols = ['descricao', 'historico', 'description']
            valor_cols = ['valor', 'amount', 'montante']
            tipo_cols = ['natureza', 'tipo', 'credito', 'debito']
        elif banco == 'bradesco':
            data_cols = ['data', 'dataoperacao', 'date']
            desc_cols = ['descricao', 'historico', 'memo', 'description']
            valor_cols = ['valor', 'amount', 'montante']
            tipo_cols = ['tipo', 'natureza', 'credito', 'debito']
        elif banco == 'pagbank':
            # Mapeamento específico do PagBank - nomes exatos das colunas
            data_cols = ['DATA', 'data', 'datatransacao', 'dataoperacao', 'date', 'created_at']
            desc_cols = ['DESCRICAO', 'descricao', 'descricaotransacao', 'historico', 'description', 'memo', 'reference']
            valor_cols = ['VALOR', 'valor', 'valortransacao', 'amount', 'montante', 'quantia', 'gross_amount']
            tipo_cols = ['TIPO', 'tipo', 'tipotransacao', 'credito', 'debito', 'natureza', 'transaction_type']
        else:
            # Mapeamento genérico
            data_cols = ['data', 'date', 'fecha']
            desc_cols = ['descricao', 'description', 'memo', 'historico']
            valor_cols = ['valor', 'value', 'amount', 'montante']
            tipo_cols = ['tipo', 'type', 'natureza']
        
        # Encontrar colunas automaticamente
        col_data = encontrar_coluna(df, data_cols)
        col_desc = encontrar_coluna(df, desc_cols)
        col_valor = encontrar_coluna(df, valor_cols)
        col_tipo = encontrar_coluna(df, tipo_cols)
        
        # Verificar se encontrou pelo menos data, descrição e valor
        if not all([col_data, col_desc, col_valor]):
            colunas_encontradas = [f"'{col}'" for col in df.columns]
            flash(f'Arquivo sem colunas essenciais. Colunas encontradas: {", ".join(colunas_encontradas)}. '
                  f'Precisa ter colunas relacionadas a: data, descrição e valor', 'danger')
            return redirect(url_for('financeiro.importar_extrato'))

        # Preparar lista de registros
        registros = []
        for index, row in df.iterrows():
            try:
                data_raw = row.get(col_data)
                descricao = str(row.get(col_desc) or '')
                valor_raw = row.get(col_valor)
                tipo_raw = row.get(col_tipo) if col_tipo else None
                
                # Normalizar data
                try:
                    if pd.isna(data_raw):
                        data_str = None
                    else:
                        # Tentar vários formatos de data
                        data_obj = pd.to_datetime(data_raw, dayfirst=True, errors='coerce')
                        if pd.isna(data_obj):
                            # Tentar formato americano
                            data_obj = pd.to_datetime(data_raw, dayfirst=False, errors='coerce')
                        
                        if not pd.isna(data_obj):
                            data_str = data_obj.strftime('%Y-%m-%d')
                        else:
                            data_str = None
                except Exception:
                    data_str = None

                # Normalizar valor
                try:
                    if pd.isna(valor_raw):
                        valor = 0.0
                    else:
                        # Remover caracteres especiais e normalizar
                        valor_str = str(valor_raw).replace(',', '.').replace(' ', '').replace('R$', '').replace('$', '')
                        # Remover outros caracteres não numéricos exceto ponto e sinal
                        import re
                        valor_str = re.sub(r'[^\d\.\-\+]', '', valor_str)
                        valor = float(valor_str) if valor_str else 0.0
                except Exception:
                    valor = 0.0

                # Determinar tipo baseado no valor ou coluna tipo
                if tipo_raw and not pd.isna(tipo_raw):
                    tipo_str = str(tipo_raw).upper()
                    if 'CREDIT' in tipo_str or 'ENTRADA' in tipo_str:
                        tipo = 'Entrada'
                        valor = abs(valor)
                    elif 'DEBIT' in tipo_str or 'SAIDA' in tipo_str:
                        tipo = 'Saída'
                        valor = abs(valor)
                    else:
                        tipo = 'Entrada' if valor >= 0 else 'Saída'
                        valor = abs(valor)
                else:
                    # Baseado no sinal do valor
                    tipo = 'Entrada' if valor >= 0 else 'Saída'
                    valor = abs(valor)

                # Buscar possível match no sistema
                match = None
                if data_str and valor > 0:
                    match = Lancamento.query.filter(
                        Lancamento.data == data_str,
                        Lancamento.valor == valor
                    ).first()

                registros.append({
                    'data': data_str,
                    'descricao': descricao[:200],  # Limitar tamanho
                    'valor': valor,
                    'tipo': tipo,
                    'banco': banco,
                    'match_id': match.id if match else None,
                    'match_desc': match.descricao if match else None,
                    'linha': index + 1
                })
                
            except Exception as e:
                flash(f'Erro na linha {index + 1}: {str(e)}', 'warning')
                current_app.logger.error(f'Erro linha {index + 1}: {str(e)}')

        # Salvar dados na sessão para confirmação posterior
        session['registros_import'] = registros
        session['banco_import'] = banco

        # Render preview
        return render_template('financeiro/import_preview.html', 
                             registros=registros,
                             banco=banco,
                             total_registros=len(registros))

    except Exception as e:
        flash(f'Erro ao processar arquivo: {str(e)}', 'danger')
        return redirect(url_for('financeiro.importar_extrato'))

@financeiro_bp.route('/financeiro/conciliacao')
@login_required
def conciliacao():
    """Tela para conciliação manual/automática"""
    # Buscar importados e manuais não conciliados
    importados = Lancamento.query.filter_by(origem='importado', conciliado=False).order_by(Lancamento.data.desc()).all()
    manuais = Lancamento.query.filter_by(origem='manual', conciliado=False).order_by(Lancamento.data.desc()).all()
    # última conciliação para permitir undo
    ultima = ConciliacaoHistorico.query.order_by(ConciliacaoHistorico.data_conciliacao.desc()).first()
    # últimos históricos para permitir desfazer por registro
    historicos = ConciliacaoHistorico.query.order_by(ConciliacaoHistorico.data_conciliacao.desc()).limit(20).all()
    return render_template('financeiro/conciliacao.html', importados=importados, manuais=manuais, ultima_conciliacao=ultima, historicos=historicos)

@financeiro_bp.route('/financeiro/conciliacao/auto', methods=['POST'])
@login_required
def conciliacao_auto():
    """Executa conciliação automática: casa importados com manuais por data e valor exato"""
    try:
        conciliados = 0
        # Buscar importados pendentes
        importados = Lancamento.query.filter_by(origem='importado', conciliado=False).all()
        for imp in importados:
            # tentar encontrar manual correspondente
            match = Lancamento.query.filter_by(origem='manual', conciliado=False, data=imp.data, valor=imp.valor, tipo=imp.tipo).first()
            if match:
                imp.conciliado = True
                match.conciliado = True
                conciliados += 1
                db.session.add(imp)
                db.session.add(match)

        db.session.commit()

        # Registrar histórico
        from flask_login import current_user
        usuario_nome = str(getattr(current_user, 'username', 'system'))
        total_pendentes = Lancamento.query.filter_by(origem='importado', conciliado=False).count()
        historico = ConciliacaoHistorico(
            data_conciliacao=datetime.now(),
            usuario=usuario_nome,
            total_conciliados=conciliados,
            total_pendentes=total_pendentes,
            observacao=f'Conciliação automática: {conciliados} conciliados'
        )
        db.session.add(historico)
        db.session.commit()

        flash(f'Conciliação automática concluída: {conciliados} conciliados.', 'success')
        return redirect(url_for('financeiro.conciliacao'))
    except Exception as e:
        db.session.rollback()
        flash(f'Erro na conciliação automática: {str(e)}', 'danger')
        return redirect(url_for('financeiro.conciliacao'))


def similaridade(a, b):
    """Retorna similaridade entre duas strings 0..1"""
    try:
        return SequenceMatcher(None, (a or '').lower(), (b or '').lower()).ratio()
    except Exception:
        return 0.0


def gerar_sugestoes(importados, manuais, days_window=2, value_tol_pct=0.02, desc_thresh=0.35):
    """Gera uma lista de sugestões de conciliação entre listas de lançamentos.
    Parameters:
      importados, manuais: listas de Lancamento
      days_window: nº de dias para considerar perto da data
      value_tol_pct: tolerância percentual para valores (ex: 0.02 = 2%)
      desc_thresh: limiar mínimo para considerar descrição relevante
    Retorna: lista de dicts {imp: Lancamento, man: Lancamento, score: float, details...}
    """
    suggestions = []
    for imp in importados:
        for man in manuais:
            try:
                # diferença de dias
                delta_days = abs((imp.data - man.data).days) if imp.data and man.data else 9999

                # diferença percentual de valor
                if man.valor and man.valor != 0:
                    value_diff_pct = abs(imp.valor - man.valor) / abs(man.valor)
                else:
                    value_diff_pct = 0 if imp.valor == man.valor else 1

                # similaridade de descrição
                desc_score = similaridade(imp.descricao or '', man.descricao or '')

                # pontuação composta (valores menores são melhores)
                score = 0.0
                # start from description weight
                score += desc_score * 0.6
                # value similarity
                score += max(0, (1 - min(1, value_diff_pct))) * 0.3
                # date proximity bonus
                score += max(0, (1 - min(1, delta_days / max(1, days_window)))) * 0.1

                # filtrar por limiares razoáveis
                if delta_days <= max(7, days_window*3) and value_diff_pct <= 0.5 and desc_score >= 0.05:
                    suggestions.append({
                        'imp_id': imp.id,
                        'man_id': man.id,
                        'imp': imp,
                        'man': man,
                        'score': round(score, 4),
                        'delta_days': delta_days,
                        'value_diff_pct': round(value_diff_pct, 4),
                        'desc_score': round(desc_score, 4)
                    })
            except Exception:
                continue

    suggestions.sort(key=lambda x: x['score'], reverse=True)
    return suggestions


@financeiro_bp.route('/financeiro/conciliacao/sugerir', methods=['POST'])
@login_required
def conciliacao_sugerir():
    """Gera sugestões com base em parâmetros enviados no formulário."""
    try:
        days_window = int(request.form.get('days_window', 2))
        value_tol_pct = float(request.form.get('value_tol_pct', 0.02))
        desc_thresh = float(request.form.get('desc_thresh', 0.35))

        importados = Lancamento.query.filter_by(origem='importado', conciliado=False).all()
        manuais = Lancamento.query.filter_by(origem='manual', conciliado=False).all()

        sugestoes = gerar_sugestoes(importados, manuais, days_window, value_tol_pct, desc_thresh)

        return render_template('financeiro/conciliacao.html', importados=importados, manuais=manuais, sugestoes=sugestoes, params={'days_window':days_window,'value_tol_pct':value_tol_pct,'desc_thresh':desc_thresh})
    except Exception as e:
        flash(f'Erro ao gerar sugestões: {str(e)}', 'danger')
        return redirect(url_for('financeiro.conciliacao'))


@financeiro_bp.route('/financeiro/conciliacao/aceitar', methods=['POST'])
@login_required
def conciliacao_aceitar():
    """Aceita um par sugerido: marca ambos como conciliado e registra histórico"""
    try:
        imp_id = int(request.form.get('imp_id'))
        man_id = int(request.form.get('man_id'))

        imp = Lancamento.query.get_or_404(imp_id)
        man = Lancamento.query.get_or_404(man_id)

        if imp.conciliado or man.conciliado:
            flash('Um dos lançamentos já está conciliado.', 'warning')
            return redirect(url_for('financeiro.conciliacao'))

        # marcar conciliado e persistir
        imp.conciliado = True
        man.conciliado = True
        db.session.add(imp)
        db.session.add(man)
        db.session.commit()

        # registrar histórico e par
        from flask_login import current_user
        usuario_nome = str(getattr(current_user, 'username', 'system'))
        total_pendentes = Lancamento.query.filter_by(origem='importado', conciliado=False).count()
        historico = ConciliacaoHistorico(data_conciliacao=datetime.now(), usuario=usuario_nome, total_conciliados=1, total_pendentes=total_pendentes, observacao=f'Conciliado manual: imp {imp.id} <> man {man.id}')
        db.session.add(historico)
        db.session.commit()

        par = ConciliacaoPar(historico_id=historico.id, imp_id=imp.id, man_id=man.id, score=request.form.get('score', None), regra=request.form.get('regra', 'manual'), usuario=usuario_nome)
        db.session.add(par)
        db.session.commit()

        flash('Par conciliado com sucesso.', 'success')
        return redirect(url_for('financeiro.conciliacao'))
    except Exception as e:
        db.session.rollback()
        flash(f'Erro ao aceitar sugestão: {str(e)}', 'danger')
        return redirect(url_for('financeiro.conciliacao'))


@financeiro_bp.route('/financeiro/conciliacao/aceitar_todos', methods=['POST'])
@login_required
def conciliacao_aceitar_todos():
    """Aceita todos os pares enviados como JSON no corpo da requisição."""
    try:
        import json
        data = None
        if request.is_json:
            data = request.get_json()
        else:
            payload = request.form.get('pairs')
            if payload:
                data = json.loads(payload)

        if not data:
            flash('Nenhum par enviado para conciliação.', 'warning')
            return redirect(url_for('financeiro.conciliacao'))

        conciliados = 0
        pairs_created = []
        for p in data:
            imp = Lancamento.query.get(p.get('imp_id'))
            man = Lancamento.query.get(p.get('man_id'))
            if not imp or not man:
                continue
            if imp.conciliado or man.conciliado:
                continue
            imp.conciliado = True
            man.conciliado = True
            db.session.add(imp)
            db.session.add(man)
            conciliados += 1

        db.session.commit()

        from flask_login import current_user
        usuario_nome = str(getattr(current_user, 'username', 'system'))
        historico = ConciliacaoHistorico(data_conciliacao=datetime.now(), usuario=usuario_nome, total_conciliados=conciliados, total_pendentes=Lancamento.query.filter_by(origem='importado', conciliado=False).count(), observacao=f'Conciliar todos via sugestões: {conciliados} pares')
        db.session.add(historico)
        db.session.commit()

        # registrar pares ligados ao historico
        for p in data:
            try:
                imp_id = int(p.get('imp_id'))
                man_id = int(p.get('man_id'))
            except Exception:
                continue
            par = ConciliacaoPar(historico_id=historico.id, imp_id=imp_id, man_id=man_id, score=p.get('score', None), regra='sugestao', usuario=usuario_nome)
            db.session.add(par)
        db.session.commit()

        flash(f'{conciliados} pares conciliados.', 'success')
        return redirect(url_for('financeiro.conciliacao'))
    except Exception as e:
        db.session.rollback()
        flash(f'Erro ao aceitar todos: {str(e)}', 'danger')
        return redirect(url_for('financeiro.conciliacao'))


@financeiro_bp.route('/financeiro/conciliacao/undo_ultimo', methods=['POST'])
@login_required
def conciliacao_undo_ultimo():
    """Desfaz a última conciliação registrada (reverte conciliado e remove pares/historico)."""
    try:
        ultima = ConciliacaoHistorico.query.order_by(ConciliacaoHistorico.data_conciliacao.desc()).first()
        if not ultima:
            flash('Não há conciliações para desfazer.', 'warning')
            return redirect(url_for('financeiro.conciliacao'))

        # obter pares ligados
        pares = ConciliacaoPar.query.filter_by(historico_id=ultima.id).all()
        revertidos = 0
        for par in pares:
            imp = Lancamento.query.get(par.imp_id)
            man = Lancamento.query.get(par.man_id)
            if imp and imp.conciliado:
                imp.conciliado = False
                db.session.add(imp)
                revertidos += 1
            if man and man.conciliado:
                man.conciliado = False
                db.session.add(man)
                revertidos += 1

        # remover registros de pares e historico
        for par in pares:
            db.session.delete(par)

        db.session.delete(ultima)
        db.session.commit()

        flash(f'Última conciliação desfeita. {revertidos} marcações revertidas.', 'success')
        return redirect(url_for('financeiro.conciliacao'))
    except Exception as e:
        db.session.rollback()
        flash(f'Erro ao desfazer última conciliação: {str(e)}', 'danger')
        return redirect(url_for('financeiro.conciliacao'))


@financeiro_bp.route('/financeiro/conciliacao/export_pairs', methods=['POST'])
@login_required
def conciliacao_export_pairs():
    """Exporta os pares selecionados como CSV para download."""
    try:
        import json
        payload = None
        if request.is_json:
            payload = request.get_json()
        else:
            payload = request.form.get('pairs')
            if payload:
                payload = json.loads(payload)

        if not payload:
            flash('Nenhum par selecionado para exportação.', 'warning')
            return redirect(url_for('financeiro.conciliacao'))

        # criar CSV em memória
        si = io.StringIO()
        writer = csv.writer(si)
        writer.writerow(['imp_id', 'man_id', 'imp_data', 'man_data', 'imp_valor', 'man_valor', 'score'])
        for p in payload:
            imp = Lancamento.query.get(p.get('imp_id'))
            man = Lancamento.query.get(p.get('man_id'))
            writer.writerow([
                p.get('imp_id'),
                p.get('man_id'),
                imp.data.isoformat() if imp and imp.data else '',
                man.data.isoformat() if man and man.data else '',
                f"{imp.valor:.2f}" if imp else '',
                f"{man.valor:.2f}" if man else '',
                p.get('score', '')
            ])

        output = si.getvalue()
        mem = io.BytesIO()
        mem.write(output.encode('utf-8'))
        mem.seek(0)

        filename = f"conciliacao_pares_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        return send_file(mem, mimetype='text/csv', as_attachment=True, download_name=filename)

    except Exception as e:
        flash(f'Erro ao exportar pares: {str(e)}', 'danger')
        return redirect(url_for('financeiro.conciliacao'))


@financeiro_bp.route('/financeiro/conciliacao/undo/<int:historico_id>', methods=['POST'])
@login_required
def conciliacao_undo(historico_id):
    """Desfaz uma conciliação específica pelo id do histórico."""
    try:
        historico = ConciliacaoHistorico.query.get_or_404(historico_id)
        pares = ConciliacaoPar.query.filter_by(historico_id=historico.id).all()
        revertidos = 0
        for par in pares:
            imp = Lancamento.query.get(par.imp_id)
            man = Lancamento.query.get(par.man_id)
            if imp and imp.conciliado:
                imp.conciliado = False
                db.session.add(imp)
                revertidos += 1
            if man and man.conciliado:
                man.conciliado = False
                db.session.add(man)
                revertidos += 1

        for par in pares:
            db.session.delete(par)

        db.session.delete(historico)
        db.session.commit()

        flash(f'Conciliação {historico_id} desfeita. {revertidos} marcações revertidas.', 'success')
        return redirect(url_for('financeiro.conciliacao'))
    except Exception as e:
        db.session.rollback()
        flash(f'Erro ao desfazer conciliação {historico_id}: {str(e)}', 'danger')
        return redirect(url_for('financeiro.conciliacao'))


@financeiro_bp.route('/financeiro/importar/confirmar-old', methods=['POST'])
@login_required
def confirmar_importacao_DEPRECATED():
    """Confirma e processa a importação dos registros"""
    try:
        import json
        
        # Recuperar dados da sessão
        registros = session.get('registros_import', [])
        banco = session.get('banco_import', 'generico')
        ignorar_duplicatas = request.form.get('ignorar_duplicatas') == 'on'
        
        if not registros:
            flash('Nenhum registro para importar.', 'warning')
            return redirect(url_for('financeiro.importar_extrato'))
        
        importados = 0
        ignorados = 0
        erros = 0
        
        for registro in registros:
            try:
                # Verificar se é duplicata
                if registro.get('match_id') and not ignorar_duplicatas:
                    ignorados += 1
                    continue
                
                # Validar dados obrigatórios
                if not registro.get('data') or not registro.get('valor'):
                    erros += 1
                    continue
                
                # Criar novo lançamento
                novo_lancamento = Lancamento(
                    data=registro['data'],
                    descricao=registro['descricao'][:500],  # Limitar tamanho
                    valor=abs(float(registro['valor'])),
                    tipo=registro['tipo'],
                    categoria='Importação Bancária',
                    observacoes=f'Importado do banco {banco.upper()}',
                    banco_origem=banco,
                    documento_ref=f"Import_{banco}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                )
                
                db.session.add(novo_lancamento)
                importados += 1
                
            except Exception as e:
                erros += 1
                current_app.logger.error(f'Erro ao importar registro: {str(e)}')
        
        # Salvar no banco
        try:
            db.session.commit()
            
            # Limpar sessão
            session.pop('registros_import', None)
            session.pop('banco_import', None)
            
            # Mensagem de sucesso
            msg = f'Importação concluída: {importados} registros importados'
            if ignorados > 0:
                msg += f', {ignorados} duplicatas ignoradas'
            if erros > 0:
                msg += f', {erros} registros com erro'
            
            flash(msg, 'success')
            return redirect(url_for('financeiro.lancamentos'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao salvar no banco: {str(e)}', 'danger')
            return redirect(url_for('financeiro.importar_extrato'))
        
    except Exception as e:
        flash(f'Erro ao processar importação: {str(e)}', 'danger')
        return redirect(url_for('financeiro.importar_extrato'))


@financeiro_bp.route('/financeiro/importar/preview', methods=['POST'])
@login_required
def importar_extrato_preview():
    """Preview dos registros importados e tentativa de sugestão de conciliação"""
    try:
        try:
            import pandas as pd
        except ImportError:
            flash('Pandas não está instalado no ambiente. A importação de extratos requer pandas.', 'warning')
            return redirect(url_for('financeiro.importar_extrato'))
        
        # Pegar arquivo e banco selecionado
        file = request.files.get('arquivo') or request.files.get('file')
        banco = request.form.get('banco', 'generico')
        
        if not file or file.filename == '':
            flash('Selecione um arquivo CSV ou XLSX para importar.', 'danger')
            return redirect(url_for('financeiro.importar_extrato'))

        # Ler arquivo baseado na extensão
        filename = file.filename.lower()
        try:
            if filename.endswith('.csv'):
                # Tentar diferentes encodings para CSV
                file.seek(0)
                content = file.read()
                
                # Tentar UTF-8 primeiro
                try:
                    content_str = content.decode('utf-8')
                    file_obj = io.StringIO(content_str)
                    df = pd.read_csv(file_obj, sep=';')
                    if len(df.columns) == 1:
                        file_obj = io.StringIO(content_str)
                        df = pd.read_csv(file_obj, sep=',')
                except UnicodeDecodeError:
                    # Tentar Latin-1
                    content_str = content.decode('latin-1')
                    file_obj = io.StringIO(content_str)
                    df = pd.read_csv(file_obj, sep=';')
                    if len(df.columns) == 1:
                        file_obj = io.StringIO(content_str)
                        df = pd.read_csv(file_obj, sep=',')
            else:
                df = pd.read_excel(file)
        except Exception as e:
            flash(f'Erro ao ler arquivo: {str(e)}', 'danger')
            return redirect(url_for('financeiro.importar_extrato'))

        # Aplicar mapeamento específico do banco com detecção inteligente
        df_original = df.copy()
        
        def encontrar_coluna(df, palavras_chave):
            """Encontra coluna baseada em palavras-chave"""
            for col in df.columns:
                col_lower = str(col).lower().replace(' ', '').replace('_', '')
                for palavra in palavras_chave:
                    if palavra.lower().replace(' ', '') in col_lower:
                        return col
            return None
        
        # Mapeamento inteligente baseado no banco
        if banco == 'pagbank':
            # Palavras-chave específicas do PagBank
            data_cols = ['data', 'datatransacao', 'dataoperacao', 'date']
            desc_cols = ['descricao', 'descricaotransacao', 'historico', 'description', 'memo']
            valor_cols = ['valor', 'valortransacao', 'amount', 'montante', 'quantia']
            tipo_cols = ['tipo', 'tipotransacao', 'credito', 'debito', 'natureza']
        elif banco == 'bradesco':
            data_cols = ['data', 'dataoperacao', 'date']
            desc_cols = ['descricao', 'historico', 'memo', 'description']
            valor_cols = ['valor', 'amount', 'montante']
            tipo_cols = ['tipo', 'natureza', 'credito', 'debito']
        else:
            # Mapeamento genérico
            data_cols = ['data', 'date', 'fecha']
            desc_cols = ['descricao', 'description', 'memo', 'historico']
            valor_cols = ['valor', 'value', 'amount', 'montante']
            tipo_cols = ['tipo', 'type', 'natureza']
        
        # Encontrar colunas automaticamente
        col_data = encontrar_coluna(df, data_cols)
        col_desc = encontrar_coluna(df, desc_cols)
        col_valor = encontrar_coluna(df, valor_cols)
        col_tipo = encontrar_coluna(df, tipo_cols)
        
        # Verificar se encontrou pelo menos data, descrição e valor
        if not all([col_data, col_desc, col_valor]):
            colunas_encontradas = [f"'{col}'" for col in df.columns]
            flash(f'Arquivo sem colunas essenciais. Colunas encontradas: {", ".join(colunas_encontradas)}. '
                  f'Precisa ter colunas relacionadas a: data, descrição e valor', 'danger')
            return redirect(url_for('financeiro.importar_extrato'))

        # Preparar lista de registros
        registros = []
        for index, row in df.iterrows():
            try:
                data_raw = row.get(col_data)
                descricao = str(row.get(col_desc) or '')
                valor_raw = row.get(col_valor)
                tipo_raw = row.get(col_tipo) if col_tipo else None
                
                # Normalizar data
                try:
                    if pd.isna(data_raw):
                        data_str = None
                    else:
                        # Tentar vários formatos de data
                        data_obj = pd.to_datetime(data_raw, dayfirst=True, errors='coerce')
                        if pd.isna(data_obj):
                            # Tentar formato americano
                            data_obj = pd.to_datetime(data_raw, dayfirst=False, errors='coerce')
                        
                        if not pd.isna(data_obj):
                            data_str = data_obj.strftime('%Y-%m-%d')
                        else:
                            data_str = None
                except Exception:
                    data_str = None

                # Normalizar valor
                try:
                    if pd.isna(valor_raw):
                        valor = 0.0
                    else:
                        # Remover caracteres especiais e normalizar
                        valor_str = str(valor_raw).replace(',', '.').replace(' ', '').replace('R$', '').replace('$', '')
                        # Remover outros caracteres não numéricos exceto ponto e sinal
                        import re
                        valor_str = re.sub(r'[^\d\.\-\+]', '', valor_str)
                        valor = float(valor_str) if valor_str else 0.0
                except Exception:
                    valor = 0.0

                # Determinar tipo baseado no valor ou coluna tipo
                if tipo_raw and not pd.isna(tipo_raw):
                    tipo_str = str(tipo_raw).upper()
                    if 'CREDIT' in tipo_str or 'ENTRADA' in tipo_str:
                        tipo = 'Entrada'
                        valor = abs(valor)
                    elif 'DEBIT' in tipo_str or 'SAIDA' in tipo_str:
                        tipo = 'Saída'
                        valor = abs(valor)
                    else:
                        tipo = 'Entrada' if valor >= 0 else 'Saída'
                        valor = abs(valor)
                else:
                    # Baseado no sinal do valor
                    tipo = 'Entrada' if valor >= 0 else 'Saída'
                    valor = abs(valor)

                # Buscar possível match no sistema
                match = None
                if data_str and valor > 0:
                    match = Lancamento.query.filter(
                        Lancamento.data == data_str,
                        Lancamento.valor == valor
                    ).first()

                registros.append({
                    'data': data_str,
                    'descricao': descricao[:200],  # Limitar tamanho
                    'valor': valor,
                    'tipo': tipo,
                    'banco': banco,
                    'match_id': match.id if match else None,
                    'match_desc': match.descricao if match else None,
                    'linha': index + 1
                })
                
            except Exception as e:
                flash(f'Erro na linha {index + 1}: {str(e)}', 'warning')
                current_app.logger.error(f'Erro linha {index + 1}: {str(e)}')

        # Salvar dados na sessão para confirmação posterior
        session['registros_import'] = registros
        session['banco_import'] = banco

        # Render preview
        return render_template('financeiro/import_preview.html', 
                             registros=registros,
                             banco=banco,
                             total_registros=len(registros))

    except Exception as e:
        flash(f'Erro ao processar arquivo: {str(e)}', 'danger')
        return redirect(url_for('financeiro.importar_extrato'))


@financeiro_bp.route('/financeiro/importar/confirmar', methods=['POST'])
@login_required
def importar_extrato_confirmar():
    """Confirma importação: insere lançamentos não casados e registra conciliação"""
    print("DEBUG: Função importar_extrato_confirmar iniciada")
    
    dados = request.form.get('registros')
    print(f"DEBUG: Dados recebidos: {bool(dados)}")
    
    if not dados:
        flash('Nenhum registro para importar.', 'warning')
        return redirect(url_for('financeiro.importar_extrato'))

    try:
        import json
        registros = json.loads(dados)
        print(f"DEBUG: {len(registros)} registros para processar")
        
        criados = 0
        conciliados = 0
        
        # Processar cada registro
        for i, r in enumerate(registros):
            try:
                print(f"DEBUG: Processando registro {i+1}")
                print(f"DEBUG: Registro completo: {r}")
                
                if r.get('match_id'):
                    print(f"DEBUG: Registro {i+1} tem match_id, pulando para conciliação")
                    conciliados += 1
                    continue
                    
                # Processar data
                data_obj = date.today()
                if r.get('data'):
                    try:
                        data_obj = datetime.strptime(r.get('data'), '%Y-%m-%d').date()
                    except:
                        pass  # Usa data atual se houver erro
                
                # Processar valor e tipo
                valor_raw = r.get('valor', '0')
                valor_float = float(str(valor_raw).replace(',', '.'))
                valor_abs = abs(valor_float)
                
                # USAR O TIPO QUE VEM DO PREVIEW, NÃO RECALCULAR!
                tipo = r.get('tipo', 'Entrada')  # Usar tipo do preview
                
                print(f"DEBUG: Registro {i+1} - Valor raw: {valor_raw}, Float: {valor_float}, Abs: {valor_abs}, Tipo do preview: {tipo}")
                
                if tipo == 'Saída':
                    print(f"DEBUG: *** SAÍDA DETECTADA *** - Registro {i+1}: {r.get('descricao', 'Sem descrição')}")
                
                # Criar lançamento
                novo = Lancamento(
                    data=data_obj,
                    tipo=tipo,
                    categoria='Importação',
                    descricao=str(r.get('descricao', '')[:190]),  # Limitar tamanho
                    valor=valor_abs,
                    conta='Extrato',
                    observacoes='Importado via extrato',
                    origem='importado',
                    conciliado=False
                )
                
                print(f"DEBUG: Objeto criado - Tipo: {novo.tipo}, Valor: {novo.valor}, Desc: {novo.descricao[:30]}...")
                
                if novo.tipo == 'Saída':
                    print(f"DEBUG: *** SALVANDO SAÍDA *** - {novo.descricao[:50]}")
                
                db.session.add(novo)
                criados += 1
                print(f"DEBUG: Lançamento {i+1} adicionado à sessão - TIPO: {tipo}")
                
            except Exception as e:
                print(f"DEBUG: Erro no registro {i+1}: {e}")
                import traceback
                traceback.print_exc()
                continue  # Pula este registro e continua
        
        print(f"DEBUG: Fazendo commit de {criados} registros...")
        db.session.commit()
        print(f"DEBUG: Commit realizado")
        
        # Verificar resultado imediatamente após commit
        total_importados = Lancamento.query.filter_by(origem='importado').count()
        entradas_importadas = Lancamento.query.filter_by(origem='importado', tipo='Entrada').count()  
        saidas_importadas = Lancamento.query.filter_by(origem='importado', tipo='Saída').count()
        
        print(f"DEBUG: Total importados no banco: {total_importados}")
        print(f"DEBUG: Entradas importadas: {entradas_importadas}")
        print(f"DEBUG: Saídas importadas: {saidas_importadas}")
        
        # Verificar últimos registros salvos
        ultimos_salvos = Lancamento.query.filter_by(origem='importado').order_by(Lancamento.id.desc()).limit(5).all()
        print(f"DEBUG: Últimos 5 salvos:")
        for lanc in ultimos_salvos:
            print(f"   ID {lanc.id}: {lanc.tipo} - {lanc.descricao[:30]}... - R$ {lanc.valor}")
        
        # Mensagem de sucesso
        mensagem = f'Importação concluída: {criados} lançamentos criados'
        if conciliados > 0:
            mensagem += f', {conciliados} conciliados'
        
        flash(mensagem, 'success')
        print(f"DEBUG: Redirecionando para lista de lançamentos")
        return redirect(url_for('financeiro.lista_lancamentos'))

    except Exception as e:
        print(f"DEBUG: Erro na função: {e}")
        try:
            db.session.rollback()
        except:
            pass
        flash(f'Erro ao processar importação: {str(e)}', 'danger')
        return redirect(url_for('financeiro.lista_lancamentos'))


@financeiro_bp.route('/debug/importacao')
@login_required 
def debug_importacao():
    """Função temporária para debug da importação"""
    from flask import jsonify
    
    # Verificar quantos lançamentos importados existem
    total_importados = Lancamento.query.filter_by(origem='importado').count()
    entradas_importadas = Lancamento.query.filter_by(origem='importado', tipo='Entrada').count()
    saidas_importadas = Lancamento.query.filter_by(origem='importado', tipo='Saída').count()
    
    # Pegar últimos 10 lançamentos importados
    ultimos = Lancamento.query.filter_by(origem='importado').order_by(Lancamento.id.desc()).limit(10).all()
    
    dados_ultimos = []
    for lanc in ultimos:
        dados_ultimos.append({
            'id': lanc.id,
            'data': lanc.data.strftime('%Y-%m-%d') if lanc.data else None,
            'tipo': lanc.tipo,
            'descricao': lanc.descricao,
            'valor': float(lanc.valor),
            'origem': lanc.origem
        })
    
    resultado = {
        'total_importados': total_importados,
        'entradas': entradas_importadas, 
        'saidas': saidas_importadas,
        'ultimos_registros': dados_ultimos
    }
    
    return jsonify(resultado)


@financeiro_bp.route('/financeiro/salvar', methods=['POST'])
@login_required
def salvar_lancamento():
    """Salva novo lançamento ou atualiza lançamento existente"""
    try:
        # Captura dados do formulário
        lancamento_id = request.form.get('id')
        data_str = request.form.get('data')
        tipo = request.form.get('tipo')
        categoria = request.form.get('categoria', '').strip()
        descricao = request.form.get('descricao', '').strip()
        valor_str = request.form.get('valor', '').strip()
        conta = request.form.get('conta')
        observacoes_raw = request.form.get('observacoes', '').strip()
        projeto_id_str = request.form.get('projeto_id', '').strip()
        
        # Processar projeto_id
        projeto_id = None
        if projeto_id_str and projeto_id_str.isdigit():
            projeto_id = int(projeto_id_str)
            # Validar se o projeto existe e está ativo
            projeto = Projeto.query.filter_by(id=projeto_id, status='Ativo').first()
            if not projeto:
                flash('Projeto selecionado inválido ou inativo!', 'danger')
                return redirect(url_for('financeiro.novo_lancamento'))
        
        # Validar se projeto é obrigatório para DESTINAÇÃO e GASTO PROJETO
        if categoria in ['DESTINAÇÃO', 'GASTO PROJETO'] and not projeto_id:
            flash('Projeto é obrigatório para lançamentos de DESTINAÇÃO e GASTO PROJETO!', 'danger')
            return redirect(url_for('financeiro.novo_lancamento'))
        
        # Limpar observações - garantir que None ou strings vazias sejam tratadas adequadamente
        observacoes = None
        if observacoes_raw and observacoes_raw.lower() != 'none' and observacoes_raw.strip():
            observacoes = observacoes_raw
        
        # Processar upload de comprovante
        file = request.files.get('comprovante')
        caminho_comprovante = None
        if file:
            caminho_comprovante = processar_upload_comprovante(file)
        
        # Validações básicas
        if not tipo or tipo not in ['Entrada', 'Saída']:
            flash('Tipo é obrigatório (Entrada ou Saída)!', 'danger')
            return redirect(url_for('financeiro.novo_lancamento'))
        
        if not valor_str:
            flash('Valor é obrigatório!', 'danger')
            return redirect(url_for('financeiro.novo_lancamento'))
        
        # Conversão de valor
        try:
            # Remove formatação brasileira e converte para float
            valor_limpo = valor_str.replace('R$', '').replace('.', '').replace(',', '.').strip()
            valor = float(valor_limpo)
            if valor <= 0:
                flash('Valor deve ser maior que zero!', 'danger')
                return redirect(url_for('financeiro.novo_lancamento'))
        except ValueError:
            flash('Valor inválido! Use formato: 1.000,50', 'danger')
            return redirect(url_for('financeiro.novo_lancamento'))
        
        # Conversão de data
        data_obj = None
        if data_str:
            try:
                data_obj = datetime.strptime(data_str, '%Y-%m-%d').date()
            except ValueError:
                flash('Data inválida!', 'danger')
                return redirect(url_for('financeiro.novo_lancamento'))
        else:
            data_obj = date.today()

        if lancamento_id:
            # Atualizar lançamento existente
            lancamento = Lancamento.query.get_or_404(lancamento_id)
            lancamento.data = data_obj
            lancamento.tipo = tipo
            lancamento.categoria = categoria if categoria else None
            lancamento.descricao = descricao if descricao else None
            lancamento.valor = valor
            lancamento.conta = conta
            lancamento.observacoes = observacoes
            lancamento.projeto_id = projeto_id  # Atualizar projeto
            # Atualizar comprovante apenas se um novo foi enviado
            if caminho_comprovante:
                lancamento.comprovante = caminho_comprovante
            flash('Lançamento atualizado com sucesso!', 'success')
            
            # Após editar, salvar e redirecionar para a lista de lançamentos
            # PRESERVANDO OS FILTROS ATIVOS
            db.session.commit()
            filtros_ativos = obter_filtros_ativos()
            return redirect(url_for('financeiro.lista_lancamentos', **filtros_ativos))
        else:
            # Validação de duplicidade
            duplicado = Lancamento.query.filter_by(
                data=data_obj,
                tipo=tipo,
                categoria=categoria if categoria else None,
                descricao=descricao if descricao else None,
                valor=valor,
                conta=conta
            ).first()
            if duplicado:
                flash('Já existe um lançamento igual cadastrado! Verifique os dados.', 'danger')
                filtros_ativos = obter_filtros_ativos()
                return redirect(url_for('financeiro.novo_lancamento', **filtros_ativos))
            # Criar novo lançamento
            novo_lancamento = Lancamento(
                data=data_obj,
                tipo=tipo,
                categoria=categoria if categoria else None,
                descricao=descricao if descricao else None,
                valor=valor,
                conta=conta,
                observacoes=observacoes,
                comprovante=caminho_comprovante,
                projeto_id=projeto_id  # Vincular ao projeto
            )
            novo_lancamento.origem = 'manual'
            db.session.add(novo_lancamento)
            flash('Lançamento cadastrado com sucesso! Você pode continuar lançando ou clicar em "Voltar" para ver a lista.', 'success')
            
            # Para novos lançamentos, salvar e continuar no formulário
            # PRESERVANDO OS FILTROS ATIVOS NA URL
            db.session.commit()
            filtros_ativos = obter_filtros_ativos()
            return redirect(url_for('financeiro.novo_lancamento', **filtros_ativos))
        
    except Exception as e:
        db.session.rollback()
        flash(f'Erro ao salvar lançamento: {str(e)}', 'danger')
        filtros_ativos = obter_filtros_ativos()
        return redirect(url_for('financeiro.novo_lancamento', **filtros_ativos))

@financeiro_bp.route('/financeiro/editar/<int:id>')
@login_required
def editar_lancamento(id):
    """Carrega dados do lançamento para edição"""
    try:
        lancamento = Lancamento.query.get_or_404(id)
        # Buscar projetos ativos para o dropdown
        projetos = Projeto.query.filter_by(status='Ativo').order_by(Projeto.nome).all()
        
        # Capturar filtros ativos para preservá-los após salvar
        filtros_ativos = obter_filtros_ativos()
        
        return render_template('financeiro/cadastro_lancamento.html', 
                             lancamento=lancamento, 
                             projetos=projetos,
                             filtros_ativos=filtros_ativos)
    except Exception as e:
        flash(f'Erro ao carregar dados do lançamento: {str(e)}', 'danger')
        filtros_ativos = obter_filtros_ativos()
        return redirect(url_for('financeiro.lista_lancamentos', **filtros_ativos))

@financeiro_bp.route('/financeiro/excluir/<int:id>')
@login_required
def excluir_lancamento(id):
    """Exclui um lançamento"""
    try:
        lancamento = Lancamento.query.get_or_404(id)
        descricao_lancamento = lancamento.descricao or f"{lancamento.tipo} de {lancamento.valor_formatado}"
        
        db.session.delete(lancamento)
        db.session.commit()
        
        flash(f'Lançamento excluído', 'info')
        
    except Exception as e:
        db.session.rollback()
        flash(f'Erro ao excluir lançamento: {str(e)}', 'danger')
    
    # PRESERVAR FILTROS APÓS EXCLUIR
    filtros_ativos = obter_filtros_ativos()
    return redirect(url_for('financeiro.lista_lancamentos', **filtros_ativos))

@financeiro_bp.route('/financeiro/excluir-comprovante/<int:id>', methods=['POST'])
@login_required
def excluir_comprovante(id):
    """Exclui apenas o comprovante de um lançamento"""
    try:
        import os
        from flask import current_app
        
        lancamento = Lancamento.query.get_or_404(id)
        
        if lancamento.tem_comprovante():
            # Tentar excluir o arquivo físico
            try:
                caminho_completo = os.path.join(current_app.root_path, lancamento.comprovante.lstrip('/'))
                if os.path.exists(caminho_completo):
                    os.remove(caminho_completo)
            except Exception as e:
                current_app.logger.warning(f'Erro ao excluir arquivo físico: {str(e)}')
            
            # Limpar referência no banco
            lancamento.comprovante = None
            db.session.commit()
            
            flash('Comprovante excluído com sucesso!', 'success')
        else:
            flash('Este lançamento não possui comprovante.', 'warning')
        
    except Exception as e:
        db.session.rollback()
        flash(f'Erro ao excluir comprovante: {str(e)}', 'danger')
    
    # Redirecionar de volta para a edição
    return redirect(url_for('financeiro.editar_lancamento', id=id))

@financeiro_bp.route('/financeiro/upload-comprovantes/<int:id>', methods=['POST'])
@login_required
def upload_comprovantes(id):
    """Upload de múltiplos comprovantes para um lançamento"""
    try:
        from app.financeiro.comprovante_model import Comprovante
        import uuid
        
        lancamento = Lancamento.query.get_or_404(id)
        
        # Debug - verificar o que está vindo no request
        current_app.logger.info(f">>> Upload comprovantes - Request.files: {request.files}")
        current_app.logger.info(f">>> Request.files.keys(): {request.files.keys()}")
        
        # Verificar se há arquivos (tentar ambas as formas)
        files = None
        if 'comprovantes[]' in request.files:
            files = request.files.getlist('comprovantes[]')
            current_app.logger.info(f">>> Encontrado comprovantes[] - Total: {len(files)}")
        elif 'comprovantes_multiplos' in request.files:
            files = request.files.getlist('comprovantes_multiplos')
            current_app.logger.info(f">>> Encontrado comprovantes_multiplos - Total: {len(files)}")
        
        if not files:
            current_app.logger.warning(">>> Nenhum arquivo encontrado no request")
            flash('Nenhum arquivo selecionado', 'warning')
            return redirect(url_for('financeiro.editar_lancamento', id=id))
        
        if files[0].filename == '':
            current_app.logger.warning(">>> Primeiro arquivo está vazio")
            flash('Nenhum arquivo selecionado', 'warning')
            return redirect(url_for('financeiro.editar_lancamento', id=id))
        
        arquivos_salvos = 0
        erros = []
        
        for file in files:
            if file and file.filename != '':
                current_app.logger.info(f">>> Processando arquivo: {file.filename}")
                
                if not allowed_file(file.filename):
                    erros.append(f"{file.filename} - formato não permitido")
                    current_app.logger.warning(f">>> Arquivo rejeitado: {file.filename}")
                    continue
                
                try:
                    # Gerar nome único
                    filename = secure_filename(file.filename)
                    nome_unico = f"{uuid.uuid4().hex}_{filename}"
                    
                    # Criar diretório se não existir
                    upload_dir = os.path.join(current_app.root_path, 'static', 'uploads', 'comprovantes')
                    os.makedirs(upload_dir, exist_ok=True)
                    
                    # Salvar arquivo
                    file_path = os.path.join(upload_dir, nome_unico)
                    file.save(file_path)
                    current_app.logger.info(f">>> Arquivo salvo: {file_path}")
                    
                    # Obter informações do arquivo
                    file_size = os.path.getsize(file_path)
                    
                    # Criar registro no banco
                    comprovante = Comprovante(
                        lancamento_id=lancamento.id,
                        arquivo=f"/static/uploads/comprovantes/{nome_unico}",
                        nome_original=filename,
                        tamanho=file_size,
                        tipo_mime=file.content_type
                    )
                    db.session.add(comprovante)
                    arquivos_salvos += 1
                    current_app.logger.info(f">>> Comprovante adicionado ao banco: {filename}")
                    
                except Exception as e:
                    erro_msg = f"{file.filename} - {str(e)}"
                    erros.append(erro_msg)
                    current_app.logger.error(f'>>> Erro ao processar arquivo {file.filename}: {str(e)}')
                    import traceback
                    traceback.print_exc()
                    continue
        
        if arquivos_salvos > 0:
            db.session.commit()
            current_app.logger.info(f">>> Total de {arquivos_salvos} comprovantes salvos com sucesso")
            flash(f'{arquivos_salvos} comprovante(s) adicionado(s) com sucesso!', 'success')
        else:
            current_app.logger.warning(">>> Nenhum arquivo foi salvo")
            flash('Nenhum arquivo foi processado', 'warning')
        
        if erros:
            for erro in erros:
                flash(f'Erro: {erro}', 'danger')
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'>>> Erro geral no upload de comprovantes: {str(e)}')
        import traceback
        traceback.print_exc()
        flash(f'Erro ao fazer upload: {str(e)}', 'danger')
    
    return redirect(url_for('financeiro.editar_lancamento', id=id))

@financeiro_bp.route('/financeiro/excluir-comprovante-multiplo/<int:comprovante_id>', methods=['POST'])
@login_required
def excluir_comprovante_multiplo(comprovante_id):
    """Exclui um comprovante específico da lista de múltiplos comprovantes"""
    try:
        from app.financeiro.comprovante_model import Comprovante
        import os
        
        comprovante = Comprovante.query.get_or_404(comprovante_id)
        lancamento_id = comprovante.lancamento_id
        
        # Tentar excluir o arquivo físico
        try:
            caminho_completo = os.path.join(current_app.root_path, comprovante.arquivo.lstrip('/'))
            if os.path.exists(caminho_completo):
                os.remove(caminho_completo)
        except Exception as e:
            current_app.logger.warning(f'Erro ao excluir arquivo físico: {str(e)}')
        
        # Excluir registro do banco
        db.session.delete(comprovante)
        db.session.commit()
        
        flash('Comprovante excluído com sucesso!', 'success')
        
    except Exception as e:
        db.session.rollback()
        flash(f'Erro ao excluir comprovante: {str(e)}', 'danger')
    
    return redirect(url_for('financeiro.editar_lancamento', id=lancamento_id))

@financeiro_bp.route('/financeiro/relatorio')
@login_required
def gerar_relatorio():
    """Tela centralizada dos relatórios financeiros com seletor de apresentação."""
    try:
        tipo_relatorio = request.args.get('tipo_relatorio', 'gerencial')
        contexto = gerar_dados_relatorio(tipo_relatorio)
        return render_template(contexto['template_relatorio'], **contexto)
    except Exception as e:
        flash(f'Erro ao gerar relatório: {str(e)}', 'danger')
        return redirect(url_for('financeiro.lista_lancamentos'))


@financeiro_bp.route('/financeiro/relatorio/justificativa', methods=['POST'])
@login_required
def salvar_justificativa_relatorio():
    """Salva ou restaura a justificativa contábil por mes/ano/tipo de relatório."""
    tipo_relatorio = (request.form.get('tipo_relatorio') or 'gerencial').strip().lower()
    if tipo_relatorio not in {'gerencial', 'sede', 'auditoria'}:
        tipo_relatorio = 'gerencial'

    hoje = datetime.now()
    mes = request.form.get('mes', type=int) or hoje.month
    ano = request.form.get('ano', type=int) or hoje.year
    acao = (request.form.get('acao') or 'salvar').strip().lower()

    try:
        if acao == 'restaurar':
            removida = ObservacaoRelatorio.excluir_texto(mes, ano, tipo_relatorio=tipo_relatorio)
            db.session.commit()
            if removida:
                flash('Texto automático restaurado com sucesso.', 'success')
            else:
                flash('Já estava usando o texto automático para este período.', 'info')
        else:
            observacao_texto = (request.form.get('observacao_repasse_sede') or '').strip()
            if not observacao_texto:
                flash('Informe um texto para salvar a justificativa.', 'warning')
            else:
                registro = ObservacaoRelatorio.salvar_texto(mes, ano, observacao_texto, tipo_relatorio=tipo_relatorio)
                if registro is None:
                    flash('A justificativa não pôde ser salva agora, mas o relatório seguirá com o texto automático.', 'warning')
                else:
                    db.session.commit()
                    flash('Justificativa contábil salva com sucesso.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Erro ao atualizar justificativa: {str(e)}', 'danger')

    return redirect(url_for('financeiro.gerar_relatorio', tipo_relatorio=tipo_relatorio, mes=mes, ano=ano))


@financeiro_bp.route('/financeiro/relatorio/pdf')
@login_required
def relatorio_pdf():
    """Gera PDF a partir do template selecionado, preservando as regras financeiras."""
    try:
        from weasyprint import HTML

        tipo_relatorio = request.args.get('tipo_relatorio', 'gerencial')
        contexto = gerar_dados_relatorio(tipo_relatorio)
        logo_pdf_src = None
        logo_relativo = str(contexto.get('dados_igreja', {}).get('logo', '') or '').replace('\\', '/').lstrip('/')
        if logo_relativo:
            caminho_logo = Path(current_app.static_folder) / logo_relativo
            if caminho_logo.exists():
                logo_pdf_src = caminho_logo.resolve().as_uri()
            else:
                fallback_logo = Path(current_app.static_folder) / 'logo_obpc_novo.jpg'
                if fallback_logo.exists():
                    logo_pdf_src = fallback_logo.resolve().as_uri()

        html = render_template(contexto['template_relatorio'], modo_pdf=True, logo_pdf_src=logo_pdf_src, **contexto)

        pdf_buffer = io.BytesIO()
        HTML(string=html, base_url=request.url_root).write_pdf(pdf_buffer)
        pdf_buffer.seek(0)

        nome_arquivo = gerar_nome_arquivo_relatorio(tipo_relatorio, contexto['mes'], contexto['ano'])
        return send_file(
            pdf_buffer,
            mimetype='application/pdf',
            as_attachment=False,
            download_name=nome_arquivo
        )
    except Exception as e:
        flash(f'Erro ao gerar PDF do relatório: {str(e)}', 'danger')
        return redirect(url_for('financeiro.gerar_relatorio', tipo_relatorio=request.args.get('tipo_relatorio', 'gerencial'), mes=request.args.get('mes'), ano=request.args.get('ano')))

@financeiro_bp.route('/financeiro/debug-outras-ofertas')
@login_required
def debug_outras_ofertas():
    """Debug para identificar problema nas Outras Ofertas"""
    mes = request.args.get('mes', type=int, default=1)
    ano = request.args.get('ano', type=int, default=2026)
    
    # Buscar lançamentos
    lancamentos = Lancamento.query.filter(
        extract('month', Lancamento.data) == mes,
        extract('year', Lancamento.data) == ano,
        Lancamento.tipo == 'Entrada'
    ).order_by(Lancamento.data, Lancamento.id).all()
    
    # Classificar
    debug_info = []
    totais_debug = {
        'outras_ofertas_banco': 0,
        'ofertas_banco': 0,
        'dizimos_banco': 0,
        'omn_banco': 0
    }
    
    for lanc in lancamentos:
        conta = lanc.conta.lower() if lanc.conta else 'dinheiro'
        categoria = lanc.categoria.lower() if lanc.categoria else ''
        valor = lanc.valor or 0
        eh_banco = 'banco' in conta or 'pix' in conta
        
        if not eh_banco:
            continue  # Mostrar apenas banco
        
        classificacao = None
        cor = ''
        
        # Dízimos
        if 'dízimo' in categoria or 'dizimo' in categoria:
            classificacao = 'DÍZIMOS'
            totais_debug['dizimos_banco'] += valor
            cor = 'success'
        # OMN
        elif 'omn' in categoria or 'missionaria' in categoria or 'missionária' in categoria:
            classificacao = 'OMN'
            totais_debug['omn_banco'] += valor
            cor = 'info'
        # Outras Ofertas
        elif 'oferta' in categoria and any(x in categoria for x in ['outras', 'especial', 'voluntaria', 'voluntária']):
            classificacao = 'OUTRAS OFERTAS'
            totais_debug['outras_ofertas_banco'] += valor
            cor = 'warning'
            debug_info.append({
                'id': lanc.id,
                'data': lanc.data,
                'categoria': lanc.categoria,
                'conta': lanc.conta,
                'valor': valor,
                'classificacao': classificacao,
                'cor': cor
            })
        # Ofertas Alçadas
        elif 'oferta' in categoria:
            classificacao = 'OFERTAS ALÇADAS'
            totais_debug['ofertas_banco'] += valor
            cor = 'primary'
    
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Debug Outras Ofertas - {mes:02d}/{ano}</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/css/bootstrap.min.css" rel="stylesheet">
    </head>
    <body class="bg-light">
        <div class="container mt-4">
            <h2>🔍 Debug: Outras Ofertas Banco - {mes:02d}/{ano}</h2>
            
            <div class="alert alert-info">
                <strong>Totais Calculados (Banco apenas):</strong><br>
                Dízimos: R$ {totais_debug['dizimos_banco']:.2f}<br>
                Ofertas Alçadas: R$ {totais_debug['ofertas_banco']:.2f}<br>
                <strong>Outras Ofertas: R$ {totais_debug['outras_ofertas_banco']:.2f}</strong><br>
                OMN: R$ {totais_debug['omn_banco']:.2f}
            </div>
            
            <h4>Lançamentos Classificados como "OUTRAS OFERTAS BANCO":</h4>
            <table class="table table-striped table-bordered">
                <thead>
                    <tr>
                        <th>ID</th>
                        <th>Data</th>
                        <th>Categoria ORIGINAL</th>
                        <th>Conta</th>
                        <th>Valor</th>
                    </tr>
                </thead>
                <tbody>
    """
    
    if debug_info:
        for item in debug_info:
            html += f"""
                    <tr class="table-{item['cor']}">
                        <td>{item['id']}</td>
                        <td>{item['data'].strftime('%d/%m/%Y')}</td>
                        <td><strong>{item['categoria']}</strong></td>
                        <td>{item['conta']}</td>
                        <td>R$ {item['valor']:.2f}</td>
                    </tr>
            """
    else:
        html += '<tr><td colspan="5" class="text-center text-muted">Nenhum lançamento classificado como Outras Ofertas Banco</td></tr>'
    
    html += """
                </tbody>
            </table>
            
            <a href="/financeiro/relatorio-caixa?mes=""" + str(mes) + """&ano=""" + str(ano) + """" class="btn btn-secondary">← Voltar ao Relatório</a>
        </div>
    </body>
    </html>
    """
    
    return html

@financeiro_bp.route('/financeiro/debug-saldo-banco')
@login_required
def debug_saldo_banco():
    """Debug para identificar diferença no saldo do banco"""
    mes = request.args.get('mes', type=int, default=1)
    ano = request.args.get('ano', type=int, default=2026)
    
    # Buscar TODOS os lançamentos até o mês especificado
    from datetime import date
    data_final = date(ano, mes, 28)  # Último dia considerado do mês
    
    lancamentos = Lancamento.query.filter(
        Lancamento.data <= data_final
    ).order_by(Lancamento.data, Lancamento.id).all()
    
    # Separar por conta BANCO
    saldo_banco = 0
    entradas_banco = 0
    saidas_banco = 0
    lancamentos_banco = []
    
    for lanc in lancamentos:
        conta = (lanc.conta or '').lower()
        categoria = (lanc.categoria or '').lower()
        
        # Apenas BANCO e PIX
        if 'banco' not in conta and 'pix' not in conta:
            continue
        
        valor = lanc.valor or 0
        
        # Verificar se é destinação (não afeta saldo)
        eh_destinacao = any(x in categoria for x in [
            'destinação', 'destinacao', 
            'transferência interna', 'transferencia interna'
        ])
        
        if lanc.tipo == 'Entrada':
            saldo_banco += valor
            entradas_banco += valor
            operacao = 'ENTRADA'
            cor = 'success'
        elif lanc.tipo == 'Saída' and not eh_destinacao:
            saldo_banco -= valor
            saidas_banco += valor
            operacao = 'SAÍDA'
            cor = 'danger'
        else:
            operacao = 'DESTINAÇÃO (ignorado)'
            cor = 'secondary'
        
        lancamentos_banco.append({
            'id': lanc.id,
            'data': lanc.data,
            'tipo': lanc.tipo,
            'categoria': lanc.categoria,
            'descricao': lanc.descricao or '',
            'conta': lanc.conta,
            'valor': valor,
            'operacao': operacao,
            'saldo_apos': saldo_banco,
            'cor': cor,
            'eh_destinacao': eh_destinacao
        })
    
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Debug Saldo Banco - até {mes:02d}/{ano}</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/css/bootstrap.min.css" rel="stylesheet">
    </head>
    <body class="bg-light">
        <div class="container-fluid mt-4">
            <h2>🔍 Debug: Saldo do Banco - até {mes:02d}/{ano}</h2>
            
            <div class="row mb-4">
                <div class="col-md-3">
                    <div class="card border-success">
                        <div class="card-body text-center">
                            <h6 class="text-success">Total Entradas</h6>
                            <h4>R$ {entradas_banco:.2f}</h4>
                        </div>
                    </div>
                </div>
                <div class="col-md-3">
                    <div class="card border-danger">
                        <div class="card-body text-center">
                            <h6 class="text-danger">Total Saídas</h6>
                            <h4>R$ {saidas_banco:.2f}</h4>
                        </div>
                    </div>
                </div>
                <div class="col-md-3">
                    <div class="card border-primary">
                        <div class="card-body text-center">
                            <h6 class="text-primary">Saldo Calculado</h6>
                            <h4>R$ {saldo_banco:.2f}</h4>
                        </div>
                    </div>
                </div>
                <div class="col-md-3">
                    <div class="card border-warning">
                        <div class="card-body text-center">
                            <h6 class="text-warning">Saldo Real (Banco)</h6>
                            <h4>R$ 1.026,90</h4>
                            <small class="text-danger">Diferença: R$ {saldo_banco - 1026.90:.2f}</small>
                        </div>
                    </div>
                </div>
            </div>
            
            <h4>Todos os Lançamentos de BANCO/PIX (ordem cronológica):</h4>
            <div class="table-responsive">
                <table class="table table-sm table-hover table-bordered">
                    <thead class="table-dark">
                        <tr>
                            <th>ID</th>
                            <th>Data</th>
                            <th>Operação</th>
                            <th>Categoria</th>
                            <th>Descrição</th>
                            <th>Conta</th>
                            <th>Valor</th>
                            <th>Saldo Após</th>
                        </tr>
                    </thead>
                    <tbody>
    """
    
    for item in lancamentos_banco:
        html += f"""
                    <tr class="table-{item['cor']}">
                        <td>{item['id']}</td>
                        <td>{item['data'].strftime('%d/%m/%Y')}</td>
                        <td><strong>{item['operacao']}</strong></td>
                        <td>{item['categoria']}</td>
                        <td>{item['descricao'][:50]}</td>
                        <td>{item['conta']}</td>
                        <td class="text-end">R$ {item['valor']:.2f}</td>
                        <td class="text-end"><strong>R$ {item['saldo_apos']:.2f}</strong></td>
                    </tr>
        """
    
    html += """
                    </tbody>
                </table>
            </div>
            
            <div class="alert alert-info mt-3">
                <strong>Instruções:</strong>
                <ul>
                    <li>Compare o Saldo Calculado (R$ """ + f"{saldo_banco:.2f}" + """) com o Saldo Real do Banco (R$ 1.026,90)</li>
                    <li>Procure por lançamentos duplicados, com valores errados ou tipos invertidos</li>
                    <li>Destinações são ignoradas no cálculo (aparecem em cinza)</li>
                    <li>Verde = Entradas (+), Vermelho = Saídas (-), Cinza = Destinações (ignoradas)</li>
                </ul>
            </div>
            
            <a href="/financeiro/relatorio-caixa?mes=""" + str(mes) + """&ano=""" + str(ano) + """" class="btn btn-secondary mb-4">← Voltar ao Relatório</a>
        </div>
    </body>
    </html>
    """
    
    return html

@financeiro_bp.route('/financeiro/relatorio-caixa')
@login_required
def relatorio_caixa():
    """Mantém compatibilidade redirecionando para o relatório gerencial centralizado."""
    return redirect(url_for('financeiro.gerar_relatorio', tipo_relatorio='gerencial', mes=request.args.get('mes', type=int), ano=request.args.get('ano', type=int)))


def _calcular_totais_relatorio_sede(lancamentos, percentual_conselho=30.0):
    """Calcula totais do relatório da sede com regras consistentes com o relatório de caixa."""
    totais = {
        'dizimos': Decimal('0'),
        'ofertas_alcadas': Decimal('0'),
        'outras_ofertas': Decimal('0'),
        'oferta_omn': Decimal('0'),
        'outras_entradas': Decimal('0'),
        'total_geral': Decimal('0'),
        'despesas_financeiras': Decimal('0'),
        'saldo_mes': Decimal('0'),
        'valor_conselho': Decimal('0'),
        'total_dizimos_ofertas': Decimal('0'),
        'percentual_30': Decimal('0')
    }

    percentual = _decimal_monetario(percentual_conselho if percentual_conselho is not None else 30).scaleb(-2)

    for lancamento in lancamentos:
        categoria = (lancamento.categoria or '').lower()
        valor = _decimal_monetario(lancamento.valor or 0)

        if lancamento.tipo == 'Entrada':
            totais['total_geral'] += valor

            if 'dízimo' in categoria or 'dizimo' in categoria:
                totais['dizimos'] += valor
            elif 'omn' in categoria or 'missionaria' in categoria or 'missionária' in categoria:
                totais['oferta_omn'] += valor
            elif 'oferta' in categoria and any(x in categoria for x in ['outras', 'especial', 'voluntaria', 'voluntária']):
                totais['outras_ofertas'] += valor
            elif 'oferta' in categoria:
                totais['ofertas_alcadas'] += valor
            else:
                totais['outras_entradas'] += valor

        elif lancamento.tipo == 'Saída':
            eh_destinacao = any(x in categoria for x in [
                'destinação', 'destinacao',
                'transferência interna', 'transferencia interna'
            ])

            if not eh_destinacao:
                totais['despesas_financeiras'] += valor

    totais['total_dizimos_ofertas'] = totais['dizimos'] + totais['ofertas_alcadas']
    totais['valor_conselho'] = totais['total_dizimos_ofertas'] * percentual
    totais['percentual_30'] = totais['valor_conselho']
    totais['saldo_mes'] = totais['total_geral'] - totais['despesas_financeiras']

    return totais


def _iterar_meses_ate(mes, ano):
    """Itera de 01/2020 até o mês/ano informado (inclusive)."""
    ano_atual = 2020
    mes_atual = 1
    while (ano_atual < ano) or (ano_atual == ano and mes_atual <= mes):
        yield mes_atual, ano_atual
        mes_atual += 1
        if mes_atual > 12:
            mes_atual = 1
            ano_atual += 1


def _calcular_obrigacao_30_mes(mes, ano, percentual_conselho):
    """Calcula a obrigacao mensal de 30% sem alterar qualquer regra existente."""
    lancamentos_mes = Lancamento.query.filter(
        extract('month', Lancamento.data) == mes,
        extract('year', Lancamento.data) == ano
    ).all()
    totais = _calcular_totais_relatorio_sede(lancamentos_mes, percentual_conselho)
    return _quantizar_monetario(totais.get('valor_conselho', Decimal('0')))


def _montar_controle_repasse_sede(mes, ano, percentual_conselho):
    """Monta quadro de controle de repasse por competencia (geracao) e pagamento (liquidacao)."""
    obrigacao_mes = _calcular_obrigacao_30_mes(mes, ano, percentual_conselho)

    obrigacoes_ate_anterior = Decimal('0')
    for mes_item, ano_item in _iterar_meses_ate(mes, ano):
        if ano_item == ano and mes_item == mes:
            break
        obrigacoes_ate_anterior += _calcular_obrigacao_30_mes(mes_item, ano_item, percentual_conselho)

    schema_moderno = _envio_sede_tem_schema_moderno()

    if schema_moderno:
        try:
            pagos_ate_anterior = _decimal_monetario(
                EnvioSede.somar_pagamentos_administrativos_por_competencia_ate(
                    mes - 1 if mes > 1 else 12,
                    ano if mes > 1 else ano - 1,
                ) or 0
            )
        except (OperationalError, ProgrammingError, AttributeError):
            db.session.rollback()
            pagos_ate_anterior = _decimal_monetario(EnvioSede.somar_pagamentos_antes_do_mes(mes, ano) or 0)

        pago_mes = _decimal_monetario(EnvioSede.somar_pagamentos_mes(mes, ano) or 0)
        try:
            pagamentos_competencia_mes = _decimal_monetario(EnvioSede.somar_pagamentos_administrativos_por_competencia_mes(mes, ano) or 0)
        except (OperationalError, ProgrammingError, AttributeError):
            db.session.rollback()
            pagamentos_competencia_mes = _decimal_monetario(EnvioSede.somar_pagamentos_mes(mes, ano) or 0)
    else:
        # Em schema antigo, evita carregar entidade completa (que referencia colunas inexistentes).
        pagos_ate_anterior = _decimal_monetario(EnvioSede.somar_pagamentos_antes_do_mes(mes, ano) or 0)
        pago_mes = _decimal_monetario(EnvioSede.somar_pagamentos_mes(mes, ano) or 0)
        pagamentos_competencia_mes = _decimal_monetario(EnvioSede.somar_pagamentos_mes(mes, ano) or 0)

    saldo_pendente_anterior = obrigacoes_ate_anterior - pagos_ate_anterior
    total_devido = saldo_pendente_anterior + obrigacao_mes
    saldo_pendente_atual = total_devido - pagamentos_competencia_mes

    try:
        pagamentos_mes = EnvioSede.listar_pagamentos_mes(mes, ano) if schema_moderno else []
    except (OperationalError, ProgrammingError, AttributeError):
        db.session.rollback()
        pagamentos_mes = []

    saldo_pendente_anterior = obrigacoes_ate_anterior - pagos_ate_anterior
    total_devido = saldo_pendente_anterior + obrigacao_mes
    saldo_pendente_atual = total_devido - pagamentos_competencia_mes

    observacao_quitacao_competencia_anterior = any(
        p.competencia_ano_ref is not None and p.competencia_mes_ref is not None and
        ((p.competencia_ano_ref < ano) or (p.competencia_ano_ref == ano and p.competencia_mes_ref < mes))
        for p in pagamentos_mes
    )

    total_admin_mes = sum(_valor_administrativo_pagamento_sede(p) for p in pagamentos_mes)
    total_despesas_fixas_mes = sum(_valor_despesas_fixas_pagamento_sede(p) for p in pagamentos_mes)
    total_pago_mes = sum(_valor_total_pagamento_sede(p) for p in pagamentos_mes)

    return {
        'saldo_pendente_anterior': _quantizar_monetario(saldo_pendente_anterior),
        'trinta_gerado_mes': _quantizar_monetario(obrigacao_mes),
        'total_devido_mes': _quantizar_monetario(total_devido),
        'valor_enviado_mes': _quantizar_monetario(pago_mes),
        'saldo_pendente_atual': _quantizar_monetario(saldo_pendente_atual),
        'pagamentos_mes': pagamentos_mes,
        'total_administrativo_pago_mes': _quantizar_monetario(total_admin_mes),
        'total_despesas_fixas_pago_mes': _quantizar_monetario(total_despesas_fixas_mes),
        'total_pago_mes': _quantizar_monetario(total_pago_mes),
        'observacao_quitacao_competencia_anterior': observacao_quitacao_competencia_anterior,
    }


def _gerar_observacao_repasse_padrao(controle_repasse_sede):
    valor_enviado_mes = float((controle_repasse_sede or {}).get('valor_enviado_mes', 0) or 0)
    if valor_enviado_mes <= 0:
        return 'Não houve pagamento de repasses à Sede neste período.'

    if (controle_repasse_sede or {}).get('observacao_quitacao_competencia_anterior'):
        return 'Foram registrados pagamentos neste período referentes à quitação de competências anteriores junto à Sede.'

    return 'Os pagamentos realizados neste período referem-se exclusivamente às competências do próprio mês.'


def _obter_observacao_repasse_sede(mes, ano, controle_repasse_sede, tipo_relatorio='gerencial'):
    tipo_observacao = (tipo_relatorio or 'gerencial').strip().lower()
    if tipo_observacao not in {'gerencial', 'sede', 'auditoria', 'caixa', 'repasses_sede'}:
        tipo_observacao = 'gerencial'

    observacao_padrao = _gerar_observacao_repasse_padrao(controle_repasse_sede)
    observacao_salva = ObservacaoRelatorio.obter_texto(mes, ano, tipo_relatorio=tipo_observacao)
    if observacao_salva:
        return observacao_salva, observacao_padrao, True
    return observacao_padrao, observacao_padrao, False

@financeiro_bp.route('/financeiro/relatorio-sede')
@login_required
def relatorio_sede():
    """Mantém compatibilidade redirecionando para o relatório oficial centralizado."""
    return redirect(url_for('financeiro.gerar_relatorio', tipo_relatorio='sede', mes=request.args.get('mes', type=int), ano=request.args.get('ano', type=int)))


@financeiro_bp.route('/financeiro/relatorio-auditoria')
@login_required
def relatorio_auditoria():
    """Relatório completo para auditoria utilizando o mesmo conjunto de dados financeiros."""
    return redirect(url_for('financeiro.gerar_relatorio', tipo_relatorio='auditoria', mes=request.args.get('mes', type=int), ano=request.args.get('ano', type=int)))

@financeiro_bp.route('/financeiro/relatorio-obpc')
@login_required
def relatorio_obpc():
    """Relatório OBPC com fechamento do dia 26 ao dia 25"""
    from datetime import date, timedelta
    from dateutil.relativedelta import relativedelta
    from app.configuracoes.configuracoes_model import Configuracao
    from app.financeiro.financeiro_model import Lancamento
    from sqlalchemy import and_
    
    try:
        # Obter mês e ano de referência (padrão: mês atual)
        mes_ref = int(request.args.get('mes', date.today().month))
        ano_ref = int(request.args.get('ano', date.today().year))
        
        # Calcular o período OBPC: dia 26 do mês anterior até dia 25 do mês de referência
        # Exemplo: Para Maio/2026, período é 26/Abr/2026 até 25/Mai/2026
        data_inicial = date(ano_ref, mes_ref, 1) - relativedelta(months=1)
        data_inicial = date(data_inicial.year, data_inicial.month, 26)
        data_final = date(ano_ref, mes_ref, 25)
        
        # Buscar lançamentos do período OBPC
        lancamentos = Lancamento.query.filter(
            and_(
                Lancamento.data >= data_inicial,
                Lancamento.data <= data_final
            )
        ).order_by(Lancamento.data).all()
        
        # Inicializar totais
        totais_obpc = {
            # Entradas por categoria
            'dizimos': 0,
            'ofertas_alcadas': 0,  # Ofertas comuns do ofertório
            'outras_ofertas': 0,   # Ofertas especiais/voluntárias
            'oferta_omn': 0,       # Ofertas missionárias
            'rendimentos': 0,
            'outras_entradas': 0,
            'total_entradas': 0,
            
            # Saídas por categoria
            'despesas_fixas': 0,
            'despesas_variaveis': 0,
            'prebenda': 0,
            'outras_saidas': 0,
            'total_saidas': 0,
            
            # Cálculos OBPC
            'base_30_sede': 0,          # Dízimos + Ofertas Alçadas
            'valor_30_sede': 0,         # 30% para a Sede
            'prebenda_percentual': 0,   # % da prebenda sobre entradas
            'saldo_operacional': 0,     # Saldo final da igreja local
            'saldo_anterior': 0,
            'saldo_periodo': 0,
            'saldo_final': 0,
        }
        
        # Processar lançamentos
        for lanc in lancamentos:
            conta = lanc.conta.lower() if lanc.conta else 'dinheiro'
            categoria = lanc.categoria.lower() if lanc.categoria else ''
            valor = lanc.valor or 0
            
            if lanc.tipo == 'Entrada':
                # Classificar entradas
                if 'dízimo' in categoria or 'dizimo' in categoria:
                    totais_obpc['dizimos'] += valor
                    
                elif 'omn' in categoria or 'missionaria' in categoria or 'missionária' in categoria:
                    totais_obpc['oferta_omn'] += valor
                    
                elif 'oferta' in categoria and any(x in categoria for x in ['outras', 'especial', 'voluntaria', 'voluntária']):
                    totais_obpc['outras_ofertas'] += valor
                    
                elif 'oferta' in categoria:
                    totais_obpc['ofertas_alcadas'] += valor
                    
                elif 'rendimento' in categoria or 'juros' in categoria:
                    totais_obpc['rendimentos'] += valor
                    
                else:
                    totais_obpc['outras_entradas'] += valor
                
                totais_obpc['total_entradas'] += valor
            
            elif lanc.tipo == 'Saída':
                # Classificar saídas
                if 'prebenda' in categoria:
                    totais_obpc['prebenda'] += valor
                    
                elif 'desp' in categoria and 'fixa' in categoria:
                    totais_obpc['despesas_fixas'] += valor
                    
                elif 'desp' in categoria and 'variav' in categoria:
                    totais_obpc['despesas_variaveis'] += valor
                    
                else:
                    totais_obpc['outras_saidas'] += valor
                
                totais_obpc['total_saidas'] += valor
        
        # Calcular saldo anterior (até o dia 25 do mês anterior ao período)
        data_limite_saldo_anterior = data_inicial - timedelta(days=1)
        lancamentos_anteriores = Lancamento.query.filter(
            Lancamento.data <= data_limite_saldo_anterior
        ).all()
        
        entradas_anteriores = sum(l.valor for l in lancamentos_anteriores if l.tipo == 'Entrada')
        saidas_anteriores = sum(l.valor for l in lancamentos_anteriores if l.tipo == 'Saída')
        totais_obpc['saldo_anterior'] = entradas_anteriores - saidas_anteriores
        
        # Cálculos OBPC
        # 1. Base para cálculo dos 30% da Sede: APENAS dízimos + ofertas alçadas
        totais_obpc['base_30_sede'] = totais_obpc['dizimos'] + totais_obpc['ofertas_alcadas']
        totais_obpc['valor_30_sede'] = totais_obpc['base_30_sede'] * 0.30
        
        # 2. Verificar se a prebenda está dentro do limite de 30% das entradas
        if totais_obpc['total_entradas'] > 0:
            totais_obpc['prebenda_percentual'] = (totais_obpc['prebenda'] / totais_obpc['total_entradas']) * 100
        else:
            totais_obpc['prebenda_percentual'] = 0
        
        # 3. Saldo do período
        totais_obpc['saldo_periodo'] = totais_obpc['total_entradas'] - totais_obpc['total_saidas']
        totais_obpc['saldo_final'] = totais_obpc['saldo_anterior'] + totais_obpc['saldo_periodo']
        
        # 4. Saldo operacional = Saldo final - 30% da Sede (que ainda não foi enviado)
        totais_obpc['saldo_operacional'] = totais_obpc['saldo_final'] - totais_obpc['valor_30_sede']
        
        # Buscar dados da configuração
        config = Configuracao.obter_configuracao()
        dados_igreja = {
            'cidade': (config.cidade if config and hasattr(config, 'cidade') and config.cidade else 'Tietê'),
            'bairro': (config.bairro if config and hasattr(config, 'bairro') and config.bairro else 'Centro'),
            'dirigente': (config.presidente if config and hasattr(config, 'presidente') and config.presidente else 'Pastor Responsável'),
            'tesoureiro': (config.primeiro_tesoureiro if config and hasattr(config, 'primeiro_tesoureiro') and config.primeiro_tesoureiro else 'Tesoureiro(a)')
        }
        
        # Buscar despesas fixas do conselho
        try:
            despesas_fixas_conselho = DespesaFixaConselho.obter_despesas_ativas()
            total_despesas_fixas_conselho = sum(d.valor_padrao for d in despesas_fixas_conselho) if despesas_fixas_conselho else 0
        except Exception as e:
            current_app.logger.error(f"Erro ao buscar despesas fixas: {e}")
            total_despesas_fixas_conselho = 0
        
        totais_obpc['despesas_fixas_conselho'] = total_despesas_fixas_conselho
        totais_obpc['total_envio_sede'] = totais_obpc['valor_30_sede'] + total_despesas_fixas_conselho
        
        return render_template('financeiro/relatorio_obpc.html',
                             totais=totais_obpc,
                             dados_igreja=dados_igreja,
                             mes_ref=mes_ref,
                             ano_ref=ano_ref,
                             data_inicial=data_inicial,
                             data_final=data_final,
                             data_geracao=date.today(),
                             lancamentos=lancamentos)
        
    except Exception as e:
        current_app.logger.error(f"Erro ao gerar relatório OBPC: {e}")
        import traceback
        current_app.logger.error(f"Traceback: {traceback.format_exc()}")
        flash(f'Erro ao gerar relatório OBPC: {str(e)}', 'danger')
        return redirect(url_for('financeiro.lista_lancamentos'))

@financeiro_bp.route('/financeiro/despesas-fixas', methods=['GET', 'POST'])
@login_required
def gerenciar_despesas_fixas():
    """Interface para gerenciar despesas fixas e controle de envio a sede."""
    try:
        _garantir_colunas_envio_sede_regularizacao()

        # Processar ações de POST
        if request.method == 'POST':
            acao = request.form.get('acao')
            
            if acao == 'criar':
                nova_despesa = DespesaFixaConselho(
                    nome=request.form.get('nome', '').strip(),
                    descricao=request.form.get('descricao', '').strip(),
                    categoria=request.form.get('categoria', '').strip(),
                    valor_padrao=float(request.form.get('valor_padrao', 0)),
                    ativo=True
                )
                
                # Validar antes de salvar
                erros = nova_despesa.validar()
                if erros:
                    for erro in erros:
                        flash(erro, 'danger')
                    return redirect(url_for('financeiro.gerenciar_despesas_fixas'))
                
                db.session.add(nova_despesa)
                db.session.commit()
                flash(f'Despesa fixa "{nova_despesa.nome}" criada com sucesso!', 'success')
                
            elif acao == 'editar':
                despesa_id = request.form.get('id')
                despesa = DespesaFixaConselho.query.get_or_404(despesa_id)
                
                despesa.nome = request.form.get('nome', '').strip()
                despesa.descricao = request.form.get('descricao', '').strip()
                despesa.categoria = request.form.get('categoria', '').strip()
                despesa.valor_padrao = float(request.form.get('valor_padrao', 0))
                despesa.ativo = bool(request.form.get('ativo'))
                
                # Validar antes de salvar
                erros = despesa.validar()
                if erros:
                    for erro in erros:
                        flash(erro, 'danger')
                    return redirect(url_for('financeiro.gerenciar_despesas_fixas'))
                
                db.session.commit()
                flash(f'Despesa fixa "{despesa.nome}" atualizada com sucesso!', 'success')

            elif acao == 'registrar_pagamento_sede':
                data_pagamento_raw = request.form.get('data_pagamento', '').strip()
                forma_pagamento = request.form.get('forma_pagamento', 'PIX').strip() or 'PIX'
                competencia = request.form.get('competencia', '').strip() or f'Competência {datetime.now().month:02d}/{datetime.now().year}'
                observacao = request.form.get('observacao', '').strip() or None
                pagamento_historico_sem_movimentacao = bool(request.form.get('pagamento_historico_sem_movimentacao'))
                tipo_pagamento = 'HISTORICO_SEM_MOVIMENTACAO' if pagamento_historico_sem_movimentacao else 'PAGAMENTO_BANCARIO'
                competencia_mes_ref = request.form.get('competencia_mes_ref', type=int)
                competencia_ano_ref = request.form.get('competencia_ano_ref', type=int)

                if not competencia_mes_ref or not competencia_ano_ref:
                    flash('Informe mês e ano de competência para registrar a baixa.', 'danger')
                    return redirect(url_for('financeiro.gerenciar_despesas_fixas'))

                if not data_pagamento_raw and not pagamento_historico_sem_movimentacao:
                    flash('Informe a data do pagamento do repasse à sede.', 'danger')
                    return redirect(url_for('financeiro.gerenciar_despesas_fixas'))

                if data_pagamento_raw:
                    try:
                        data_pagamento = datetime.strptime(data_pagamento_raw, '%Y-%m-%d').date()
                    except ValueError:
                        flash('Data de pagamento inválida.', 'danger')
                        return redirect(url_for('financeiro.gerenciar_despesas_fixas'))
                else:
                    data_pagamento = date(competencia_ano_ref, competencia_mes_ref, 1)

                ids = request.form.getlist('alocacao_obrigacao_id[]')
                valores = request.form.getlist('alocacao_valor[]')
                if not ids and request.form.get('alocacao_obrigacao_id') is not None:
                    ids = [request.form.get('alocacao_obrigacao_id')]
                if not valores and request.form.get('alocacao_valor') is not None:
                    valores = [request.form.get('alocacao_valor')]

                if len(ids) != len(valores):
                    flash('A alocação do pagamento deve informar cada obrigação com seu valor correspondente.', 'danger')
                    return redirect(url_for('financeiro.gerenciar_despesas_fixas'))

                alocacoes = []
                for index, obrigacao_id in enumerate(ids):
                    try:
                        valor = float((valores[index] or '0').replace(',', '.'))
                    except (TypeError, ValueError):
                        flash(f'Valor inválido para a alocação da obrigação {obrigacao_id}.', 'danger')
                        return redirect(url_for('financeiro.gerenciar_despesas_fixas'))
                    if obrigacao_id is None or str(obrigacao_id).strip() == '':
                        flash('Obrigação da alocação não informada.', 'danger')
                        return redirect(url_for('financeiro.gerenciar_despesas_fixas'))
                    alocacoes.append({"obrigacao_id": obrigacao_id, "valor": valor})

                comprovante = None
                file = request.files.get('comprovante_sede')
                if file and file.filename:
                    comprovante = processar_upload_comprovante(file)

                resultado = registrar_repasse_sede_composto(
                    alocacoes=alocacoes,
                    competencia_mes_ref=competencia_mes_ref,
                    competencia_ano_ref=competencia_ano_ref,
                    data_pagamento=data_pagamento,
                    forma_pagamento=forma_pagamento,
                    tipo_pagamento=tipo_pagamento,
                    comprovante=comprovante,
                    observacao=observacao,
                    usuario=getattr(current_user, 'nome', None) or getattr(current_user, 'username', None),
                    valor_total=None,
                    valor_administrativo=None,
                    valor_despesas_fixas=None,
                )

                if resultado.get('status') == 'ja_existente':
                    flash('Este pagamento composto já foi registrado para a mesma alocação e competência.', 'info')
                    return redirect(url_for('financeiro.gerenciar_despesas_fixas', mes=competencia_mes_ref, ano=competencia_ano_ref))
                if resultado.get('status') == 'erro' or resultado.get('erro'):
                    flash(f"Erro ao registrar pagamento composto: {resultado.get('erro') or 'falha ao processar o repasse.'}", 'danger')
                    return redirect(url_for('financeiro.gerenciar_despesas_fixas', mes=competencia_mes_ref, ano=competencia_ano_ref))

                if pagamento_historico_sem_movimentacao:
                    flash('Baixa histórica registrada com sucesso (sem movimentação no caixa/banco).', 'success')
                else:
                    flash('Pagamento de repasse à sede registrado com sucesso!', 'success')

                return redirect(url_for('financeiro.gerenciar_despesas_fixas', mes=competencia_mes_ref, ano=competencia_ano_ref))

            elif acao == 'editar_pagamento_sede':
                pagamento_id = request.form.get('pagamento_id', type=int)
                pagamento = EnvioSede.query.get_or_404(pagamento_id)

                try:
                    pagamento.validar_edicao_ou_exclusao_aceita()
                except ValueError as exc:
                    flash(str(exc), 'danger')
                    return redirect(url_for('financeiro.gerenciar_despesas_fixas'))

                data_pagamento_raw = request.form.get('data_pagamento', '').strip()
                valor_administrativo = float(request.form.get('valor_administrativo', 0) or 0)
                valor_despesas_fixas = float(request.form.get('valor_despesas_fixas', 0) or 0)
                valor_total = float(request.form.get('valor_total', 0) or 0)
                forma_pagamento = request.form.get('forma_pagamento', 'PIX').strip() or 'PIX'
                competencia = request.form.get('competencia', '').strip() or f'Competência {datetime.now().month:02d}/{datetime.now().year}'
                observacao = request.form.get('observacao', '').strip() or None
                pagamento_historico_sem_movimentacao = bool(request.form.get('pagamento_historico_sem_movimentacao'))

                if not data_pagamento_raw and not pagamento_historico_sem_movimentacao:
                    flash('Informe a data do pagamento do repasse à sede.', 'danger')
                    return redirect(url_for('financeiro.gerenciar_despesas_fixas'))

                if valor_administrativo < 0 or valor_despesas_fixas < 0:
                    flash('Valores de administrativo e despesas fixas não podem ser negativos.', 'danger')
                    return redirect(url_for('financeiro.gerenciar_despesas_fixas'))

                soma_componentes = round(valor_administrativo + valor_despesas_fixas, 2)
                valor_total = round(valor_total, 2)
                if valor_total <= 0:
                    flash('O valor do pagamento deve ser maior que zero.', 'danger')
                    return redirect(url_for('financeiro.gerenciar_despesas_fixas'))
                if abs(valor_total - soma_componentes) > 0.009:
                    flash('O valor total deve ser igual à soma de administrativo + despesas fixas.', 'danger')
                    return redirect(url_for('financeiro.gerenciar_despesas_fixas'))

                competencia_mes_ref = request.form.get('competencia_mes_ref', type=int)
                competencia_ano_ref = request.form.get('competencia_ano_ref', type=int)

                if not competencia_mes_ref or not competencia_ano_ref:
                    flash('Informe mês e ano de competência para atualizar a baixa.', 'danger')
                    return redirect(url_for('financeiro.gerenciar_despesas_fixas'))

                valido, resultado_limites = _validar_limites_repasse_sede(
                    competencia_mes_ref,
                    competencia_ano_ref,
                    valor_administrativo,
                    valor_despesas_fixas,
                    excluir_pagamento_id=pagamento.id,
                )
                if not valido:
                    flash(resultado_limites, 'danger')
                    return redirect(url_for('financeiro.gerenciar_despesas_fixas'))

                data_pagamento_informada = True
                if data_pagamento_raw:
                    try:
                        data_pagamento = datetime.strptime(data_pagamento_raw, '%Y-%m-%d').date()
                    except ValueError:
                        flash('Data de pagamento inválida.', 'danger')
                        return redirect(url_for('financeiro.gerenciar_despesas_fixas'))
                else:
                    data_pagamento = date(competencia_ano_ref, competencia_mes_ref, 1)
                    data_pagamento_informada = False

                if pagamento.comprovante:
                    pagamento.comprovante = pagamento.comprovante
                file = request.files.get('comprovante_sede')
                if file and file.filename:
                    pagamento.comprovante = processar_upload_comprovante(file)

                pagamento.data_pagamento = data_pagamento
                pagamento.valor = valor_total
                pagamento.valor_administrativo = valor_administrativo
                pagamento.valor_despesas_fixas = valor_despesas_fixas
                pagamento.valor_total = valor_total
                pagamento.forma_pagamento = forma_pagamento
                pagamento.competencia = competencia
                pagamento.competencia_mes_ref = competencia_mes_ref
                pagamento.competencia_ano_ref = competencia_ano_ref
                pagamento.competencia_mes = competencia_mes_ref
                pagamento.competencia_ano = competencia_ano_ref
                pagamento.tipo_pagamento = _tipo_pagamento_sede(pagamento_historico_sem_movimentacao)
                pagamento.observacao = observacao
                pagamento.valor_devido_competencia = valor_total
                pagamento.pagamento_historico_sem_movimentacao = pagamento_historico_sem_movimentacao
                pagamento.data_pagamento_informada = data_pagamento_informada
                _sincronizar_lancamento_repasse_sede(pagamento)
                db.session.commit()
                if pagamento_historico_sem_movimentacao:
                    flash('Baixa histórica atualizada com sucesso (sem movimentação no caixa/banco).', 'success')
                else:
                    flash('Pagamento de repasse à sede atualizado com sucesso!', 'success')

                return redirect(url_for('financeiro.gerenciar_despesas_fixas', mes=competencia_mes_ref, ano=competencia_ano_ref))

            elif acao == 'excluir_pagamento_sede':
                pagamento_id = request.form.get('pagamento_id', type=int)
                pagamento = EnvioSede.query.get_or_404(pagamento_id)
                mes_retorno = pagamento.competencia_mes_ref or request.args.get('mes', type=int)
                ano_retorno = pagamento.competencia_ano_ref or request.args.get('ano', type=int)

                try:
                    pagamento.validar_edicao_ou_exclusao_aceita()
                except ValueError as exc:
                    flash(str(exc), 'danger')
                    return redirect(url_for('financeiro.gerenciar_despesas_fixas'))

                if pagamento.lancamento_financeiro_id:
                    lancamento = Lancamento.query.get(pagamento.lancamento_financeiro_id)
                    if lancamento:
                        db.session.delete(lancamento)
                db.session.delete(pagamento)
                db.session.commit()
                flash('Pagamento de repasse à sede excluído com sucesso!', 'success')
                return redirect(url_for('financeiro.gerenciar_despesas_fixas', mes=mes_retorno, ano=ano_retorno))

            elif acao == 'salvar_observacao_repasse_sede':
                mes_ref_post = request.form.get('mes_ref', type=int)
                ano_ref_post = request.form.get('ano_ref', type=int)
                observacao_texto = request.form.get('observacao_repasse_sede', '')

                if not mes_ref_post or not ano_ref_post:
                    flash('Competência inválida para salvar a observação.', 'danger')
                    return redirect(url_for('financeiro.gerenciar_despesas_fixas'))

                if not observacao_texto or not observacao_texto.strip():
                    flash('Digite uma observação antes de salvar.', 'danger')
                    return redirect(url_for('financeiro.gerenciar_despesas_fixas', mes=mes_ref_post, ano=ano_ref_post))

                registro = ObservacaoRelatorio.salvar_texto(mes_ref_post, ano_ref_post, observacao_texto, tipo_relatorio='repasses_sede')
                if registro is None:
                    flash('A observação não pôde ser salva agora, mas o sistema continuará usando o texto automático.', 'warning')
                else:
                    db.session.commit()
                    flash('Observação dos repasses salva com sucesso!', 'success')
                return redirect(url_for('financeiro.gerenciar_despesas_fixas', mes=mes_ref_post, ano=ano_ref_post))

            elif acao == 'excluir_observacao_repasse_sede':
                mes_ref_post = request.form.get('mes_ref', type=int)
                ano_ref_post = request.form.get('ano_ref', type=int)

                if not mes_ref_post or not ano_ref_post:
                    flash('Competência inválida para excluir a observação.', 'danger')
                    return redirect(url_for('financeiro.gerenciar_despesas_fixas'))

                removida = ObservacaoRelatorio.excluir_texto(mes_ref_post, ano_ref_post, tipo_relatorio='repasses_sede')
                db.session.commit()

                if removida:
                    flash('Observação removida. O sistema voltará a usar o texto automático.', 'success')
                else:
                    flash('Não havia observação salva para esta competência.', 'info')
                return redirect(url_for('financeiro.gerenciar_despesas_fixas', mes=mes_ref_post, ano=ano_ref_post))
            
            return redirect(url_for('financeiro.gerenciar_despesas_fixas'))
        
        # Buscar todas as despesas para exibição
        despesas_todas = DespesaFixaConselho.query.order_by(DespesaFixaConselho.nome).all()
        despesas_ativas = DespesaFixaConselho.obter_despesas_ativas()
        total_despesas = DespesaFixaConselho.obter_total_despesas_fixas()

        # Dados do controle de repasse
        hoje = datetime.now()
        mes_ref = request.args.get('mes', hoje.month, type=int)
        ano_ref = request.args.get('ano', hoje.year, type=int)

        config = Configuracao.obter_configuracao()
        percentual_conselho = config.percentual_conselho if config and hasattr(config, 'percentual_conselho') and config.percentual_conselho else 30
        controle_repasse_sede = _montar_controle_repasse_sede(mes_ref, ano_ref, percentual_conselho)
        historico_pagamentos = EnvioSede.query.order_by(EnvioSede.data_pagamento.desc(), EnvioSede.id.desc()).limit(100).all()
        observacao_repasse_sede, observacao_repasse_padrao, observacao_repasse_salva = _obter_observacao_repasse_sede(
            mes_ref,
            ano_ref,
            controle_repasse_sede,
            tipo_relatorio='repasses_sede'
        )
        
        # Buscar categorias de saída dos lançamentos (para usar nas despesas fixas)
        categorias_saida = db.session.query(Lancamento.categoria).distinct().filter(
            Lancamento.categoria.isnot(None),
            Lancamento.tipo.ilike('saída')
        ).order_by(Lancamento.categoria).all()
        categorias_saida = [c[0] for c in categorias_saida if c[0] and c[0].strip()]
        
        obrigacoes_disponiveis = db.session.query(ObrigacaoFinanceira).filter(
            ObrigacaoFinanceira.competencia_mes == mes_ref,
            ObrigacaoFinanceira.competencia_ano == ano_ref,
            ObrigacaoFinanceira.origem_obrigacao == 'automatico',
            ObrigacaoFinanceira.tipo_obrigacao.in_(['ADMIN_SEDE_30', 'DESPESA_FIXA']),
            ObrigacaoFinanceira.status != 'CANCELADA',
        ).order_by(
            ObrigacaoFinanceira.tipo_obrigacao.asc(),
            ObrigacaoFinanceira.id.asc(),
        ).all()

        return render_template('financeiro/gerenciar_despesas_fixas.html',
                             despesas_todas=despesas_todas,
                             despesas_ativas=despesas_ativas,
                             total_despesas=total_despesas,
                             categorias_saida=categorias_saida,
                             controle_repasse_sede=controle_repasse_sede,
                             historico_pagamentos=historico_pagamentos,
                             observacao_repasse_sede=observacao_repasse_sede,
                             observacao_repasse_padrao=observacao_repasse_padrao,
                             observacao_repasse_salva=observacao_repasse_salva,
                             mes_ref=mes_ref,
                             ano_ref=ano_ref,
                             now=hoje,
                             obrigacoes_disponiveis=obrigacoes_disponiveis)
    
    except Exception as e:
        db.session.rollback()
        flash(f'Erro ao gerenciar despesas fixas: {str(e)}', 'danger')
        return redirect(url_for('financeiro.lista_lancamentos'))


@financeiro_bp.route('/financeiro/envio-sede', methods=['GET', 'POST'])
@login_required
def envio_sede():
    """Atalho de navegação para a tela unificada de envio à sede."""
    return gerenciar_despesas_fixas()

@financeiro_bp.route('/financeiro/despesas-fixas/toggle/<int:id>')
@login_required
def toggle_despesa_fixa(id):
    """Alterna o status ativo/inativo de uma despesa fixa"""
    try:
        despesa = DespesaFixaConselho.query.get_or_404(id)
        despesa.ativo = not despesa.ativo
        
        db.session.commit()
        
        status = "ativada" if despesa.ativo else "desativada"
        flash(f'Despesa "{despesa.nome}" {status} com sucesso!', 'info')
        
    except Exception as e:
        flash(f'Erro ao alterar status da despesa: {str(e)}', 'danger')
    
    return redirect(url_for('financeiro.gerenciar_despesas_fixas'))

@financeiro_bp.route('/financeiro/despesas-fixas/excluir/<int:id>', methods=['POST'])
@login_required
def excluir_despesa_fixa(id):
    """Exclui permanentemente uma despesa fixa do banco de dados"""
    try:
        despesa = DespesaFixaConselho.query.get_or_404(id)
        nome_despesa = despesa.nome
        
        # Remover a despesa do banco de dados
        db.session.delete(despesa)
        db.session.commit()
        
        flash(f'Despesa fixa "{nome_despesa}" excluída com sucesso!', 'success')
        
    except Exception as e:
        db.session.rollback()
        flash(f'Erro ao excluir despesa fixa: {str(e)}', 'danger')
    
    return redirect(url_for('financeiro.gerenciar_despesas_fixas'))

@financeiro_bp.route('/financeiro/despesas-fixas/gerar-lancamentos', methods=['POST'])
@login_required
def gerar_lancamentos_despesas_fixas():
    """Gera obrigações automáticas para o mês baseado nas despesas fixas ativas."""
    mes = request.form.get('mes', type=int) or datetime.now().month
    ano = request.form.get('ano', type=int) or datetime.now().year

    resultado = gerar_obrigacoes_despesas_fixas(mes=mes, ano=ano)

    if resultado['erros']:
        flash(f'Erro ao gerar obrigações de despesas fixas: {resultado["erros"][0]}', 'danger')
    elif not resultado['criadas'] and not resultado['ja_existentes']:
        flash('Nenhuma despesa fixa ativa encontrada!', 'warning')
    else:
        mensagem = f'Obrigações de despesas fixas geradas: {len(resultado["criadas"])} criada(s)'
        if resultado['ja_existentes']:
            mensagem += f', {len(resultado["ja_existentes"])} já existente(s)'
        flash(mensagem, 'success')
    
    return redirect(url_for('financeiro.gerenciar_despesas_fixas'))


@financeiro_bp.route('/financeiro/gerar-lancamento-administrativo', methods=['POST'])
@login_required
def gerar_lancamento_administrativo():
    """Gera obrigação ADMIN_SEDE_30 (sem criar lançamento automático)."""
    try:
        mes = request.form.get('mes', type=int) or datetime.now().month
        ano = request.form.get('ano', type=int) or datetime.now().year
        resultado = gerar_obrigacao_admin_sede_30(mes=mes, ano=ano)

        if resultado['erro']:
            flash(f'Erro ao gerar obrigação administrativa: {resultado["erro"]}', 'danger')
            return redirect(request.referrer or url_for('financeiro.dashboard_moderno'))

        percentual = resultado['percentual']
        valor = float(resultado['valor_obrigacao'])
        if valor <= 0:
            flash(f'Não há base de cálculo para os {percentual:.0f}% administrativo no mês {mes:02d}/{ano}!', 'warning')
            return redirect(request.referrer or url_for('financeiro.dashboard_moderno'))

        if resultado['status'] == 'ja_existente':
            flash(f'Já existe obrigação de {percentual:.0f}% administrativo para {mes:02d}/{ano}!', 'warning')
            return redirect(request.referrer or url_for('financeiro.dashboard_moderno'))

        flash(
            f'Obrigação de {percentual:.0f}% administrativo criada: R$ {valor:.2f} para {mes:02d}/{ano} (sem lançamento automático).',
            'success'
        )
        
    except Exception as e:
        db.session.rollback()
        flash(f'Erro ao gerar obrigação administrativa: {str(e)}', 'danger')
    
    return redirect(request.referrer or url_for('financeiro.dashboard_moderno'))


@financeiro_bp.route('/financeiro/relatorio-caixa/preview')
@login_required
def relatorio_caixa_preview():
    """Mantém compatibilidade redirecionando para o relatório gerencial centralizado."""
    return redirect(url_for('financeiro.gerar_relatorio', tipo_relatorio='gerencial', mes=request.args.get('mes', type=int), ano=request.args.get('ano', type=int)))

@financeiro_bp.route('/financeiro/relatorio-sede/preview')
@login_required  
def relatorio_sede_preview():
    """Mantém compatibilidade redirecionando para o relatório oficial centralizado."""
    return redirect(url_for('financeiro.gerar_relatorio', tipo_relatorio='sede', mes=request.args.get('mes', type=int), ano=request.args.get('ano', type=int)))

@financeiro_bp.route('/financeiro/relatorio-caixa/pdf')
@login_required
def relatorio_caixa_pdf():
    """
    Gera o PDF do Relatório de Caixa usando ReportLab.
    Corrige o problema do botão PDF que piscava e retornava para a mesma tela.
    """
    mes = None
    ano = None

    try:
        current_app.logger.info("=== INICIO GERACAO PDF CAIXA ===")
        hoje = datetime.now()
        mes = request.args.get('mes', hoje.month, type=int)
        ano = request.args.get('ano', hoje.year, type=int)
        current_app.logger.info(f"Mes: {mes}, Ano: {ano}")

        current_app.logger.info("Buscando lancamentos...")
        lancamentos = Lancamento.query.filter(
            extract('month', Lancamento.data) == mes,
            extract('year', Lancamento.data) == ano
        ).order_by(
            Lancamento.data.asc(),
            Lancamento.id.asc()
        ).all()
        current_app.logger.info(f"Lancamentos encontrados: {len(lancamentos)}")

        # Calcular saldo anterior
        current_app.logger.info("Calculando saldo anterior...")
        saldo_anterior = Lancamento.calcular_saldo_ate_mes_anterior(mes, ano)
        current_app.logger.info(f"Saldo anterior: {saldo_anterior}")

        # Obter configuração
        current_app.logger.info("Obtendo configuracao...")
        config = Configuracao.obter_configuracao()
        current_app.logger.info(f"Configuracao OK - Logo: {config.logo if config else 'None'}")

        # Montar contexto de repasse à sede para renderização no PDF (informativo, sem alterar cálculos existentes)
        percentual_conselho = config.percentual_conselho if config and hasattr(config, 'percentual_conselho') and config.percentual_conselho else 30
        controle_repasse_sede = _montar_controle_repasse_sede(mes, ano, percentual_conselho)
        observacao_repasse_sede, _, _ = _obter_observacao_repasse_sede(
            mes,
            ano,
            controle_repasse_sede,
            tipo_relatorio='gerencial'
        )

        # Criar instância do gerador com configuração
        current_app.logger.info("Criando instancia RelatorioFinanceiro...")
        relatorio = RelatorioFinanceiro(config)
        current_app.logger.info("RelatorioFinanceiro criado OK")
        
        # Gerar PDF com todos os parâmetros necessários
        current_app.logger.info("Gerando PDF...")
        pdf_buffer = relatorio.gerar_relatorio_caixa(
            lancamentos,
            mes,
            ano,
            saldo_anterior,
            controle_repasse_sede=controle_repasse_sede,
            observacao_repasse_sede=observacao_repasse_sede
        )
        current_app.logger.info("PDF gerado OK")

        if not pdf_buffer:
            raise Exception("O gerador retornou um PDF vazio.")

        pdf_buffer.seek(0)
        tamanho = len(pdf_buffer.getvalue())
        current_app.logger.info(f"Tamanho do PDF: {tamanho} bytes")

        nome_arquivo = gerar_nome_arquivo_relatorio('caixa', mes, ano)
        current_app.logger.info(f"Enviando PDF: {nome_arquivo}")

        return send_file(
            pdf_buffer,
            mimetype='application/pdf',
            as_attachment=False,
            download_name=nome_arquivo
        )

    except Exception as e:
        import traceback

        current_app.logger.error("=== ERRO AO GERAR PDF DO RELATÓRIO DE CAIXA ===")
        current_app.logger.error(f"Mes: {mes}, Ano: {ano}")
        current_app.logger.error(f"Tipo do erro: {type(e).__name__}")
        current_app.logger.error(f"Mensagem: {str(e)}")
        current_app.logger.error("Traceback completo:")
        current_app.logger.error(traceback.format_exc())

        flash(f"Erro ao gerar PDF do relatório de caixa: {str(e)}", "danger")

        if mes and ano:
            return redirect(url_for("financeiro.relatorio_caixa", mes=mes, ano=ano))

        return redirect(url_for("financeiro.lista_lancamentos"))

@financeiro_bp.route('/financeiro/relatorio-sede/pdf')
@login_required
def relatorio_sede_pdf():
    """Gera PDF do relatório oficial para sede"""
    try:
        # Pegar mês e ano da query string com validação
        mes = request.args.get('mes', type=int)
        ano = request.args.get('ano', type=int)
        
        # Se não foram fornecidos na URL, usar o mês/ano atual
        if mes is None:
            mes = datetime.now().month
        if ano is None:
            ano = datetime.now().year
        
        # Validar valores
        if mes < 1 or mes > 12:
            mes = datetime.now().month
        if ano < 2020 or ano > 2030:
            ano = datetime.now().year
        
        # Filtrar lançamentos do mês
        lancamentos = Lancamento.query.filter(
            extract('month', Lancamento.data) == mes,
            extract('year', Lancamento.data) == ano
        ).all()
        
        # Buscar dados de configuração da igreja
        config = Configuracao.obter_configuracao()
        dados_igreja = {
            'cidade': config.cidade if config.cidade else 'Tietê',
            'bairro': config.bairro if config.bairro else 'Centro',
            'dirigente': config.dirigente if config.dirigente else 'Pastor Responsável',
            'tesoureiro': config.tesoureiro if config.tesoureiro else 'Tesoureiro(a)',
            'saldo_anterior': Lancamento.calcular_saldo_ate_mes_anterior(mes, ano)
        }
        
        percentual_conselho = config.percentual_conselho if config and hasattr(config, 'percentual_conselho') and config.percentual_conselho else 30
        totais = _calcular_totais_relatorio_sede(lancamentos, percentual_conselho)
        
        # Envios fixos obtidos da base de dados
        envios = DespesaFixaConselho.obter_despesas_para_relatorio()
        
        # Calcular total de envios (envios fixos + valor do conselho)
        total_envio_sede = sum(envios.values()) + totais['valor_conselho']
        
        # Obter configurações do sistema
        config = Configuracao.obter_configuracao()
        
        # Gerar PDF com ReportLab profissional
        relatorio = RelatorioFinanceiro(config)
        pdf_buffer = relatorio.gerar_relatorio_sede(lancamentos, mes, ano, dados_igreja['saldo_anterior'])
        
        # Gerar nome do arquivo
        nome_arquivo = gerar_nome_arquivo_relatorio('sede', mes, ano)
        
        return send_file(
            pdf_buffer,
            as_attachment=False,
            download_name=nome_arquivo,
            mimetype='application/pdf'
        )

    except Exception as e:
        flash(f'Erro ao gerar PDF do relatório da sede: {str(e)}', 'danger')
        return redirect(url_for('financeiro.relatorio_sede'))


# ========== EMISSOR DE RECIBOS ==========

@financeiro_bp.route('/financeiro/emitir-recibo', methods=['GET', 'POST'])
@login_required
def emitir_recibo():
    """Emissor de recibo para doações e ofertas - COM SALVAMENTO NO BANCO"""
    try:
        if request.method == 'POST':
            # Capturar dados do formulário
            nome_recebedor = request.form.get('nome_doador', '').strip()
            cpf_cnpj = request.form.get('cpf_cnpj', '').strip()
            valor_str = request.form.get('valor', '0').replace(',', '.')
            forma_pagamento = request.form.get('forma_pagamento', 'Dinheiro')
            referente_a = request.form.get('tipo_doacao', 'Pagamento')
            data_pagamento_str = request.form.get('data_doacao', '')
            observacoes = request.form.get('observacoes', '').strip()
            numero_recibo = request.form.get('numero_recibo', '').strip()
            
            # Validações básicas
            if not nome_recebedor:
                flash('Nome do recebedor é obrigatório', 'danger')
                return render_template('financeiro/emitir_recibo.html', dados={
                    'nome_doador': nome_recebedor,
                    'cpf_cnpj': cpf_cnpj,
                    'valor': valor_str,
                    'forma_pagamento': forma_pagamento,
                    'tipo_doacao': referente_a,
                    'data_doacao': data_pagamento_str,
                    'observacoes': observacoes
                })
            
            try:
                valor = float(valor_str)
                if valor <= 0:
                    raise ValueError()
            except:
                flash('Valor deve ser maior que zero', 'danger')
                return render_template('financeiro/emitir_recibo.html', dados={})
            
            # Converter data
            try:
                if data_pagamento_str:
                    data_pagamento = datetime.strptime(data_pagamento_str, '%Y-%m-%d').date()
                else:
                    data_pagamento = datetime.now().date()
            except:
                data_pagamento = datetime.now().date()
            
            # Gerar número do recibo se não fornecido
            if not numero_recibo:
                numero_recibo = Recibo.gerar_numero_recibo()
            
            # SALVAR NO BANCO
            recibo = Recibo(
                numero_recibo=numero_recibo,
                nome_recebedor=nome_recebedor,
                cpf_cnpj_recebedor=cpf_cnpj,
                valor=valor,
                data_pagamento=data_pagamento,
                referente_a=referente_a,
                forma_pagamento=forma_pagamento,
                observacoes=observacoes,
                criado_por=current_user.nome if hasattr(current_user, 'nome') else 'Sistema'
            )
            
            db.session.add(recibo)
            db.session.commit()
            
            # Preparar dados para PDF
            dados_recibo = {
                'numero_recibo': numero_recibo,
                'nome_doador': nome_recebedor,
                'cpf_cnpj': cpf_cnpj,
                'valor': valor_str,
                'forma_pagamento': forma_pagamento,
                'tipo_doacao': referente_a,
                'data_doacao': data_pagamento,
                'observacoes': observacoes
            }
            
            # Gerar PDF do recibo
            from app.utils.gerar_pdf_reportlab import gerar_recibo_pdf
            config = Configuracao.obter_configuracao()
            pdf_buffer = gerar_recibo_pdf(dados_recibo, config)
            
            # Marcar como PDF gerado
            recibo.pdf_gerado = True
            db.session.commit()
            
            flash(f'Recibo {numero_recibo} criado com sucesso!', 'success')
            
            # Retornar PDF
            nome_arquivo = f"recibo_{numero_recibo}.pdf"
            return send_file(
                pdf_buffer,
                as_attachment=True,
                download_name=nome_arquivo,
                mimetype='application/pdf'
            )
        
        # GET - Mostrar formulário
        return render_template('financeiro/emitir_recibo.html', dados={
            'data_doacao': datetime.now().strftime('%Y-%m-%d'),
            'forma_pagamento': 'Dinheiro',
            'tipo_doacao': 'Oferta'
        })
        
    except Exception as e:
        db.session.rollback()
        flash(f'Erro ao emitir recibo: {str(e)}', 'danger')
        return redirect(url_for('financeiro.lista_lancamentos'))


# ========== CRUD DE RECIBOS ==========

@financeiro_bp.route('/financeiro/recibos')
@login_required
def lista_recibos():
    """Lista todos os recibos emitidos"""
    try:
        # Filtros
        search = request.args.get('search', '')
        data_inicio = request.args.get('data_inicio', '')
        data_fim = request.args.get('data_fim', '')
        page = request.args.get('page', 1, type=int)
        
        # Query base
        query = Recibo.query
        
        # Aplicar filtros
        if search:
            query = query.filter(
                or_(
                    Recibo.numero_recibo.contains(search),
                    Recibo.nome_recebedor.contains(search),
                    Recibo.referente_a.contains(search)
                )
            )
        
        if data_inicio:
            query = query.filter(Recibo.data_pagamento >= datetime.strptime(data_inicio, '%Y-%m-%d').date())
        
        if data_fim:
            query = query.filter(Recibo.data_pagamento <= datetime.strptime(data_fim, '%Y-%m-%d').date())
        
        # Paginação
        recibos = query.order_by(Recibo.criado_em.desc()).paginate(
            page=page, per_page=20, error_out=False
        )
        
        # Métricas
        total_recibos = query.count()
        total_valor = sum(r.valor for r in query.all())
        
        return render_template('financeiro/lista_recibos.html',
                             recibos=recibos,
                             total_recibos=total_recibos,
                             total_valor=total_valor,
                             search=search,
                             data_inicio=data_inicio,
                             data_fim=data_fim)
                             
    except Exception as e:
        flash(f'Erro ao carregar recibos: {str(e)}', 'danger')
        return redirect(url_for('financeiro.lista_lancamentos'))


@financeiro_bp.route('/financeiro/recibos/novo', methods=['GET', 'POST'])
@login_required
def novo_recibo():
    """Cria um novo recibo e salva no banco"""
    try:
        if request.method == 'POST':
            # Capturar dados
            nome_recebedor = request.form.get('nome_doador', '').strip()
            cpf_cnpj = request.form.get('cpf_cnpj', '').strip()
            valor_str = request.form.get('valor', '0').replace(',', '.')
            forma_pagamento = request.form.get('forma_pagamento', 'Dinheiro')
            referente_a = request.form.get('tipo_doacao', 'Pagamento')
            data_pagamento_str = request.form.get('data_doacao', '')
            observacoes = request.form.get('observacoes', '').strip()
            numero_recibo = request.form.get('numero_recibo', '').strip()
            
            # Validações
            if not nome_recebedor:
                flash('Nome do recebedor é obrigatório', 'danger')
                return redirect(url_for('financeiro.novo_recibo'))
            
            try:
                valor = float(valor_str)
                if valor <= 0:
                    raise ValueError()
            except:
                flash('Valor inválido', 'danger')
                return redirect(url_for('financeiro.novo_recibo'))
            
            # Data
            try:
                if data_pagamento_str:
                    data_pagamento = datetime.strptime(data_pagamento_str, '%Y-%m-%d').date()
                else:
                    data_pagamento = datetime.now().date()
            except:
                data_pagamento = datetime.now().date()
            
            # Gerar número do recibo
            if not numero_recibo:
                numero_recibo = Recibo.gerar_numero_recibo()
            
            # Criar recibo
            recibo = Recibo(
                numero_recibo=numero_recibo,
                nome_recebedor=nome_recebedor,
                cpf_cnpj_recebedor=cpf_cnpj,
                valor=valor,
                data_pagamento=data_pagamento,
                referente_a=referente_a,
                forma_pagamento=forma_pagamento,
                observacoes=observacoes,
                criado_por=current_user.nome if hasattr(current_user, 'nome') else 'Sistema'
            )
            
            db.session.add(recibo)
            db.session.commit()
            
            flash('Recibo criado com sucesso!', 'success')
            
            # Gerar PDF automaticamente
            dados_recibo = {
                'numero_recibo': numero_recibo,
                'nome_doador': nome_recebedor,
                'cpf_cnpj': cpf_cnpj,
                'valor': valor_str,
                'forma_pagamento': forma_pagamento,
                'tipo_doacao': referente_a,
                'data_doacao': data_pagamento,
                'observacoes': observacoes
            }
            
            from app.utils.gerar_pdf_reportlab import gerar_recibo_pdf
            config = Configuracao.obter_configuracao()
            pdf_buffer = gerar_recibo_pdf(dados_recibo, config)
            
            # Marcar como PDF gerado
            recibo.pdf_gerado = True
            db.session.commit()
            
            # Retornar PDF
            nome_arquivo = f"recibo_{numero_recibo}.pdf"
            return send_file(
                pdf_buffer,
                as_attachment=True,
                download_name=nome_arquivo,
                mimetype='application/pdf'
            )
        
        # GET
        return render_template('financeiro/emitir_recibo.html', dados={
            'data_doacao': datetime.now().strftime('%Y-%m-%d'),
            'forma_pagamento': 'Dinheiro',
            'tipo_doacao': 'Pagamento'
        })
        
    except Exception as e:
        db.session.rollback()
        flash(f'Erro ao criar recibo: {str(e)}', 'danger')
        return redirect(url_for('financeiro.lista_recibos'))


@financeiro_bp.route('/financeiro/recibos/<int:id>')
@login_required
def visualizar_recibo(id):
    """Visualiza detalhes de um recibo"""
    try:
        recibo = Recibo.query.get_or_404(id)
        return render_template('financeiro/visualizar_recibo.html', recibo=recibo)
    except Exception as e:
        flash(f'Erro ao visualizar recibo: {str(e)}', 'danger')
        return redirect(url_for('financeiro.lista_recibos'))


@financeiro_bp.route('/financeiro/recibos/<int:id>/editar', methods=['GET', 'POST'])
@login_required
def editar_recibo(id):
    """Edita um recibo existente"""
    try:
        recibo = Recibo.query.get_or_404(id)
        
        if request.method == 'POST':
            # Capturar dados atualizados
            nome_recebedor = request.form.get('nome_doador', '').strip()
            cpf_cnpj = request.form.get('cpf_cnpj', '').strip()
            valor_str = request.form.get('valor', '0').replace(',', '.')
            forma_pagamento = request.form.get('forma_pagamento', 'Dinheiro')
            referente_a = request.form.get('tipo_doacao', 'Pagamento')
            data_pagamento_str = request.form.get('data_doacao', '')
            observacoes = request.form.get('observacoes', '').strip()
            
            # Validações
            if not nome_recebedor:
                flash('Nome do recebedor é obrigatório', 'danger')
                return render_template('financeiro/editar_recibo.html', recibo=recibo)
            
            try:
                valor = float(valor_str)
                if valor <= 0:
                    raise ValueError()
            except:
                flash('Valor inválido', 'danger')
                return render_template('financeiro/editar_recibo.html', recibo=recibo)
            
            # Data
            try:
                if data_pagamento_str:
                    data_pagamento = datetime.strptime(data_pagamento_str, '%Y-%m-%d').date()
                else:
                    data_pagamento = recibo.data_pagamento
            except:
                data_pagamento = recibo.data_pagamento
            
            # Atualizar recibo
            recibo.nome_recebedor = nome_recebedor
            recibo.cpf_cnpj_recebedor = cpf_cnpj
            recibo.valor = valor
            recibo.data_pagamento = data_pagamento
            recibo.referente_a = referente_a
            recibo.forma_pagamento = forma_pagamento
            recibo.observacoes = observacoes
            
            db.session.commit()
            
            flash(f'Recibo {recibo.numero_recibo} atualizado com sucesso!', 'success')
            return redirect(url_for('financeiro.visualizar_recibo', id=recibo.id))
        
        # GET - Mostrar formulário de edição
        return render_template('financeiro/editar_recibo.html', recibo=recibo)
        
    except Exception as e:
        db.session.rollback()
        flash(f'Erro ao editar recibo: {str(e)}', 'danger')
        return redirect(url_for('financeiro.lista_recibos'))


@financeiro_bp.route('/financeiro/recibos/<int:id>/pdf')
@login_required
def gerar_pdf_recibo(id):
    """Gera PDF de um recibo existente"""
    try:
        recibo = Recibo.query.get_or_404(id)
        
        # Preparar dados para geração do PDF
        dados_recibo = {
            'numero_recibo': recibo.numero_recibo,
            'nome_doador': recibo.nome_recebedor,
            'cpf_cnpj': recibo.cpf_cnpj_recebedor or '',
            'valor': str(recibo.valor),
            'forma_pagamento': recibo.forma_pagamento,
            'tipo_doacao': recibo.referente_a,
            'data_doacao': recibo.data_pagamento,
            'observacoes': recibo.observacoes or ''
        }
        
        from app.utils.gerar_pdf_reportlab import gerar_recibo_pdf
        config = Configuracao.obter_configuracao()
        pdf_buffer = gerar_recibo_pdf(dados_recibo, config)
        
        nome_arquivo = f"recibo_{recibo.numero_recibo}.pdf"
        return send_file(
            pdf_buffer,
            as_attachment=True,
            download_name=nome_arquivo,
            mimetype='application/pdf'
        )
        
    except Exception as e:
        flash(f'Erro ao gerar PDF: {str(e)}', 'danger')
        return redirect(url_for('financeiro.lista_recibos'))


@financeiro_bp.route('/financeiro/recibos/<int:id>/excluir', methods=['POST'])
@login_required
def excluir_recibo(id):
    """Exclui um recibo"""
    try:
        recibo = Recibo.query.get_or_404(id)
        numero = recibo.numero_recibo
        
        db.session.delete(recibo)
        db.session.commit()
        
        flash(f'Recibo {numero} excluído com sucesso!', 'success')
        
    except Exception as e:
        db.session.rollback()
        flash(f'Erro ao excluir recibo: {str(e)}', 'danger')
    
    return redirect(url_for('financeiro.lista_recibos'))