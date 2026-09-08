from __future__ import annotations

import os
import re
from datetime import datetime, timedelta, timezone
from io import BytesIO
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import cm, mm
from reportlab.platypus import HRFlowable, Image, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle


def _num(value):
    try:
        return round(float(value or 0), 2)
    except (TypeError, ValueError):
        return 0.0


def _tipo(lancamento):
    return str(getattr(lancamento, "tipo", "") or "").strip().lower()


def _categoria(lancamento):
    return str(getattr(lancamento, "categoria", "") or "").strip().lower()


def _valor_total_pagamento(pagamento):
    value = getattr(pagamento, "valor_total", None)
    return _num(getattr(pagamento, "valor", 0) if value is None else value)


def _valor_admin_pagamento(pagamento):
    value = getattr(pagamento, "valor_administrativo", None)
    if value is not None:
        return _num(value)
    total = _valor_total_pagamento(pagamento)
    fixas = getattr(pagamento, "valor_despesas_fixas", None)
    return total if fixas is None else round(max(total - _num(fixas), 0), 2)


def _valor_fixas_pagamento(pagamento):
    value = getattr(pagamento, "valor_despesas_fixas", None)
    if value is not None:
        return _num(value)
    return round(max(_valor_total_pagamento(pagamento) - _valor_admin_pagamento(pagamento), 0), 2)


def _pagamento_real(pagamento):
    if bool(getattr(pagamento, "pagamento_historico_sem_movimentacao", False)):
        return False
    return str(getattr(pagamento, "tipo_pagamento", "") or "").upper() != "HISTORICO_SEM_MOVIMENTACAO"


def _competencia(pagamento):
    texto = str(getattr(pagamento, "competencia", "") or "").strip()
    if texto:
        return texto
    mes = getattr(pagamento, "competencia_mes", None) or getattr(pagamento, "competencia_mes_ref", None)
    ano = getattr(pagamento, "competencia_ano", None) or getattr(pagamento, "competencia_ano_ref", None)
    return f"{int(mes):02d}/{int(ano)}" if mes and ano else "-"


def _refere_competencia_anterior(texto, mes, ano):
    alvo = (int(ano), int(mes))
    return any((int(aaaa), int(mm)) < alvo for mm, aaaa in re.findall(r"(?<!\d)(0?[1-9]|1[0-2])/(\d{4})(?!\d)", texto or ""))


def _pagamentos_mes(mes, ano):
    from app.financeiro.envios_sede_model import EnvioSede
    return EnvioSede.listar_pagamentos_mes(mes, ano)


def _obrigacoes_fixas(mes, ano):
    """Consulta read-only da competência; não cria/recalcula obrigação."""
    from app.financeiro.despesas_fixas_model import DespesaFixaConselho
    from app.financeiro.obrigacoes_model import ObrigacaoFinanceira

    obrigacoes = ObrigacaoFinanceira.query.filter(
        ObrigacaoFinanceira.competencia_mes == mes,
        ObrigacaoFinanceira.competencia_ano == ano,
        ObrigacaoFinanceira.tipo_obrigacao == "DESPESA_FIXA",
        ObrigacaoFinanceira.status != "CANCELADA",
    ).order_by(ObrigacaoFinanceira.id.asc()).all()
    if not obrigacoes:
        return [
            {"nome": item.nome, "valor": _num(item.valor_padrao)}
            for item in DespesaFixaConselho.obter_despesas_ativas()
            if _num(item.valor_padrao) > 0
        ]

    nomes = {item.id: item.nome for item in DespesaFixaConselho.query.all()}
    itens = []
    for obrigacao in obrigacoes:
        nome = nomes.get(getattr(obrigacao, "referencia_origem_id", None))
        if not nome:
            nome = str(getattr(obrigacao, "descricao", "") or "Despesa fixa").strip()
            nome = re.sub(r"\s*-\s*Despesa Fixa\s+\d{2}/\d{4}\s*$", "", nome, flags=re.I)
        itens.append({"nome": nome, "valor": _num(obrigacao.valor_devido)})
    return itens


