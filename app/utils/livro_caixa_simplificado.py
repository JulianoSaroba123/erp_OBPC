"""Livro Caixa interno simplificado do ERP OBPC.

Fluxo ECONOMICO consolidado Banco/Pix + Dinheiro. Evidencias conciliadas
nao sao movimentos economicos e nao entram no extrato ou totais.

Nao consulta banco, nao grava registros, nao executa migracoes.
"""
from __future__ import annotations

from collections import defaultdict
from datetime import date
from decimal import Decimal, ROUND_HALF_UP
from io import BytesIO
from pathlib import Path
from unicodedata import normalize, category as unicode_category
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT
from reportlab.lib.units import cm
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase.pdfmetrics import stringWidth
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, KeepTogether,
)

_CENTAVO = Decimal('0.01')
_NAVY = colors.HexColor('#0b1b3a')
_GREEN = colors.HexColor('#25704b')
_BG = colors.HexColor('#f4f7fa')
_GRAY = colors.HexColor('#596574')


def _dinheiro(valor):
    return Decimal(str(0 if valor is None else valor)).quantize(
        _CENTAVO, rounding=ROUND_HALF_UP
    )


def _real(valor):
    negativo = '-' if _dinheiro(valor) < 0 else ''
    numero = f'{abs(_dinheiro(valor)):,.2f}'.replace(',', '#').replace('.', ',').replace('#', '.')
    return f'{negativo}R$ {numero}'


def _normal(texto):
    texto = normalize('NFD', str(texto or '').strip().lower())
    return ''.join(c for c in texto if unicode_category(c) != 'Mn')


def _tipo(lancamento):
    # Respeitar a propriedade economica Lancamento.tipo da aplicacao.
    return _normal(getattr(lancamento, 'tipo', ''))


def _conta(lancamento):
    conta = _normal(getattr(lancamento, 'conta', ''))
    if 'pix' in conta:
        return 'Pix', 'Banco/Pix'
    if 'banco' in conta or 'conta' in conta:
        return 'Banco', 'Banco/Pix'
    return 'Dinheiro', 'Dinheiro'


_GRUPOS_ENTRADA = (
    'Dízimos', 'Ofertas de culto', 'Outras ofertas', 'OMN - Oferta Missionária',
    'Outras entradas',
)


def _natureza_entrada(lancamento):
    """Subgrupos não sobrepostos, usados apenas como detalhamento das entradas."""
    categoria = _normal(getattr(lancamento, 'categoria', ''))
    if 'dizimo' in categoria:
        return 'Dízimos'
    # A identificação missionária tem precedência sobre a oferta genérica.
    if ('omn' in categoria or 'missionaria' in categoria):
        return 'OMN - Oferta Missionária'
    if ('outras ofertas' in categoria or 'outra oferta' in categoria
            or 'oferta especial' in categoria or 'oferta voluntaria' in categoria):
        return 'Outras ofertas'
    if 'oferta' in categoria:
        return 'Ofertas de culto'
    return 'Outras entradas'


def _eh_envio_sede(lancamento):
    """Identifica SAÍDAS efetivas à Sede, nunca obrigação ou previsão."""
    categoria = _normal(getattr(lancamento, 'categoria', ''))
    descricao = _normal(getattr(lancamento, 'descricao', ''))
    if categoria in (
        'contrib. sede', 'contrib sede', 'repasse a sede', 'contribuicao sede',
        'envio sede', 'envio a sede', 'envios a sede',
    ):
        return True
    return descricao.startswith((
        'repasse a sede', '30% administrativo - conselho sede',
        'acerto historico sede', 'envio a sede',
    ))


