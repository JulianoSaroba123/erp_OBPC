import os
from datetime import datetime
from flask import current_app
from app.configuracoes.configuracoes_model import Configuracao
from reportlab.lib.pagesizes import A4, letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.units import inch, cm, mm
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT, TA_JUSTIFY
from reportlab.platypus.tableofcontents import TableOfContents
from reportlab.platypus.flowables import HRFlowable
from io import BytesIO
import locale

# Configurar locale para formatação brasileira
try:
    locale.setlocale(locale.LC_ALL, 'pt_BR.UTF-8')
except:
    try:
        locale.setlocale(locale.LC_ALL, 'Portuguese_Brazil.1252')
    except:
        pass


class RelatorioFinanceiro:
    """Classe para gerar relatórios financeiros profissionais"""
    
    def __init__(self, configuracao=None):
        self.buffer = BytesIO()
        self.pagesize = A4
        self.width, self.height = self.pagesize
        
        # Carregar configuração se não fornecida
        if configuracao is None:
            self.config = Configuracao.obter_configuracao()
        else:
            self.config = configuracao
            
        self.styles = self._criar_estilos()
        
    def _criar_estilos(self):
        """Cria estilos personalizados para o relatório"""
        styles = getSampleStyleSheet()
        
        # Cores da configuração do sistema
        cor_primaria = colors.HexColor(self.config.cor_principal)
        cor_secundaria = colors.HexColor(self.config.cor_secundaria)
        cor_destaque = colors.HexColor(self.config.cor_destaque)
        
        # Fonte configurável
        fonte_configurada = self.config.fonte_relatorio or 'Helvetica'
        
        custom_styles = {
            'titulo_principal': ParagraphStyle(
                'TituloPrincipal',
                parent=styles['Heading1'],
                fontSize=18,
                textColor=cor_primaria,
                alignment=TA_CENTER,
                spaceAfter=20,
                fontName=f'{fonte_configurada}-Bold',
                spaceBefore=10
            ),
            
            'titulo_igreja': ParagraphStyle(
                'TituloIgreja',
                parent=styles['Normal'],
                fontSize=16,
                textColor=cor_primaria,
                alignment=TA_CENTER,
                fontName=f'{fonte_configurada}-Bold',
                spaceAfter=5
            ),
            
            'subtitulo_igreja': ParagraphStyle(
                'SubtituloIgreja',
                parent=styles['Normal'],
                fontSize=12,
                textColor=cor_secundaria,
                alignment=TA_CENTER,
                fontName=fonte_configurada,
                spaceAfter=3
            ),
            
            'info_periodo': ParagraphStyle(
                'InfoPeriodo',
                parent=styles['Normal'],
                fontSize=14,
                textColor=cor_primaria,
                alignment=TA_CENTER,
                fontName=f'{fonte_configurada}-Bold',
                spaceAfter=20,
                spaceBefore=15
            ),
            
            'cabecalho_secao': ParagraphStyle(
                'CabecalhoSecao',
                parent=styles['Heading2'],
                fontSize=14,
                textColor=cor_primaria,
                alignment=TA_LEFT,
                fontName=f'{fonte_configurada}-Bold',
                spaceAfter=10,
                spaceBefore=20
            ),
            
            'texto_normal': ParagraphStyle(
                'TextoNormal',
                parent=styles['Normal'],
                fontSize=10,
                textColor=colors.black,
                alignment=TA_LEFT,
                fontName=fonte_configurada
            ),
            
            'rodape': ParagraphStyle(
                'Rodape',
                parent=styles['Normal'],
                fontSize=8,
                textColor=colors.grey,
                alignment=TA_CENTER,
                fontName=fonte_configurada
            )
        }
        
        return custom_styles
    
    def _criar_cabecalho(self, titulo_relatorio, periodo=None, dados_igreja=None):
        """Cria cabeçalho profissional do relatório"""
        elementos = []
        
        # Logo da igreja (se configurado para exibir e existir)
        if self.config.exibir_logo_relatorio and self.config.logo:
            try:
                # Determinar caminho da logo
                if self.config.logo.startswith('static/'):
                    logo_path = os.path.join(current_app.root_path, '..', self.config.logo)
                else:
                    logo_path = os.path.join(current_app.static_folder, self.config.logo.replace('static/', ''))
                
                if os.path.exists(logo_path):
                    logo = Image(logo_path, width=60, height=60)
                    logo.hAlign = 'CENTER'
                    elementos.append(logo)
                    elementos.append(Spacer(1, 10))
            except Exception as e:
                # Fallback para logo padrão se configurada
                logo_path = os.path.join(current_app.static_folder, 'logo_obpc_novo.jpg')
                if os.path.exists(logo_path):
                    try:
                        logo = Image(logo_path, width=60, height=60)
                        logo.hAlign = 'CENTER'
                        elementos.append(logo)
                        elementos.append(Spacer(1, 10))
                    except:
                        pass
        
        # Nome da igreja da configuração
        nome_igreja = self.config.nome_igreja or "IGREJA O BRASIL PARA CRISTO"
        elementos.append(Paragraph(nome_igreja.upper(), self.styles['titulo_igreja']))
        
        # Endereço da igreja
        endereco_completo = self.config.endereco_completo()
        if endereco_completo:
            elementos.append(Paragraph(endereco_completo, self.styles['subtitulo_igreja']))
        elif self.config.cidade:
            elementos.append(Paragraph(f"{self.config.cidade}/SP", self.styles['subtitulo_igreja']))
        
        # Linha separadora usando cor principal configurada
        elementos.append(Spacer(1, 15))
        elementos.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor(self.config.cor_principal)))
        elementos.append(Spacer(1, 15))
        
        # Título do relatório
        elementos.append(Paragraph(titulo_relatorio.upper(), self.styles['titulo_principal']))
        
        # Período
        if periodo:
            elementos.append(Paragraph(f"Período: {periodo}", self.styles['info_periodo']))
        
        return elementos
    
    def _criar_tabela_lancamentos(self, lancamentos, mostrar_saldo=True):
        """Cria tabela profissional de lançamentos"""
        if not lancamentos:
            return [Paragraph("Nenhum lançamento encontrado para este período.", self.styles['texto_normal'])]
        
        # Definir colunas
        if mostrar_saldo:
            colunas = ['Data', 'Descrição', 'Categoria', 'Tipo', 'Valor', 'Saldo Acum.']
            larguras = [2*cm, 5*cm, 3*cm, 1.5*cm, 2.5*cm, 2.5*cm]
        else:
            colunas = ['Data', 'Descrição', 'Categoria', 'Tipo', 'Valor']
            larguras = [2*cm, 6*cm, 3.5*cm, 2*cm, 2.5*cm]
        
        # Dados da tabela
        dados = [colunas]
        saldo_acumulado = 0
        
        # Ordenar lançamentos por data
        lancamentos_ordenados = sorted(lancamentos, key=lambda x: x.data)
        
        for lancamento in lancamentos_ordenados:
            # Calcular saldo acumulado
            if lancamento.tipo.lower() == 'entrada':
                saldo_acumulado += lancamento.valor
                valor_formatado = f"+{self._formatar_moeda(lancamento.valor)}"
                cor_valor = colors.green
            else:
                saldo_acumulado -= lancamento.valor
                valor_formatado = f"-{self._formatar_moeda(lancamento.valor)}"
                cor_valor = colors.red
            
            linha = [
                lancamento.data.strftime('%d/%m/%Y'),
                lancamento.descricao or '-',
                lancamento.categoria or '-',
                lancamento.tipo.upper(),
                valor_formatado
            ]
            
            if mostrar_saldo:
                linha.append(self._formatar_moeda(saldo_acumulado))
            
            dados.append(linha)
        
        # Criar tabela
        tabela = Table(dados, colWidths=larguras, repeatRows=1)
        
        # Estilo da tabela
        estilo_tabela = [
            # Cabeçalho
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#001f3f')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            
            # Dados
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
            ('ALIGN', (0, 1), (0, -1), 'CENTER'),  # Data
            ('ALIGN', (1, 1), (1, -1), 'LEFT'),    # Descrição
            ('ALIGN', (2, 1), (2, -1), 'CENTER'),  # Categoria
            ('ALIGN', (3, 1), (3, -1), 'CENTER'),  # Tipo
            ('ALIGN', (4, 1), (-1, -1), 'RIGHT'),  # Valores
            
            # Bordas e cores alternadas
            ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8f9fa')]),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('TOPPADDING', (0, 1), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 1), (-1, -1), 6),
        ]
        
        # Aplicar cores específicas para valores
        for i, lancamento in enumerate(lancamentos_ordenados, 1):
            if lancamento.tipo.lower() == 'entrada':
                estilo_tabela.append(('TEXTCOLOR', (4, i), (4, i), colors.green))
            else:
                estilo_tabela.append(('TEXTCOLOR', (4, i), (4, i), colors.red))
        
        tabela.setStyle(TableStyle(estilo_tabela))
        
        return [tabela]
    
    def _criar_resumo_financeiro(self, entradas_total, saidas_total, saldo_anterior=0, lancamentos=None):
        """Cria seção de resumo financeiro detalhado"""
        elementos = []
        
        elementos.append(Spacer(1, 20))
        elementos.append(Paragraph("RESUMO FINANCEIRO DETALHADO", self.styles['cabecalho_secao']))
        
        if lancamentos:
            # Calcular totais por categoria
            totais_categoria = self._calcular_totais_por_categoria(lancamentos)
            
            # Seção 1: Entradas
            elementos.append(Paragraph("ENTRADAS", self.styles['cabecalho_secao']))
            
            dados_entradas = [
                ['CATEGORIA', 'VALOR', '%']
            ]
            
            total_entradas = sum(totais_categoria['entradas'].values())
            
            for categoria, valor in totais_categoria['entradas'].items():
                percentual = (valor / total_entradas * 100) if total_entradas > 0 else 0
                dados_entradas.append([
                    categoria.title(),
                    f"+{self._formatar_moeda(valor)}",
                    f"{percentual:.1f}%"
                ])
            
            dados_entradas.append([
                'TOTAL ENTRADAS',
                f"+{self._formatar_moeda(total_entradas)}",
                '100.0%'
            ])
            
            tabela_entradas = Table(dados_entradas, colWidths=[6*cm, 3*cm, 2*cm])
            self._aplicar_estilo_tabela_resumo(tabela_entradas, colors.green)
            elementos.append(tabela_entradas)
            elementos.append(Spacer(1, 15))
            
            # Seção 2: Saídas/Despesas
            elementos.append(Paragraph("SAÍDAS E DESPESAS", self.styles['cabecalho_secao']))
            
            dados_saidas = [
                ['CATEGORIA', 'VALOR', '%']
            ]
            
            total_saidas = sum(totais_categoria['saidas'].values())
            
            for categoria, valor in totais_categoria['saidas'].items():
                percentual = (valor / total_saidas * 100) if total_saidas > 0 else 0
                dados_saidas.append([
                    categoria.title(),
                    f"-{self._formatar_moeda(valor)}",
                    f"{percentual:.1f}%"
                ])
            
            dados_saidas.append([
                'TOTAL SAÍDAS',
                f"-{self._formatar_moeda(total_saidas)}",
                '100.0%'
            ])
            
            tabela_saidas = Table(dados_saidas, colWidths=[6*cm, 3*cm, 2*cm])
            self._aplicar_estilo_tabela_resumo(tabela_saidas, colors.red)
            elementos.append(tabela_saidas)
            elementos.append(Spacer(1, 20))
            
            # Seção 3: Resumo por Tipo de Conta
            elementos.append(Paragraph("RESUMO POR CONTA", self.styles['cabecalho_secao']))
            
            totais_conta = self._calcular_totais_por_conta(lancamentos)
            
            dados_conta = [
                ['CONTA', 'ENTRADAS', 'SAÍDAS', 'SALDO']
            ]
            
            for conta in ['Dinheiro', 'Banco', 'PIX']:
                entradas = totais_conta[conta.lower()]['entradas']
                saidas = totais_conta[conta.lower()]['saidas']
                saldo = entradas - saidas
                
                dados_conta.append([
                    conta.upper(),
                    f"+{self._formatar_moeda(entradas)}" if entradas > 0 else "-",
                    f"-{self._formatar_moeda(saidas)}" if saidas > 0 else "-",
                    self._formatar_moeda(saldo)
                ])
            
            tabela_conta = Table(dados_conta, colWidths=[3*cm, 3*cm, 3*cm, 3*cm])
            self._aplicar_estilo_tabela_resumo(tabela_conta, colors.HexColor('#001f3f'))
            elementos.append(tabela_conta)
            elementos.append(Spacer(1, 20))
        
        # Seção 4: Distribuição Visual (Gráfico Textual)
        if lancamentos and (entradas_total > 0 or saidas_total > 0):
            elementos.append(Spacer(1, 20))
            elementos.append(Paragraph("DISTRIBUIÇÃO FINANCEIRA", self.styles['cabecalho_secao']))
            
            # Criar gráfico textual das principais categorias
            principais_entradas = sorted(totais_categoria['entradas'].items(), key=lambda x: x[1], reverse=True)[:5]
            principais_saidas = sorted(totais_categoria['saidas'].items(), key=lambda x: x[1], reverse=True)[:5]
            
            dados_distribuicao = [['PRINCIPAIS ENTRADAS', 'VALOR', 'PRINCIPAIS SAÍDAS', 'VALOR']]
            
            max_linhas = max(len(principais_entradas), len(principais_saidas))
            
            for i in range(max_linhas):
                linha = []
                
                # Entradas
                if i < len(principais_entradas):
                    cat, val = principais_entradas[i]
                    linha.extend([cat.title(), self._formatar_moeda(val)])
                else:
                    linha.extend(['', ''])
                
                # Saídas
                if i < len(principais_saidas):
                    cat, val = principais_saidas[i]
                    linha.extend([cat.title(), self._formatar_moeda(val)])
                else:
                    linha.extend(['', ''])
                
                dados_distribuicao.append(linha)
            
            tabela_distribuicao = Table(dados_distribuicao, colWidths=[4*cm, 2.5*cm, 4*cm, 2.5*cm])
            
            estilo_distribuicao = [
                # Cabeçalho
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#001f3f')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
                
                # Dados
                ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 1), (-1, -1), 9),
                ('ALIGN', (0, 1), (0, -1), 'LEFT'),   # Categorias entradas
                ('ALIGN', (1, 1), (1, -1), 'RIGHT'),  # Valores entradas
                ('ALIGN', (2, 1), (2, -1), 'LEFT'),   # Categorias saídas
                ('ALIGN', (3, 1), (3, -1), 'RIGHT'),  # Valores saídas
                
                # Bordas e cores
                ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('TOPPADDING', (0, 0), (-1, -1), 6),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8f9fa')]),
                
                # Cores das colunas
                ('TEXTCOLOR', (1, 1), (1, -1), colors.green),  # Valores entradas
                ('TEXTCOLOR', (3, 1), (3, -1), colors.red),    # Valores saídas
            ]
            
            tabela_distribuicao.setStyle(TableStyle(estilo_distribuicao))
            elementos.append(tabela_distribuicao)
            elementos.append(Spacer(1, 20))
        
        # Seção 5: Resumo Final
        elementos.append(Paragraph("RESUMO FINAL", self.styles['cabecalho_secao']))
        
        saldo_final = saldo_anterior + entradas_total - saidas_total
        
        dados_resumo = [
            ['DESCRIÇÃO', 'VALOR'],
            ['Saldo Anterior', self._formatar_moeda(saldo_anterior)],
            ['Total de Entradas', f"+{self._formatar_moeda(entradas_total)}"],
            ['Total de Saídas', f"-{self._formatar_moeda(saidas_total)}"],
            ['Movimento do Período', self._formatar_moeda(entradas_total - saidas_total)],
            ['SALDO FINAL', self._formatar_moeda(saldo_final)]
        ]
        
        tabela_resumo = Table(dados_resumo, colWidths=[8*cm, 4*cm])
        
        estilo_resumo = [
            # Cabeçalho
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#001f3f')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            
            # Dados
            ('FONTNAME', (0, 1), (-1, -2), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -2), 11),
            ('ALIGN', (0, 1), (0, -1), 'LEFT'),
            ('ALIGN', (1, 1), (1, -1), 'RIGHT'),
            
            # Linha do saldo final
            ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#f0f8ff')),
            ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, -1), (-1, -1), 14),
            ('TEXTCOLOR', (0, -1), (-1, -1), colors.HexColor('#001f3f')),
            
            # Bordas
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ]
        
        # Cores para entradas e saídas
        estilo_resumo.append(('TEXTCOLOR', (1, 2), (1, 2), colors.green))  # Entradas
        estilo_resumo.append(('TEXTCOLOR', (1, 3), (1, 3), colors.red))    # Saídas
        
        # Cor para movimento do período
        if entradas_total - saidas_total >= 0:
            estilo_resumo.append(('TEXTCOLOR', (1, 4), (1, 4), colors.green))
        else:
            estilo_resumo.append(('TEXTCOLOR', (1, 4), (1, 4), colors.red))
        
        tabela_resumo.setStyle(TableStyle(estilo_resumo))
        elementos.append(tabela_resumo)
        
        return elementos
    
    def _calcular_totais_por_categoria(self, lancamentos):
        """Calcula totais agrupados por categoria"""
        totais = {
            'entradas': {},
            'saidas': {}
        }
        
        for lancamento in lancamentos:
            categoria = lancamento.categoria or 'Outros'
            valor = lancamento.valor or 0
            
            if lancamento.tipo.lower() == 'entrada':
                if categoria not in totais['entradas']:
                    totais['entradas'][categoria] = 0
                totais['entradas'][categoria] += valor
            else:
                if categoria not in totais['saidas']:
                    totais['saidas'][categoria] = 0
                totais['saidas'][categoria] += valor
        
        return totais
    
    def _calcular_totais_por_conta(self, lancamentos):
        """Calcula totais agrupados por conta"""
        totais = {
            'dinheiro': {'entradas': 0, 'saidas': 0},
            'banco': {'entradas': 0, 'saidas': 0},
            'pix': {'entradas': 0, 'saidas': 0}
        }
        
        for lancamento in lancamentos:
            conta = (lancamento.conta or 'dinheiro').lower()
            valor = lancamento.valor or 0
            
            # Determinar a conta
            if 'banco' in conta:
                conta_key = 'banco'
            elif 'pix' in conta:
                conta_key = 'pix'
            else:
                conta_key = 'dinheiro'
            
            if lancamento.tipo.lower() == 'entrada':
                totais[conta_key]['entradas'] += valor
            else:
                totais[conta_key]['saidas'] += valor
        
        return totais
    
    def _aplicar_estilo_tabela_resumo(self, tabela, cor_destaque):
        """Aplica estilo padrão para tabelas de resumo"""
        estilo = [
            # Cabeçalho
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#001f3f')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            
            # Dados
            ('FONTNAME', (0, 1), (-1, -2), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -2), 9),
            ('ALIGN', (0, 1), (0, -1), 'LEFT'),
            ('ALIGN', (1, 1), (-1, -1), 'RIGHT'),
            
            # Linha total
            ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#f0f8ff')),
            ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, -1), (-1, -1), 10),
            ('TEXTCOLOR', (0, -1), (-1, -1), cor_destaque),
            
            # Bordas
            ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('ROWBACKGROUNDS', (0, 1), (-1, -2), [colors.white, colors.HexColor('#f8f9fa')]),
        ]
        
        tabela.setStyle(TableStyle(estilo))
    
    def _criar_rodape(self):
        """Cria rodapé profissional usando configurações"""
        elementos = []
        
        elementos.append(Spacer(1, 30))
        elementos.append(HRFlowable(width="100%", thickness=0.5, color=colors.grey))
        elementos.append(Spacer(1, 10))
        
        data_atual = datetime.now().strftime('%d/%m/%Y às %H:%M')
        elementos.append(Paragraph(f"Relatório gerado em: {data_atual}", self.styles['rodape']))
        
        # Usar rodapé configurado
        if self.config.rodape_relatorio:
            elementos.append(Paragraph(self.config.rodape_relatorio, self.styles['rodape']))
        else:
            elementos.append(Paragraph("Sistema Administrativo OBPC", self.styles['rodape']))
        
        # Endereço da igreja no rodapé
        endereco_rodape = self.config.endereco_completo()
        if endereco_rodape:
            elementos.append(Paragraph(endereco_rodape, self.styles['rodape']))
        
        return elementos
    
    def _criar_campos_assinatura(self):
        """Cria campos de assinatura usando configurações"""
        elementos = []
        
        elementos.append(Spacer(1, 40))
        
        # Criar tabela de assinaturas se configuradas
        if self.config.campo_assinatura_1 or self.config.campo_assinatura_2:
            dados_assinatura = []
            
            # Linha com os campos
            if self.config.campo_assinatura_1 and self.config.campo_assinatura_2:
                dados_assinatura.append([
                    f"______________________________\n{self.config.campo_assinatura_1}",
                    f"______________________________\n{self.config.campo_assinatura_2}"
                ])
            elif self.config.campo_assinatura_1:
                dados_assinatura.append([
                    f"______________________________\n{self.config.campo_assinatura_1}",
                    ""
                ])
            elif self.config.campo_assinatura_2:
                dados_assinatura.append([
                    "",
                    f"______________________________\n{self.config.campo_assinatura_2}"
                ])
            
            if dados_assinatura:
                tabela_assinatura = Table(dados_assinatura, colWidths=[8*cm, 8*cm])
                tabela_assinatura.setStyle(TableStyle([
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                    ('FONTNAME', (0, 0), (-1, -1), self.config.fonte_relatorio or 'Helvetica'),
                    ('FONTSIZE', (0, 0), (-1, -1), 10),
                    ('TOPPADDING', (0, 0), (-1, -1), 20),
                ]))
                elementos.append(tabela_assinatura)
        
        return elementos
    
    def _formatar_moeda(self, valor):
        """Formata valor como moeda brasileira"""
        try:
            return f"R$ {valor:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
        except:
            return f"R$ 0,00"
    
    def gerar_relatorio_caixa(self, lancamentos, mes, ano, saldo_anterior=0):
        """Gera relatório de caixa profissional"""
        doc = SimpleDocTemplate(
            self.buffer, 
            pagesize=self.pagesize,
            rightMargin=2*cm, 
            leftMargin=2*cm,
            topMargin=2*cm, 
            bottomMargin=2*cm,
            title=f"Relatório de Caixa {mes:02d}/{ano}"
        )
        
        elementos = []
        
        # Cabeçalho
        periodo = f"{mes:02d}/{ano}"
        elementos.extend(self._criar_cabecalho("RELATÓRIO DE CAIXA (INTERNO)", periodo))
        
        if lancamentos:
            # Tabela de lançamentos
            elementos.extend(self._criar_tabela_lancamentos(lancamentos, mostrar_saldo=True))
            
            # Calcular totais
            entradas_total = sum(l.valor for l in lancamentos if l.tipo.lower() == 'entrada')
            saidas_total = sum(l.valor for l in lancamentos if l.tipo.lower() == 'saida')
            
            # Resumo financeiro
            elementos.extend(self._criar_resumo_financeiro(entradas_total, saidas_total, saldo_anterior, lancamentos))
        else:
            elementos.append(Paragraph("Nenhum lançamento encontrado para este período.", 
                                     self.styles['texto_normal']))
        
        # Campos de assinatura
        elementos.extend(self._criar_campos_assinatura())
        
        # Rodapé
        elementos.extend(self._criar_rodape())
        
        # Gerar PDF
        doc.build(elementos)
        self.buffer.seek(0)
        return self.buffer
    
    def gerar_relatorio_sede(self, lancamentos, mes, ano, saldo_anterior=0):
        """Gera relatório para sede profissional"""
        doc = SimpleDocTemplate(
            self.buffer, 
            pagesize=self.pagesize,
            rightMargin=2*cm, 
            leftMargin=2*cm,
            topMargin=2*cm, 
            bottomMargin=2*cm,
            title=f"Relatório Sede {mes:02d}/{ano}"
        )
        
        elementos = []
        
        # Cabeçalho
        periodo = f"{mes:02d}/{ano}"
        elementos.extend(self._criar_cabecalho("RELATÓRIO PARA IGREJA SEDE", periodo))
        
        if lancamentos:
            # Filtrar apenas entradas
            entradas = [l for l in lancamentos if l.tipo.lower() == 'entrada']
            
            if entradas:
                elementos.extend(self._criar_tabela_lancamentos(entradas, mostrar_saldo=False))
                
                # Resumo simplificado
                entradas_total = sum(l.valor for l in entradas)
                
                elementos.append(Spacer(1, 20))
                elementos.append(Paragraph("RESUMO DE ENTRADAS", self.styles['cabecalho_secao']))
                
                dados_resumo = [
                    ['DESCRIÇÃO', 'VALOR'],
                    ['Total de Entradas', self._formatar_moeda(entradas_total)]
                ]
                
                tabela_resumo = Table(dados_resumo, colWidths=[8*cm, 4*cm])
                tabela_resumo.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#001f3f')),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 12),
                    ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
                    ('FONTNAME', (0, 1), (-1, 1), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 1), (-1, 1), 11),
                    ('ALIGN', (0, 1), (0, 1), 'LEFT'),
                    ('ALIGN', (1, 1), (1, 1), 'RIGHT'),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black),
                    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                    ('TOPPADDING', (0, 0), (-1, -1), 8),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
                ]))
                elementos.append(tabela_resumo)
            else:
                elementos.append(Paragraph("Nenhuma entrada encontrada para este período.", 
                                         self.styles['texto_normal']))
        else:
            elementos.append(Paragraph("Nenhum lançamento encontrado para este período.", 
                                     self.styles['texto_normal']))
        
        # Campos de assinatura
        elementos.extend(self._criar_campos_assinatura())
        
        # Rodapé
        elementos.extend(self._criar_rodape())
        
        # Gerar PDF
        doc.build(elementos)
        self.buffer.seek(0)
        return self.buffer


def gerar_pdf_relatorio_caixa(lancamentos, mes, ano, saldo_anterior=0):
    """Função wrapper para compatibilidade"""
    config = Configuracao.obter_configuracao()
    relatorio = RelatorioFinanceiro(config)
    return relatorio.gerar_relatorio_caixa(lancamentos, mes, ano, saldo_anterior)


def gerar_pdf_relatorio_sede(lancamentos, mes, ano, saldo_anterior=0):
    """Função wrapper para compatibilidade"""
    config = Configuracao.obter_configuracao()
    relatorio = RelatorioFinanceiro(config)
    return relatorio.gerar_relatorio_sede(lancamentos, mes, ano, saldo_anterior)


def gerar_nome_arquivo_relatorio(tipo_relatorio, mes, ano):
    """Gera nome padronizado para os arquivos de relatório"""
    nomes = {
        'caixa': f'relatorio_caixa_{mes:02d}_{ano}.pdf',
        'sede': f'relatorio_sede_{mes:02d}_{ano}.pdf'
    }
    return nomes.get(tipo_relatorio, f'relatorio_{mes:02d}_{ano}.pdf')