def montar_read_model_sede(lancamentos, mes, ano, saldo_anterior, percentual_conselho, pagamentos=None, obrigacoes_fixas=None):
    """Monta somente a visão oficial. Não grava, recalcula ou regulariza fatos financeiros."""
    dados = dict(
        saldo_anterior=_num(saldo_anterior), dizimos=0.0, ofertas_alcadas=0.0,
        oferta_omn=0.0, rendimentos=0.0, outras_entradas=0.0,
        total_entradas=0.0, total_saidas=0.0,
    )
    for lancamento in lancamentos or []:
        if not bool(getattr(lancamento, "impacta_financeiro", True)):
            continue
        tipo, valor, categoria = _tipo(lancamento), _num(getattr(lancamento, "valor", 0)), _categoria(lancamento)
        if tipo == "entrada":
            dados["total_entradas"] = round(dados["total_entradas"] + valor, 2)
            if "dízimo" in categoria or "dizimo" in categoria:
                chave = "dizimos"
            elif "oferta" in categoria and ("omn" in categoria or "missionaria" in categoria or "missionária" in categoria):
                chave = "oferta_omn"
            elif "oferta" in categoria and not any(x in categoria for x in ("outras", "especial", "voluntaria", "voluntária")):
                chave = "ofertas_alcadas"
            elif any(x in categoria for x in ("rendimento", "juros", "aplicacao", "aplicação")):
                chave = "rendimentos"
            else:
                chave = "outras_entradas"
            dados[chave] = round(dados[chave] + valor, 2)
        elif tipo in {"saída", "saida"}:
            dados["total_saidas"] = round(dados["total_saidas"] + valor, 2)

    origem_pagamentos = list(pagamentos if pagamentos is not None else _pagamentos_mes(mes, ano))
    unicos, ids = [], set()
    for pagamento in origem_pagamentos:
        if not _pagamento_real(pagamento):
            continue
        chave = getattr(pagamento, "id", None) or id(pagamento)
        if chave not in ids:
            ids.add(chave)
            unicos.append(pagamento)

    pagamentos_model, total_pago, total_admin, total_fixas, historico = [], 0.0, 0.0, 0.0, False
    for pagamento in unicos:
        comp = _competencia(pagamento)
        total, admin, fixas = _valor_total_pagamento(pagamento), _valor_admin_pagamento(pagamento), _valor_fixas_pagamento(pagamento)
        total_pago, total_admin, total_fixas = round(total_pago + total, 2), round(total_admin + admin, 2), round(total_fixas + fixas, 2)
        historico = historico or _refere_competencia_anterior(comp, mes, ano)
        pagamentos_model.append(dict(data=getattr(pagamento, "data_pagamento", None), competencia=comp, administrativo=admin, despesas_fixas=fixas, total=total))

    fixas_model = []
    for item in list(obrigacoes_fixas if obrigacoes_fixas is not None else _obrigacoes_fixas(mes, ano)):
        if isinstance(item, dict):
            nome, valor = str(item.get("nome") or item.get("descricao") or "Despesa fixa").strip(), _num(item.get("valor", item.get("valor_devido", 0)))
        else:
            nome = str(getattr(item, "nome", None) or getattr(item, "descricao", None) or "Despesa fixa").strip()
            valor = _num(getattr(item, "valor", getattr(item, "valor_devido", getattr(item, "valor_padrao", 0))))
        if valor > 0:
            fixas_model.append({"nome": nome, "valor": valor})

    dados["base_30"] = round(dados["dizimos"] + dados["ofertas_alcadas"], 2)
    dados["percentual_conselho"] = _num(percentual_conselho)
    dados["valor_30"] = round(dados["base_30"] * dados["percentual_conselho"] / 100, 2)
    dados["obrigacoes_fixas"] = fixas_model
    dados["total_fixas_competencia"] = round(sum(x["valor"] for x in fixas_model), 2)
    dados["total_competencia"] = round(dados["valor_30"] + dados["total_fixas_competencia"], 2)
    dados["pagamentos"] = pagamentos_model
    dados["total_admin_pago"], dados["total_fixas_pago"], dados["total_pago_sede"] = total_admin, total_fixas, total_pago
    dados["despesas_gerais"] = round(dados["total_saidas"] - total_pago, 2)
    dados["resultado_mes"] = round(dados["total_entradas"] - dados["total_saidas"], 2)
    dados["saldo_final"] = round(dados["saldo_anterior"] + dados["resultado_mes"], 2)
    dados["justificativa"] = "Foram registrados pagamentos neste período referentes à quitação de competências anteriores junto à Sede." if pagamentos_model and historico else None
    return dados