def apurar_livro_caixa(lancamentos, saldo_anterior):
    """Apuracao independente e testavel, sem modificar objetos persistidos."""
    ordenados = sorted(lancamentos, key=lambda l: (
        getattr(l, 'data', date.min), int(getattr(l, 'id', 0) or 0)
    ))
    saldo = _dinheiro(saldo_anterior)
    entradas = saidas = _dinheiro(0)
    evidencia_qtd = 0
    evidencia_valor = _dinheiro(0)
    contas = defaultdict(lambda: {'entradas': _dinheiro(0), 'saidas': _dinheiro(0)})
    movimentos = []
    entradas_por_natureza = {nome: _dinheiro(0) for nome in _GRUPOS_ENTRADA}
    enviado_sede = _dinheiro(0)

    for lancamento in ordenados:
        tipo = _tipo(lancamento)
        valor = _dinheiro(getattr(lancamento, 'valor', 0))
        if tipo == 'evidencia':
            evidencia_qtd += 1
            evidencia_valor += valor
            continue
        if tipo not in ('entrada', 'saida'):
            # Outros estados nao sao classificados como gasto por omissao.
            continue
        if valor < 0:
            raise ValueError('Valor de lancamento economico negativo: normalizar na origem.')
        conta, grupo = _conta(lancamento)
        entrada, saida = (_dinheiro(0), _dinheiro(0))
        if tipo == 'entrada':
            entrada = valor
            entradas += valor
            saldo += valor
            contas[grupo]['entradas'] += valor
            entradas_por_natureza[_natureza_entrada(lancamento)] += valor
        else:
            saida = valor
            saidas += valor
            saldo -= valor
            contas[grupo]['saidas'] += valor
            if _eh_envio_sede(lancamento):
                enviado_sede += valor
        movimentos.append({
            'data': getattr(lancamento, 'data'),
            'descricao': (getattr(lancamento, 'descricao', '') or 'Sem historico'),
            'categoria': (getattr(lancamento, 'categoria', '') or 'Sem categoria'),
            'conta': conta,
            'entrada': entrada,
            'saida': saida,
            'saldo': saldo,
        })
    return {
        'saldo_anterior': _dinheiro(saldo_anterior),
        'entradas': entradas, 'saidas': saidas, 'saldo_final': saldo,
        'movimentos': movimentos, 'contas': dict(contas),
        'evidencias_qtd': evidencia_qtd, 'evidencias_valor': evidencia_valor,
        'entradas_por_natureza': entradas_por_natureza,
        'enviado_sede': enviado_sede,
        'demais_saidas': saidas - enviado_sede,
    }


def _historico_para_pdf(texto, largura, fonte='Helvetica', tamanho=8):
    """Quebra em duas linhas quando a renderizacao natural isolaria a ultima palavra.

    Preserva integralmente o historico no PDF. Nao altera nenhum lancamento.
    """
    palavras = str(texto or '').split()
    if len(palavras) < 3:
        return escape(str(texto or ''))
    linhas, atual = [], ''
    for palavra in palavras:
        candidato = (atual + ' ' + palavra).strip()
        if not atual or stringWidth(candidato, fonte, tamanho) <= largura:
            atual = candidato
        else:
            linhas.append(atual)
            atual = palavra
    if atual:
        linhas.append(atual)
    if len(linhas) != 2 or len(linhas[-1].split()) > 1:
        return escape(str(texto or ''))

    # A quebra natural criou uma linha com apenas uma palavra no fim.
    # Redistribuir as palavras, sem truncar e sem gerar uma terceira linha.
    candidatos = []
    conectivos = {'a', 'as', 'ao', 'aos', 'da', 'das', 'de', 'do', 'dos', 'e', 'em', 'o', 'os', 'para'}
    for indice in range(1, len(palavras)):
        esquerda = ' '.join(palavras[:indice])
        direita = ' '.join(palavras[indice:])
        largura_esquerda = stringWidth(esquerda, fonte, tamanho)
        largura_direita = stringWidth(direita, fonte, tamanho)
        if largura_esquerda > largura or largura_direita > largura:
            continue
        penalidade = 25 if palavras[indice-1].lower() in conectivos else 0
        penalidade += 25 if palavras[indice].lower() in conectivos else 0
        candidatos.append((abs(largura_esquerda - largura_direita) + penalidade, esquerda, direita))
    if candidatos:
        _, esquerda, direita = min(candidatos, key=lambda item: item[0])
        return escape(esquerda) + '<br/>' + escape(direita)
    return escape(str(texto or ''))


def _logo_igreja(config):
    """Usa somente imagem existente em app/static, sem regenerar a marca."""
    static = Path(__file__).resolve().parents[1] / 'static'
    preferida = str(getattr(config, 'logo', '') or '')
    candidatos = [Path(preferida).name, 'Logo_OBPC.jpg', 'logo_obpc_novo.jpg']
    for nome in candidatos:
        if not nome or nome in ('.', '..'):
            continue
        caminho = static / nome
        if caminho.is_file():
            return caminho
    return None