def _moeda(relatorio, valor):
    return relatorio._formatar_moeda(_num(valor))


def _estilo(nome, **kwargs):
    return ParagraphStyle(nome, **kwargs)


def _tabela(linhas, larguras, cabecalho=False, total=None, fonte=8.2, repeat_rows=0):
    tabela = Table(linhas, colWidths=larguras, repeatRows=repeat_rows)
    estilo = [
        ("FONTNAME", (0, 0), (-1, -1), "Helvetica"), ("FONTSIZE", (0, 0), (-1, -1), fonte),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"), ("GRID", (0, 0), (-1, -1), .35, colors.HexColor("#B8C2CC")),
        ("TOPPADDING", (0, 0), (-1, -1), 3.2), ("BOTTOMPADDING", (0, 0), (-1, -1), 3.2),
        ("LEFTPADDING", (0, 0), (-1, -1), 4), ("RIGHTPADDING", (0, 0), (-1, -1), 4),
    ]
    if cabecalho:
        estilo += [("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#254B3B")), ("TEXTCOLOR", (0, 0), (-1, 0), colors.white), ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"), ("ALIGN", (0, 0), (-1, 0), "CENTER")]
    if total is not None:
        estilo += [("BACKGROUND", (0, total), (-1, total), colors.HexColor("#EDF4F0")), ("FONTNAME", (0, total), (-1, total), "Helvetica-Bold")]
    tabela.setStyle(TableStyle(estilo))
    return tabela


def _titulo(texto):
    return Paragraph(texto, _estilo("D23D49Secao", fontName="Helvetica-Bold", fontSize=8.8, leading=10, textColor=colors.HexColor("#254B3B"), spaceBefore=2, spaceAfter=2.5))


def _logo(config):
    caminho = str(getattr(config, "logo", "") or "").strip()
    if not caminho:
        return None
    try:
        from flask import current_app
        if caminho.startswith("static/"):
            return os.path.join(current_app.static_folder, caminho[7:])
        return caminho if os.path.isabs(caminho) else os.path.join(current_app.root_path, "..", caminho)
    except Exception:
        return caminho if os.path.isabs(caminho) else None


def _cabecalho(relatorio, mes, ano):
    c, elementos = relatorio.config, []
    logo = _logo(c)
    if logo and os.path.exists(logo):
        imagem = Image(logo, width=34 * mm, height=23 * mm); imagem.hAlign = "CENTER"; elementos += [imagem, Spacer(1, 2 * mm)]
    nome = str(getattr(c, "nome_igreja", "") or "Igreja não informada")
    cidade, bairro = str(getattr(c, "cidade", "") or "Não informada"), str(getattr(c, "bairro", "") or "Não informado")
    dirigente = str(getattr(c, "presidente", "") or getattr(c, "dirigente", "") or "Não informado")
    tesoureiro = str(getattr(c, "primeiro_tesoureiro", "") or getattr(c, "tesoureiro", "") or "Não informado")
    elementos += [
        Paragraph(escape(nome), _estilo("D23D49Titulo", fontName="Helvetica-Bold", fontSize=12, leading=14, alignment=TA_CENTER, textColor=colors.HexColor("#254B3B"))),
        Paragraph(f"RELATÓRIO OFICIAL À SEDE · COMPETÊNCIA {mes:02d}/{ano}", _estilo("D23D49Sub", fontName="Helvetica-Bold", fontSize=9.5, leading=11, alignment=TA_CENTER, spaceAfter=3)),
    ]
    rot = _estilo("D23D49Rot", fontName="Helvetica-Bold", fontSize=8, leading=9.5)
    val = _estilo("D23D49Val", fontName="Helvetica", fontSize=8, leading=9.5)
    info = [[Paragraph("Cidade", rot), Paragraph(escape(cidade), val), Paragraph("Bairro", rot), Paragraph(escape(bairro), val)], [Paragraph("Dirigente", rot), Paragraph(escape(dirigente), val), Paragraph("Tesoureiro", rot), Paragraph(escape(tesoureiro), val)]]
    t = _tabela(info, [2.1*cm, 6*cm, 2.1*cm, 6*cm], fonte=8); t.setStyle(TableStyle([("BACKGROUND", (0,0),(0,-1),colors.HexColor("#F3F6F4")), ("BACKGROUND",(2,0),(2,-1),colors.HexColor("#F3F6F4"))]))
    return elementos + [t, Spacer(1, 4*mm)]


def _duas_colunas(relatorio, titulo, linhas, total=None):
    t = _tabela(linhas, [13.2*cm, 4.5*cm], total=total, fonte=8.2); t.setStyle(TableStyle([("ALIGN",(1,0),(1,-1),"RIGHT")]))
    return [_titulo(titulo), t, Spacer(1, 2.5*mm)]


def _secoes(relatorio, d, mes, ano):
    arrec = [["Saldo anterior", _moeda(relatorio,d["saldo_anterior"])], ["Dízimos",_moeda(relatorio,d["dizimos"])], ["Ofertas Alçadas",_moeda(relatorio,d["ofertas_alcadas"])], ["Oferta OMN / específica",_moeda(relatorio,d["oferta_omn"])]]
    if d["rendimentos"]: arrec.append(["Rendimentos financeiros",_moeda(relatorio,d["rendimentos"])])
    if d["outras_entradas"]: arrec.append(["Outras entradas",_moeda(relatorio,d["outras_entradas"])])
    arrec.append(["TOTAL DE ENTRADAS / ARRECADAÇÃO",_moeda(relatorio,d["total_entradas"])])
    resultado = [["Despesas Gerais da Igreja",_moeda(relatorio,d["despesas_gerais"])], ["Pagamentos realizados à Sede no período",_moeda(relatorio,d["total_pago_sede"])], ["Total de Saídas Financeiras",_moeda(relatorio,d["total_saidas"])], ["Resultado do Mês",_moeda(relatorio,d["resultado_mes"])], ["SALDO DISPONÍVEL / FINAL",_moeda(relatorio,d["saldo_final"])]]
    competencia = [["Base sujeita ao repasse (Dízimos + Ofertas Alçadas)",_moeda(relatorio,d["base_30"])], [f"{d['percentual_conselho']:.0f}% Conselho Administrativo",_moeda(relatorio,d["valor_30"])]] + [[x["nome"],_moeda(relatorio,x["valor"])] for x in d["obrigacoes_fixas"]] + [["TOTAL DA COMPETÊNCIA",_moeda(relatorio,d["total_competencia"])]]
    return _duas_colunas(relatorio,"ARRECADAÇÃO FINANCEIRA NO MÊS",arrec,len(arrec)-1) + _duas_colunas(relatorio,"DESPESAS E RESULTADO",resultado,len(resultado)-1) + _duas_colunas(relatorio,f"VALORES DESTINADOS À SEDE · COMPETÊNCIA {mes:02d}/{ano}",competencia,len(competencia)-1)


def _secao_pagamentos(relatorio, d):
    if not d["pagamentos"]: return []
    hs = _estilo("D23D49Head", fontName="Helvetica-Bold", fontSize=7.2, leading=8, textColor=colors.white, alignment=TA_CENTER)
    cs = _estilo("D23D49Cell", fontName="Helvetica", fontSize=7.2, leading=8.2)
    linhas = [[Paragraph(x,hs) for x in ("DATA","COMPETÊNCIA / REFERÊNCIA","ADMINISTRATIVO","DESPESAS FIXAS","TOTAL")]]
    for p in d["pagamentos"]:
        data = p["data"].strftime("%d/%m/%Y") if p["data"] else "-"
        linhas.append([data, Paragraph(escape(p["competencia"]),cs), _moeda(relatorio,p["administrativo"]), _moeda(relatorio,p["despesas_fixas"]), _moeda(relatorio,p["total"])])
    linhas.append(["","TOTAL PAGO",_moeda(relatorio,d["total_admin_pago"]),_moeda(relatorio,d["total_fixas_pago"]),_moeda(relatorio,d["total_pago_sede"])])
    t = _tabela(linhas,[2.3*cm,6*cm,3.1*cm,3.2*cm,3.5*cm],cabecalho=True,total=len(linhas)-1,fonte=7.2,repeat_rows=1)
    t.setStyle(TableStyle([("ALIGN",(0,1),(0,-1),"CENTER"),("ALIGN",(2,1),(4,-1),"RIGHT")]))
    return [_titulo("PAGAMENTOS REALIZADOS NO MÊS"),t,Spacer(1,2.5*mm)]