def gerar_livro_caixa_simplificado(lancamentos, mes, ano, saldo_anterior=0,
                                   configuracao=None, identificacao_teste=None):
    """Gera PDF em memoria. Nao grava, nao concilia e nao recalcula obrigacoes."""
    if not (1 <= int(mes) <= 12) or not (2020 <= int(ano) <= 2100):
        raise ValueError('Competencia invalida')
    dados = apurar_livro_caixa(lancamentos, saldo_anterior)
    buf = BytesIO()
    doc = SimpleDocTemplate(
        buf, pagesize=A4, leftMargin=1.45*cm, rightMargin=1.45*cm,
        topMargin=1.2*cm, bottomMargin=1.25*cm,
        title=f'Livro Caixa Interno OBPC {int(mes):02d}/{int(ano)}',
        author='ERP OBPC', pageCompression=1,
    )
    normal = ParagraphStyle('ObpcLC_Normal', fontName='Helvetica', fontSize=8, leading=10.4, textColor=_NAVY)
    minusculo = ParagraphStyle('ObpcLC_Small', parent=normal, fontSize=6.7, leading=8.5)
    titulo = ParagraphStyle('ObpcLC_Title', parent=normal, fontName='Helvetica-Bold', fontSize=15, leading=18)
    subtitulo = ParagraphStyle('ObpcLC_Subtitle', parent=normal, fontSize=9, leading=12, textColor=_GRAY)
    cabeca = ParagraphStyle('ObpcLC_Head', parent=normal, fontName='Helvetica-Bold', fontSize=8, textColor=colors.white)
    secao = ParagraphStyle('ObpcLC_Section', parent=normal, fontName='Helvetica-Bold', fontSize=10, leading=14)
    valor = ParagraphStyle('ObpcLC_Val', parent=normal, alignment=TA_RIGHT)
    val_negrito = ParagraphStyle('ObpcLC_ValBold', parent=valor, fontName='Helvetica-Bold')

    def P(texto, estilo=normal):
        return Paragraph(str(texto), estilo)

    cidade = escape(str(getattr(configuracao, 'cidade', 'Tietê') or 'Tietê'))
    titulo_igreja = P('IGREJA O BRASIL PARA CRISTO', ParagraphStyle(
        'ObpcLC_Igreja', parent=normal, fontName='Helvetica-Bold', fontSize=9, leading=12))
    subt = P(f'{cidade} / SP  |  Competência: {int(mes):02d}/{int(ano)} (mês civil)', subtitulo)
    tit = P('LIVRO CAIXA INTERNO', titulo)
    blocos = [titulo_igreja, tit, subt]
    logo = _logo_igreja(configuracao)
    if logo:
        try:
            reader = ImageReader(str(logo))
            w, h = reader.getSize()
            escala = min(2.45*cm/w, 1.65*cm/h)
            figura = Image(str(logo), width=w*escala, height=h*escala)
            blocos = [Table([[figura, [titulo_igreja, tit, subt]]], colWidths=[3.1*cm, 14.9*cm],
                            style=[('VALIGN', (0,0),(-1,-1),'MIDDLE'), ('LEFTPADDING',(0,0),(-1,-1),0),
                                   ('RIGHTPADDING',(0,0),(-1,-1),0), ('TOPPADDING',(0,0),(-1,-1),0),
                                   ('BOTTOMPADDING',(0,0),(-1,-1),0)])]
        except Exception:
            pass
    elem = list(blocos)
    elem.append(Spacer(1, 0.18*cm))
    if identificacao_teste:
        elem.extend([P(f'<font color="#9b3b3b"><b>{escape(str(identificacao_teste))}</b></font>', subtitulo), Spacer(1, 0.12*cm)])
    elem.append(P('Movimentação financeira consolidada: Banco, Pix e Dinheiro. O saldo abaixo não representa exclusivamente o caixa físico.', minusculo))
    elem.append(Spacer(1, 0.3*cm))

    # Tabela de livro caixa: evidencia conciliada nao aparece como gasto.
    colunas = ['DATA', 'HISTÓRICO / CATEGORIA', 'CONTA', 'ENTRADA', 'SAÍDA', 'SALDO']
    linhas = [[P(escape(c), cabeca) for c in colunas]]
    abertura = [P(f'01/{int(mes):02d}/{int(ano)}', minusculo), P('<b>SALDO ANTERIOR</b>', normal),
                P('-', minusculo), '', '', P(_real(dados['saldo_anterior']), val_negrito)]
    linhas.append(abertura)
    for m in dados['movimentos']:
        descr = _historico_para_pdf(m['descricao'], largura=6.35*cm - 8)
        categoria = escape(str(m['categoria']))
        hist = P(f'{descr}<br/><font size="6.6" color="#596574">{categoria}</font>', normal)
        linhas.append([
            P(m['data'].strftime('%d/%m/%Y'), minusculo), hist,
            P(escape(m['conta']), minusculo),
            P(_real(m['entrada']), valor) if m['entrada'] else '',
            P(_real(m['saida']), valor) if m['saida'] else '',
            P(_real(m['saldo']), valor),
        ])
    larguras = [1.8*cm, 6.35*cm, 1.65*cm, 2.45*cm, 2.45*cm, 3.3*cm]  # 18 cm
    tabela = Table(linhas, colWidths=larguras, repeatRows=1, hAlign='LEFT', splitByRow=1)
    tabela.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), _NAVY),
        ('BACKGROUND', (0,1), (-1,1), _BG),
        ('ROWBACKGROUNDS', (0,2), (-1,-1), [colors.white, colors.HexColor('#f7f9fb')]),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('ALIGN', (3,1), (-1,-1), 'RIGHT'),
        ('LINEBELOW', (0,0), (-1,0), 0.7, _NAVY),
        ('LINEBELOW', (0,1), (-1,-1), 0.3, colors.HexColor('#c7cdd5')),
        ('TOPPADDING', (0,0), (-1,0), 8), ('BOTTOMPADDING',(0,0),(-1,0),8),
        ('TOPPADDING', (0,1),(-1,-1), 3), ('BOTTOMPADDING',(0,1),(-1,-1),3),
        ('LEFTPADDING', (0,0),(-1,-1),4), ('RIGHTPADDING',(0,0),(-1,-1),4),
    ]))
    elem.append(tabela)
    elem.append(Spacer(1, 0.45*cm))

    # Fechamento em um unico bloco; nenhuma obrigacao da sede misturada.
    tot = dados
    resumo = Table([
        [P('FECHAMENTO DO MÊS', cabeca), ''],
        [P('Saldo anterior', normal), P(_real(tot['saldo_anterior']), val_negrito)],
        [P('Total de entradas', normal), P(_real(tot['entradas']), val_negrito)],
        [P('Total de saídas', normal), P(_real(tot['saidas']), val_negrito)],
        [P('SALDO FINAL', secao), P(_real(tot['saldo_final']), val_negrito)],
    ], colWidths=[12.0*cm, 6.0*cm], style=TableStyle([
        ('SPAN',(0,0),(-1,0)), ('BACKGROUND',(0,0),(-1,0),_NAVY),
        ('BACKGROUND',(0,4),(-1,4),colors.HexColor('#e1efe8')),
        ('BOX',(0,0),(-1,-1),0.5,colors.HexColor('#b5c1cc')),
        ('LINEBELOW',(0,1),(-1,3),0.3,colors.HexColor('#d2dce4')),
        ('LEFTPADDING',(0,0),(-1,-1),9), ('RIGHTPADDING',(0,0),(-1,-1),9),
        ('TOPPADDING',(0,0),(-1,-1),5), ('BOTTOMPADDING',(0,0),(-1,-1),5),
        ('VALIGN',(0,0),(-1,-1),'MIDDLE'),
    ]))
    elem.append(KeepTogether([resumo, Spacer(1,0.25*cm)]))

    contas_linhas = [[P('MOVIMENTAÇÃO POR CONTA', cabeca), P('ENTRADAS', cabeca), P('SAÍDAS', cabeca)]]
    for grupo in ('Dinheiro', 'Banco/Pix'):
        vv = dados['contas'].get(grupo, {'entradas':_dinheiro(0),'saidas':_dinheiro(0)})
        contas_linhas.append([P(escape(grupo),normal),P(_real(vv['entradas']),valor), P(_real(vv['saidas']),valor)])
    resumo_contas = Table(contas_linhas, colWidths=[9.0*cm,4.5*cm,4.5*cm], style=TableStyle([
        ('BACKGROUND',(0,0),(-1,0),_NAVY), ('ROWBACKGROUNDS',(0,1),(-1,-1),[colors.white,_BG]),
        ('VALIGN',(0,0),(-1,-1),'MIDDLE'), ('LINEBELOW',(0,0),(-1,-1),0.3,colors.HexColor('#c7cdd5')),
        ('TOPPADDING',(0,0),(-1,-1),5),('BOTTOMPADDING',(0,0),(-1,-1),5),
        ('LEFTPADDING',(0,0),(-1,-1),9),('RIGHTPADDING',(0,0),(-1,-1),9),
    ]))
    elem.append(KeepTogether([resumo_contas, Spacer(1,0.2*cm)]))

    # Detalhamento informativo sem alterar o total econômico do Livro Caixa.
    # Os subgrupos de ofertas são mutuamente exclusivos.
    detalhamento_linhas = [[P('DETALHAMENTO DE ENTRADAS E REPASSES', cabeca), '']]
    for nome in _GRUPOS_ENTRADA:
        detalhamento_linhas.append([
            P(escape(nome), normal),
            P(_real(tot['entradas_por_natureza'][nome]), valor),
        ])
    detalhamento_linhas.extend([
        [P('TOTAL DE ENTRADAS', val_negrito), P(_real(tot['entradas']), val_negrito)],
        [P('Envios à Sede (pagamentos efetivos)', normal), P(_real(tot['enviado_sede']), valor)],
        [P('Demais saídas', normal), P(_real(tot['demais_saidas']), valor)],
        [P('TOTAL DE SAÍDAS', val_negrito), P(_real(tot['saidas']), val_negrito)],
    ])
    detalhamento_tabela = Table(detalhamento_linhas, colWidths=[12*cm, 6*cm], style=TableStyle([
        ('SPAN', (0,0),(-1,0)), ('BACKGROUND',(0,0),(-1,0),_NAVY),
        ('BACKGROUND',(0,6),(-1,6),_BG),
        ('BACKGROUND',(0,len(detalhamento_linhas)-1),(-1,len(detalhamento_linhas)-1),_BG),
        ('LINEBELOW',(0,0),(-1,-1),0.3,colors.HexColor('#c7cdd5')),
        ('TOPPADDING',(0,0),(-1,-1),3), ('BOTTOMPADDING',(0,0),(-1,-1),3),
        ('LEFTPADDING',(0,0),(-1,-1),9), ('RIGHTPADDING',(0,0),(-1,-1),9),
        ('VALIGN',(0,0),(-1,-1),'MIDDLE'),
    ]))
    elem.append(KeepTogether([detalhamento_tabela, Spacer(1,0.12*cm)]))
    elem.append(P('Envios à Sede já integram o total de saídas, sem desconto duplicado. OMN e Outras ofertas são separadas das ofertas de culto.', minusculo))
    elem.append(P(
        f'Conciliação: {dados["evidencias_qtd"]} '
        f'{"evidência bancária" if dados["evidencias_qtd"] == 1 else "evidências bancárias"} '
        f'({_real(dados["evidencias_valor"])}) '
        f'{"preservada" if dados["evidencias_qtd"] == 1 else "preservadas"} no ERP e '
        f'{"excluída" if dados["evidencias_qtd"] == 1 else "excluídas"} da apuração econômica.',
        minusculo,
    ))
    elem.append(P('Documento de controle interno. O saldo é consolidado e não substitui a conferência do caixa físico, dos extratos bancários e dos repasses à Sede.', minusculo))

    def rodape(canvas, pagina_doc):
        canvas.saveState()
        w, _ = A4
        canvas.setStrokeColor(colors.HexColor('#c8d3da'))
        canvas.line(1.45*cm, 0.92*cm, w-1.45*cm, 0.92*cm)
        canvas.setFont('Helvetica', 7)
        canvas.setFillColor(_GRAY)
        canvas.drawString(1.45*cm,0.68*cm,'ERP OBPC  |  Livro Caixa interno  |  Mês civil')
        canvas.drawRightString(w-1.45*cm,0.68*cm,f'Página {pagina_doc.page}')
        canvas.restoreState()
    doc.build(elem, onFirstPage=rodape, onLaterPages=rodape)
    buf.seek(0)
    return buf