def _final(relatorio, d):
    elementos = []
    if d.get("justificativa"):
        js = _estilo("D23D49Just",fontName="Helvetica",fontSize=7.8,leading=9.3,textColor=colors.HexColor("#4B5563"),borderColor=colors.HexColor("#D1D5DB"),borderWidth=.5,borderPadding=4,backColor=colors.HexColor("#F9FAFB"))
        elementos += [_titulo("JUSTIFICATIVA CONTÁBIL"),Paragraph(escape(d["justificativa"]),js),Spacer(1,2*mm)]
    c = relatorio.config
    dirigente = escape(str(getattr(c,"presidente","") or getattr(c,"dirigente","") or "")); tesoureiro = escape(str(getattr(c,"primeiro_tesoureiro","") or getattr(c,"tesoureiro","") or ""))
    ass = _estilo("D23D49Ass",fontName="Helvetica",fontSize=7.7,leading=9,alignment=TA_CENTER); linha="________________________________________"
    t = Table([[Paragraph(f"{linha}<br/><b>Assinatura do Dirigente</b><br/>{dirigente}",ass),Paragraph(f"{linha}<br/><b>Assinatura do Tesoureiro</b><br/>{tesoureiro}",ass)]],colWidths=[8.7*cm,8.7*cm])
    t.setStyle(TableStyle([("ALIGN",(0,0),(-1,-1),"CENTER"),("TOPPADDING",(0,0),(-1,-1),6)])); elementos += [Spacer(1,7*mm),t]
    agora=datetime.now(timezone(timedelta(hours=-3))); meses=["","janeiro","fevereiro","março","abril","maio","junho","julho","agosto","setembro","outubro","novembro","dezembro"]
    cidade=str(getattr(c,"cidade","") or ""); local=f"{cidade}, " if cidade else ""; rod=f"{local}{agora.day} de {meses[agora.month]} de {agora.year} · Sistema Administrativo OBPC"
    rs=_estilo("D23D49Rod",fontName="Helvetica",fontSize=6.8,leading=8,textColor=colors.HexColor("#6B7280"),alignment=TA_CENTER)
    return elementos+[Spacer(1,2*mm),HRFlowable(width="100%",thickness=.35,color=colors.HexColor("#D1D5DB")),Spacer(1,mm),Paragraph(escape(rod),rs)]


def gerar_relatorio_sede_oficial(relatorio, lancamentos, mes, ano, saldo_anterior=0, pagamentos=None, obrigacoes_fixas=None):
    """PDF oficial da Sede, alimentado somente por fatos econômicos homologados."""
    d = montar_read_model_sede(lancamentos,mes,ano,saldo_anterior,_num(getattr(relatorio.config,"percentual_conselho",30) or 30),pagamentos,obrigacoes_fixas)
    relatorio.buffer=BytesIO(); doc=SimpleDocTemplate(relatorio.buffer,pagesize=A4,rightMargin=1.2*cm,leftMargin=1.2*cm,topMargin=.9*cm,bottomMargin=1*cm,title=f"Relatório Oficial à Sede {mes:02d}/{ano}",author="Sistema Administrativo OBPC")
    elementos=_cabecalho(relatorio,mes,ano)+_secoes(relatorio,d,mes,ano)+_secao_pagamentos(relatorio,d)+_final(relatorio,d)
    doc.build(elementos); relatorio.buffer.seek(0); return relatorio.buffer


def _gerar_relatorio_sede_d23d49(self, lancamentos, mes, ano, saldo_anterior=0):
    return gerar_relatorio_sede_oficial(self,lancamentos,mes,ano,saldo_anterior)


def instalar_relatorio_sede_oficial():
    """Troca apenas a apresentação da Sede; Caixa e recibos permanecem no legado."""
    from app.utils.gerar_pdf_reportlab import RelatorioFinanceiro
    atual=getattr(RelatorioFinanceiro,"gerar_relatorio_sede",None)
    if getattr(atual,"_d23d49_relatorio_sede",False): return
    _gerar_relatorio_sede_d23d49._d23d49_relatorio_sede=True
    RelatorioFinanceiro.gerar_relatorio_sede=_gerar_relatorio_sede_d23d49
