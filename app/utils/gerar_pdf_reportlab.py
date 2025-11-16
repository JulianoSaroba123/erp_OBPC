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
        """Cria cabeçalho profissional do relatório com logo OBPC"""
        elementos = []
        
        # Logo OBPC sempre presente
        try:
            logo_path = os.path.join(current_app.static_folder, 'Logo_OBPC.jpg')
            if os.path.exists(logo_path):
                logo = Image(logo_path, width=120, height=120)
                logo.hAlign = 'CENTER'
                elementos.append(logo)
                elementos.append(Spacer(1, 15))
        except Exception as e:
            # Fallback para outros logos se OBPC não existir
            fallback_logos = ['logo_obpc_novo.jpg', 'logo_obpc.ico']
            for fallback_logo in fallback_logos:
                try:
                    logo_path = os.path.join(current_app.static_folder, fallback_logo)
                    if os.path.exists(logo_path):
                        logo = Image(logo_path, width=110, height=110)
                        logo.hAlign = 'CENTER'
                        elementos.append(logo)
                        elementos.append(Spacer(1, 15))
                        break
                except:
                    continue
        
        # Apenas cidade abaixo do logo (mais limpo)
        elementos.append(Paragraph("TIETÊ - SP", self.styles['subtitulo_igreja']))
        
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
        
        # Definir colunas e larguras ajustadas para A4 (21cm)
        # Total disponível: ~17cm (21cm - 2cm margem esquerda - 2cm margem direita)
        if mostrar_saldo:
            colunas = ['Data', 'Descrição', 'Categoria', 'Tipo', 'Valor', 'Comprovante', 'Saldo Acum.']
            larguras = [2.2*cm, 5.5*cm, 2.8*cm, 1.8*cm, 2.5*cm, 1.7*cm, 2.5*cm]  # Total: 17cm
        else:
            colunas = ['Data', 'Descrição', 'Categoria', 'Tipo', 'Valor', 'Comprovante']
            larguras = [2.2*cm, 6.5*cm, 3.0*cm, 2.0*cm, 2.5*cm, 1.8*cm]  # Total: 18cm
        
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
            
            # Gerar informação do comprovante
            comprovante_info = self._gerar_info_comprovante(lancamento)
            
            # Truncar descrição se muito longa para evitar sobreposição
            descricao = self._truncar_texto(lancamento.descricao or '-', 35)
            categoria = self._truncar_texto(lancamento.categoria or '-', 15)
            
            linha = [
                lancamento.data.strftime('%d/%m/%Y'),
                descricao,
                categoria,
                lancamento.tipo.upper(),
                valor_formatado,
                comprovante_info
            ]
            
            if mostrar_saldo:
                linha.append(self._formatar_moeda(saldo_acumulado))
            
            dados.append(linha)
        
        # Criar tabela com altura adequada para evitar sobreposição
        tabela = Table(dados, colWidths=larguras, repeatRows=1, rowHeights=None)
        
        # Configurar altura mínima das linhas para evitar sobreposição
        if len(dados) > 1:  # Se há dados além do cabeçalho
            altura_minima = [22]  # Cabeçalho maior
            for _ in range(len(dados) - 1):  # Dados
                altura_minima.append(25)  # Altura maior para cada linha de dados
            tabela = Table(dados, colWidths=larguras, repeatRows=1, rowHeights=altura_minima)
        
        # Estilo da tabela com espaçamento adequado
        estilo_tabela = [
            # Cabeçalho
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#001f3f')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 9),  # Fonte menor para evitar sobreposição
            ('BOTTOMPADDING', (0, 0), (-1, 0), 14),
            ('TOPPADDING', (0, 0), (-1, 0), 8),
            
            # Dados
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 8),  # Fonte menor para evitar sobreposição
            ('ALIGN', (0, 1), (0, -1), 'CENTER'),  # Data
            ('ALIGN', (1, 1), (1, -1), 'LEFT'),    # Descrição
            ('ALIGN', (2, 1), (2, -1), 'CENTER'),  # Categoria
            ('ALIGN', (3, 1), (3, -1), 'CENTER'),  # Tipo
            ('ALIGN', (4, 1), (4, -1), 'RIGHT'),   # Valor
            ('ALIGN', (5, 1), (5, -1), 'CENTER'),  # Comprovante
            ('ALIGN', (6, 1), (-1, -1), 'RIGHT'),  # Saldo (se mostrar_saldo=True)
            
            # Bordas e cores alternadas
            ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8f9fa')]),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('TOPPADDING', (0, 1), (-1, -1), 10),    # Mais espaçamento
            ('BOTTOMPADDING', (0, 1), (-1, -1), 10), # Mais espaçamento
            ('LEFTPADDING', (0, 0), (-1, -1), 6),    # Espaçamento lateral
            ('RIGHTPADDING', (0, 0), (-1, -1), 6),   # Espaçamento lateral
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
        """Cria seção de resumo financeiro detalhado com despesas fixas e conselho"""
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
            
            tabela_entradas = Table(dados_entradas, colWidths=[8*cm, 5*cm, 3*cm])  # Larguras ainda mais amplas
            self._aplicar_estilo_tabela_resumo(tabela_entradas, colors.green)
            elementos.append(tabela_entradas)
            elementos.append(Spacer(1, 15))
            
            # Seção 2: Saídas/Despesas (incluindo fixas)
            elementos.append(Paragraph("SAÍDAS E DESPESAS", self.styles['cabecalho_secao']))
            
            dados_saidas = [
                ['CATEGORIA', 'VALOR', '%']
            ]
            
            # Calcular total de saídas dos lançamentos + despesas fixas
            total_saidas_lancamentos = sum(totais_categoria['saidas'].values())
            
            # Obter despesas fixas
            try:
                from app.financeiro.despesas_fixas_model import DespesaFixaConselho
                despesas_fixas = DespesaFixaConselho.obter_despesas_para_relatorio()
                total_despesas_fixas = sum(despesas_fixas.values())
            except:
                despesas_fixas = {
                    'contador_sede': 100.00,
                    'forca_para_viver': 50.00,
                    'oferta_voluntaria_conchas': 100.00,
                    'projeto_filipe': 10.00,
                    'site': 20.00
                }
                total_despesas_fixas = sum(despesas_fixas.values())
            
            # Calcular valor do conselho administrativo
            percentual_conselho = self.config.percentual_conselho / 100 if self.config else 0.30
            valor_conselho = total_entradas * percentual_conselho
            
            # Total geral de saídas (lançamentos + despesas fixas + conselho)
            total_saidas_geral = total_saidas_lancamentos + total_despesas_fixas + valor_conselho
            
            # Adicionar categorias de lançamentos
            for categoria, valor in totais_categoria['saidas'].items():
                percentual = (valor / total_saidas_geral * 100) if total_saidas_geral > 0 else 0
                dados_saidas.append([
                    categoria.title(),
                    f"-{self._formatar_moeda(valor)}",
                    f"{percentual:.1f}%"
                ])
            
            # Adicionar despesas fixas
            if total_despesas_fixas > 0:
                percentual_fixas = (total_despesas_fixas / total_saidas_geral * 100) if total_saidas_geral > 0 else 0
                dados_saidas.append([
                    'Despesas Fixas Sede',
                    f"-{self._formatar_moeda(total_despesas_fixas)}",
                    f"{percentual_fixas:.1f}%"
                ])
            
            # Adicionar conselho administrativo
            if valor_conselho > 0:
                percentual_conselho_calc = (valor_conselho / total_saidas_geral * 100) if total_saidas_geral > 0 else 0
                dados_saidas.append([
                    'Total Enviado ao Conselho Administrativo',
                    f"-{self._formatar_moeda(valor_conselho)}",
                    f"{percentual_conselho_calc:.1f}%"
                ])
            
            dados_saidas.append([
                'TOTAL SAÍDAS',
                f"-{self._formatar_moeda(total_saidas_geral)}",
                '100.0%'
            ])
            
            tabela_saidas = Table(dados_saidas, colWidths=[8*cm, 5*cm, 3*cm])  # Larguras ainda mais amplas
            self._aplicar_estilo_tabela_resumo(tabela_saidas, colors.red)
            elementos.append(tabela_saidas)
            elementos.append(Spacer(1, 20))
            
            # Seção 3: Resumo por Tipo de Conta
            elementos.append(Paragraph("RESUMO POR CONTA", self.styles['cabecalho_secao']))
            
            totais_conta = self._calcular_totais_por_conta(lancamentos)
            
            dados_conta = [
                ['CONTA', 'ENTRADAS', 'SAÍDAS', 'SALDO']
            ]
            
            for conta in ['Dinheiro', 'Banco']:  # Removido PIX
                entradas = totais_conta[conta.lower()]['entradas']
                saidas = totais_conta[conta.lower()]['saidas']
                saldo = entradas - saidas
                
                dados_conta.append([
                    conta.upper(),
                    f"+{self._formatar_moeda(entradas)}" if entradas > 0 else "-",
                    f"-{self._formatar_moeda(saidas)}" if saidas > 0 else "-",
                    self._formatar_moeda(saldo)
                ])
            
            tabela_conta = Table(dados_conta, colWidths=[4*cm, 4*cm, 4*cm, 4*cm])  # Larguras ajustadas
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
                ('TOPPADDING', (0, 0), (-1, -1), 8),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8f9fa')]),
                
                # Cores das colunas
                ('TEXTCOLOR', (1, 1), (1, -1), colors.green),  # Valores entradas
                ('TEXTCOLOR', (3, 1), (3, -1), colors.red),    # Valores saídas
            ]
            
            tabela_distribuicao.setStyle(TableStyle(estilo_distribuicao))
            elementos.append(tabela_distribuicao)
            elementos.append(Spacer(1, 20))
        
        # Seção Final: Resumo Final (com totais corretos)
        elementos.append(Paragraph("RESUMO FINAL", self.styles['cabecalho_secao']))
        
        # Recalcular totais incluindo despesas fixas e conselho
        if lancamentos:
            total_entradas_final = sum(totais_categoria['entradas'].values())
            total_saidas_lancamentos_final = sum(totais_categoria['saidas'].values())
            
            # Adicionar despesas fixas e conselho ao total de saídas
            try:
                from app.financeiro.despesas_fixas_model import DespesaFixaConselho
                despesas_fixas_final = DespesaFixaConselho.obter_despesas_para_relatorio()
                total_despesas_fixas_final = sum(despesas_fixas_final.values())
            except:
                total_despesas_fixas_final = 280.00  # Valor padrão
            
            percentual_conselho_final = self.config.percentual_conselho / 100 if self.config else 0.30
            valor_conselho_final = total_entradas_final * percentual_conselho_final
            
            total_saidas_final = total_saidas_lancamentos_final + total_despesas_fixas_final + valor_conselho_final
        else:
            total_entradas_final = entradas_total
            total_saidas_final = saidas_total
        
        saldo_final = saldo_anterior + total_entradas_final - total_saidas_final
        
        dados_resumo = [
            ['DESCRIÇÃO', 'VALOR'],
            ['Saldo Anterior', self._formatar_moeda(saldo_anterior)],
            ['Total de Entradas', f"+{self._formatar_moeda(total_entradas_final)}"],
            ['Total de Saídas', f"-{self._formatar_moeda(total_saidas_final)}"],
            ['Movimento do Período', self._formatar_moeda(total_entradas_final - total_saidas_final)],
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
            'banco': {'entradas': 0, 'saidas': 0}
        }
        
        for lancamento in lancamentos:
            conta = (lancamento.conta or 'dinheiro').lower()
            valor = float(lancamento.valor) if lancamento.valor else 0
            
            # Determinar a conta - mapeamento melhorado
            if 'banco' in conta or 'conta' in conta:
                conta_key = 'banco'
            else:
                conta_key = 'dinheiro'
            
            # Garantir que a conta existe no dicionário
            if conta_key not in totais:
                totais[conta_key] = {'entradas': 0, 'saidas': 0}
            
            if lancamento.tipo.lower() == 'entrada':
                totais[conta_key]['entradas'] += valor
            elif lancamento.tipo.lower() == 'saída' or lancamento.tipo.lower() == 'saida':
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
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
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
    
    def _gerar_info_comprovante(self, lancamento):
        """Gera informação do comprovante para o PDF"""
        if hasattr(lancamento, 'comprovante') and lancamento.comprovante:
            # Extrair nome do arquivo do caminho
            nome_arquivo = lancamento.comprovante.split('/')[-1] if '/' in lancamento.comprovante else lancamento.comprovante
            
            # Gerar URL completa do comprovante
            url_comprovante = f"http://127.0.0.1:5000/static/uploads/comprovantes/{nome_arquivo}"
            
            # Criar link clicável usando HTML
            from reportlab.platypus import Paragraph
            link_html = f'<link href="{url_comprovante}">📎 {nome_arquivo[:15]}...</link>'
            return Paragraph(link_html, self.styles['texto_normal'])
        else:
            return "-"
    
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
            
            # Calcular totais corrigindo o problema das saídas
            entradas_total = sum(float(l.valor) for l in lancamentos if l.tipo.lower() == 'entrada')
            saidas_total = sum(float(l.valor) for l in lancamentos if l.tipo.lower() in ['saída', 'saida'])
            
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
        """Gera relatório para sede seguindo o padrão oficial da igreja"""
        doc = SimpleDocTemplate(
            self.buffer, 
            pagesize=self.pagesize,
            rightMargin=2*cm, 
            leftMargin=2*cm,
            topMargin=1.5*cm, 
            bottomMargin=2*cm,
            title=f"Relatório Sede {mes:02d}/{ano}"
        )
        
        elementos = []
        
        # CABEÇALHO OFICIAL DA IGREJA
        elementos.extend(self._criar_cabecalho_sede_oficial())
        
        # INFORMAÇÕES DO PERÍODO E IGREJA
        elementos.extend(self._criar_info_periodo_sede(mes, ano))
        
        if lancamentos:
            # Calcular totais seguindo a mesma lógica do template
            totais = self._calcular_totais_sede(lancamentos)
            
            # Obter despesas fixas dinamicamente
            envios = self._obter_despesas_fixas_sede()
            
            # SEÇÃO 1: ARRECADAÇÃO DO MÊS
            elementos.extend(self._criar_secao_arrecadacao_sede(totais))
            
            # SEÇÃO 2: DESPESAS FINANCEIRAS
            elementos.extend(self._criar_secao_despesas_sede(totais))
            
            # SEÇÃO 3: SALDO DO MÊS
            elementos.extend(self._criar_secao_saldo_sede(totais))
            
            # SEÇÃO 4: VALOR DO CONSELHO ADMINISTRATIVO
            elementos.extend(self._criar_secao_conselho_sede(totais))
            
            # SEÇÃO 5: LISTA DE ENVIOS À SEDE
            elementos.extend(self._criar_secao_envios_sede(envios))
            
            # SEÇÃO 6: TOTAL DE ENVIO PARA SEDE (CONSELHO + PROJETOS)
            elementos.extend(self._criar_secao_total_envio_sede(totais, envios))
            
        else:
            elementos.append(Spacer(1, 20))
            elementos.append(Paragraph("Nenhum lançamento encontrado para este período.", 
                                     self.styles['texto_normal']))
        
        # ASSINATURAS OFICIAIS
        elementos.extend(self._criar_assinaturas_sede())
        
        # RODAPÉ COM DATA E LOCAL
        elementos.extend(self._criar_rodape_sede())
        
        # Gerar PDF
        doc.build(elementos)
        self.buffer.seek(0)
        return self.buffer
    
    def _criar_cabecalho_sede_oficial(self):
        """Cria cabeçalho oficial da igreja para relatório da sede com logo OBPC"""
        elementos = []
        
        # Logo OBPC no cabeçalho da sede
        try:
            logo_path = os.path.join(current_app.static_folder, 'Logo_OBPC.jpg')
            if os.path.exists(logo_path):
                logo = Image(logo_path, width=130, height=130)
                logo.hAlign = 'CENTER'
                elementos.append(logo)
                elementos.append(Spacer(1, 20))
        except Exception as e:
            pass
        
        # Título principal centralizado
        titulo_style = ParagraphStyle(
            'TituloSede',
            parent=self.styles['titulo_principal'],
            fontSize=18,
            textColor=colors.HexColor('#4A7C59'),  # Verde do logo OBPC
            alignment=TA_CENTER,
            spaceAfter=5,
            fontName='Helvetica-Bold'
        )
        
        subtitulo_style = ParagraphStyle(
            'SubtituloSede',
            parent=self.styles['titulo_principal'],
            fontSize=14,
            textColor=colors.black,
            alignment=TA_CENTER,
            spaceAfter=15,
            fontName='Helvetica-Bold'
        )
        
        periodo_style = ParagraphStyle(
            'PeriodoSede',
            parent=self.styles['titulo_principal'],
            fontSize=12,
            textColor=colors.black,
            alignment=TA_CENTER,
            spaceAfter=20,
            fontName='Helvetica-Bold'
        )
        
        # Apenas cidade (mais limpo e profissional)
        elementos.append(Paragraph("TIETÊ - SP", subtitulo_style))
        
        # Título do relatório
        elementos.append(Paragraph("RELATÓRIO MENSAL OFICIAL", subtitulo_style))
        
        # Linha horizontal decorativa
        elementos.append(HRFlowable(width="60%", thickness=2, color=colors.HexColor('#2E86AB')))  # Azul do logo
        elementos.append(Spacer(1, 15))
        
        return elementos
    
    def _criar_info_periodo_sede(self, mes, ano):
        """Cria seção com informações do período e dados da igreja"""
        elementos = []
        
        # Dados da igreja em tabela
        dados_igreja = [
            ['Cidade:', 'Tietê', 'Dirigente:', 'Pastor João Silva'],
            ['Bairro:', 'Centro', 'Tesoureiro:', 'Maria Santos'],
            ['Mês/Ano:', f'{mes:02d}/{ano}', 'Data Relatório:', datetime.now().strftime('%d/%m/%Y')],
        ]
        
        tabela_info = Table(dados_igreja, colWidths=[3*cm, 4*cm, 3*cm, 4*cm])
        tabela_info.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),  # Labels primeira coluna
            ('FONTNAME', (2, 0), (2, -1), 'Helvetica-Bold'),  # Labels terceira coluna
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('LEFTPADDING', (0, 0), (-1, -1), 0),
            ('RIGHTPADDING', (1, 0), (1, -1), 20),  # Espaço entre colunas
        ]))
        
        elementos.append(tabela_info)
        elementos.append(Spacer(1, 20))
        elementos.append(HRFlowable(width="100%", thickness=1, color=colors.grey))
        elementos.append(Spacer(1, 20))
        
        return elementos
    
    def _calcular_totais_sede(self, lancamentos):
        """Calcula totais específicos para o relatório da sede"""
        totais = {
            'dizimos': 0,
            'ofertas_alcadas': 0,
            'outras_ofertas': 0,
            'total_geral': 0,
            'despesas_financeiras': 0,
            'saldo_mes': 0,
            'valor_conselho': 0
        }
        
        for lancamento in lancamentos:
            valor = float(lancamento.valor) if lancamento.valor else 0
            
            if lancamento.tipo == 'Entrada':
                categoria_lower = (lancamento.categoria or '').lower()
                
                if 'dízimo' in categoria_lower or 'dizimo' in categoria_lower:
                    totais['dizimos'] += valor
                elif 'oferta' in categoria_lower:
                    # Lógica padronizada das ofertas:
                    if 'omn' in categoria_lower:
                        # OFERTA OMN - direcionada à convenção
                        totais['ofertas_alcadas'] += valor
                    elif categoria_lower == 'oferta':
                        # OFERTA regular - verificar descrição
                        descricao = (lancamento.descricao or '').lower()
                        if 'oferta' in descricao and 'outras' not in descricao:
                            # Ofertas do ofertório durante cultos
                            totais['ofertas_alcadas'] += valor
                        else:
                            # Ofertas externas, doações, projetos
                            totais['outras_ofertas'] += valor
                    else:
                        # Outras categorias de oferta
                        totais['outras_ofertas'] += valor
                else:
                    totais['outras_ofertas'] += valor
                
                totais['total_geral'] += valor
            
            elif lancamento.tipo == 'Saída':
                totais['despesas_financeiras'] += valor
        
        # Calcular valores finais
        totais['saldo_mes'] = totais['total_geral'] - totais['despesas_financeiras']
        
        # Buscar percentual do conselho das configurações
        percentual = self.config.percentual_conselho / 100
        totais['valor_conselho'] = totais['total_geral'] * percentual
        
        return totais
    
    def _obter_despesas_fixas_sede(self):
        """Obtém despesas fixas da base de dados ou valores padrão"""
        try:
            from app.financeiro.despesas_fixas_model import DespesaFixaConselho
            envios = DespesaFixaConselho.obter_despesas_para_relatorio()
        except ImportError:
            # Fallback para valores fixos
            envios = {
                'oferta_voluntaria_conchas': 50.00,
                'site': 25.00,
                'projeto_filipe': 100.00,
                'forca_para_viver': 30.00,
                'contador_sede': 150.00
            }
        return envios
    
    def _criar_secao_arrecadacao_sede(self, totais):
        """Cria seção de arrecadação seguindo padrão da igreja"""
        elementos = []
        
        # Título da seção com ícone
        secao_style = ParagraphStyle(
            'SecaoSede',
            parent=self.styles['cabecalho_secao'],
            fontSize=14,
            textColor=colors.HexColor('#4A7C59'),  # Verde do logo OBPC
            alignment=TA_LEFT,
            spaceAfter=10,
            fontName='Helvetica-Bold'
        )
        
        elementos.append(Paragraph("🤲 ARRECADAÇÃO DO MÊS", secao_style))
        
        # Adicionar explicação das categorias
        explicacao_style = ParagraphStyle(
            'ExplicacaoSede',
            fontSize=9,
            textColor=colors.HexColor('#666666'),
            alignment=TA_LEFT,
            spaceAfter=15,
            fontName='Helvetica'
        )
        
        texto_explicacao = """
        <b>Ofertas Alçadas:</b> Ofertas do ofertório durante cultos + Ofertas OMN para convenção<br/>
        <b>Outras Ofertas:</b> Ofertas externas, doações, projetos e investimentos no templo
        """
        
        elementos.append(Paragraph(texto_explicacao, explicacao_style))
        
        # Tabela de arrecadação com headers
        dados_arrecadacao = [
            ['CATEGORIA', 'VALOR ARRECADADO'],
            ['Dízimos', self._formatar_moeda(totais['dizimos'])],
            ['Ofertas Alçadas', self._formatar_moeda(totais['ofertas_alcadas'])],
            ['Outras Ofertas', self._formatar_moeda(totais['outras_ofertas'])],
        ]
        
        tabela_arrecadacao = Table(dados_arrecadacao, colWidths=[12*cm, 4*cm])
        tabela_arrecadacao.setStyle(TableStyle([
            # Header (primeira linha)
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#4A7C59')),  # Verde escuro
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('ALIGN', (0, 0), (0, 0), 'LEFT'),
            ('ALIGN', (1, 0), (1, 0), 'CENTER'),
            
            # Dados (demais linhas)
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 1), (-1, -1), 11),
            ('ALIGN', (0, 1), (0, -1), 'LEFT'),
            ('ALIGN', (1, 1), (1, -1), 'RIGHT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('LEFTPADDING', (0, 0), (-1, -1), 12),
            ('RIGHTPADDING', (0, 0), (-1, -1), 12),
            
            # Cores alternadas para as linhas de dados
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.HexColor('#F0F8F0'), colors.HexColor('#E8F5E8')]),
            ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#CCCCCC')),
            ('TEXTCOLOR', (1, 1), (1, -1), colors.HexColor('#4A7C59')),  # Verde para valores
            
            # Bordas mais elegantes
            ('LINEBELOW', (0, 0), (-1, 0), 2, colors.HexColor('#4A7C59')),  # Linha abaixo do header
        ]))
        
        elementos.append(tabela_arrecadacao)
        
        # Seção informativa sobre percentuais
        elementos.append(Spacer(1, 15))
        
        info_style = ParagraphStyle(
            'InfoCalculos',
            fontSize=10,
            textColor=colors.HexColor('#4A7C59'),
            alignment=TA_LEFT,
            spaceAfter=12,
            fontName='Helvetica',
            leftIndent=20,
            rightIndent=20,
            backColor=colors.HexColor('#F8FFF8'),
            borderColor=colors.HexColor('#7FB069'),
            borderWidth=1,
            borderPadding=10
        )
        
        percentual_conselho = self.config.percentual_conselho if hasattr(self.config, 'percentual_conselho') else 30
        valor_conselho = totais['total_geral'] * (percentual_conselho / 100)
        
        texto_info = f"""
        <b>📊 INFORMAÇÕES IMPORTANTES:</b><br/>
        • Do total arrecadado, {percentual_conselho}% vai para o Conselho da sede: <b>{self._formatar_moeda(valor_conselho)}</b><br/>
        • As Ofertas OMN são direcionadas diretamente à convenção (não passam pelo caixa local)<br/>
        • Este relatório serve para comunicação oficial com a igreja sede
        """
        
        elementos.append(Paragraph(texto_info, info_style))
        
        # Espaçamento antes do total
        elementos.append(Spacer(1, 10))
        
        # Total geral destacado
        total_dados = [['💰 TOTAL GERAL ARRECADADO', self._formatar_moeda(totais['total_geral'])]]
        tabela_total = Table(total_dados, colWidths=[12*cm, 4*cm])
        tabela_total.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#4A7C59')),  # Verde escuro
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 14),
            ('ALIGN', (0, 0), (0, -1), 'LEFT'),
            ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('TOPPADDING', (0, 0), (-1, -1), 12),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
            ('LEFTPADDING', (0, 0), (-1, -1), 12),
            ('RIGHTPADDING', (0, 0), (-1, -1), 12),
            ('GRID', (0, 0), (-1, -1), 2, colors.HexColor('#2D4A35')),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.white),
            # Sombra sutil
            ('LINEBEFORE', (0, 0), (-1, -1), 3, colors.HexColor('#7FB069')),
        ]))
        
        elementos.append(tabela_total)
        elementos.append(Spacer(1, 20))
        
        return elementos
    
    def _criar_secao_despesas_sede(self, totais):
        """Cria seção de despesas financeiras"""
        elementos = []
        
        secao_style = ParagraphStyle(
            'SecaoSede',
            parent=self.styles['cabecalho_secao'],
            fontSize=14,
            textColor=colors.HexColor('#DC143C'),
            alignment=TA_LEFT,
            spaceAfter=10,
            fontName='Helvetica-Bold'
        )
        
        elementos.append(Paragraph("💳 DESPESAS FINANCEIRAS DO MÊS", secao_style))
        
        dados_despesas = [['Despesas Financeiras no Mês', self._formatar_moeda(totais['despesas_financeiras'])]]
        
        tabela_despesas = Table(dados_despesas, colWidths=[12*cm, 4*cm])
        tabela_despesas.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#FFE4E1')),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 11),
            ('ALIGN', (0, 0), (0, -1), 'LEFT'),
            ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('TEXTCOLOR', (1, 0), (1, -1), colors.HexColor('#DC143C')),
        ]))
        
        elementos.append(tabela_despesas)
        elementos.append(Spacer(1, 20))
        
        return elementos
    
    def _criar_secao_saldo_sede(self, totais):
        """Cria seção de saldo do mês"""
        elementos = []
        
        secao_style = ParagraphStyle(
            'SecaoSede',
            parent=self.styles['cabecalho_secao'],
            fontSize=14,
            textColor=colors.HexColor('#2E86AB'),  # Azul do logo OBPC
            alignment=TA_LEFT,
            spaceAfter=10,
            fontName='Helvetica-Bold'
        )
        
        elementos.append(Paragraph("⚖️ SALDO DO MÊS", secao_style))
        
        # Cor de fundo baseada no saldo
        cor_fundo = colors.HexColor('#E8F5E8') if totais['saldo_mes'] >= 0 else colors.HexColor('#FFE6E6')  # Verde claro do logo
        cor_texto = colors.HexColor('#4A7C59') if totais['saldo_mes'] >= 0 else colors.HexColor('#DC143C')  # Verde do logo
        
        dados_saldo = [['Saldo do Mês', self._formatar_moeda(totais['saldo_mes'])]]
        
        tabela_saldo = Table(dados_saldo, colWidths=[12*cm, 4*cm])
        tabela_saldo.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), cor_fundo),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 12),
            ('ALIGN', (0, 0), (0, -1), 'LEFT'),
            ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('TOPPADDING', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('TEXTCOLOR', (1, 0), (1, -1), cor_texto),
        ]))
        
        elementos.append(tabela_saldo)
        elementos.append(Spacer(1, 20))
        
        return elementos
    
    def _criar_secao_conselho_sede(self, totais):
        """Cria seção do valor do conselho administrativo"""
        elementos = []
        
        secao_style = ParagraphStyle(
            'SecaoSede',
            parent=self.styles['cabecalho_secao'],
            fontSize=14,
            textColor=colors.HexColor('#2E86AB'),  # Azul do logo OBPC
            alignment=TA_LEFT,
            spaceAfter=10,
            fontName='Helvetica-Bold'
        )
        
        elementos.append(Paragraph("👥 VALOR DO CONSELHO ADMINISTRATIVO", secao_style))
        
        # Usar percentual configurado
        percentual = int(self.config.percentual_conselho)
        descricao = f'Valor a ser entregue à sede ({percentual}% do total arrecadado)'
        
        dados_conselho = [[descricao, self._formatar_moeda(totais['valor_conselho'])]]
        
        tabela_conselho = Table(dados_conselho, colWidths=[12*cm, 4*cm])
        tabela_conselho.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#E8F5E8')),  # Verde claro do logo
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 11),
            ('ALIGN', (0, 0), (0, -1), 'LEFT'),
            ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('TEXTCOLOR', (1, 0), (1, -1), colors.HexColor('#2E86AB')),  # Azul do logo
        ]))
        
        elementos.append(tabela_conselho)
        elementos.append(Spacer(1, 20))
        
        return elementos
    
    def _criar_secao_envios_sede(self, envios):
        """Cria seção de lista de envios à sede"""
        elementos = []
        
        secao_style = ParagraphStyle(
            'SecaoSede',
            parent=self.styles['cabecalho_secao'],
            fontSize=14,
            textColor=colors.HexColor('#4A7C59'),  # Verde do logo OBPC
            alignment=TA_LEFT,
            spaceAfter=10,
            fontName='Helvetica-Bold'
        )
        
        elementos.append(Paragraph("📤 LISTA DE ENVIOS À SEDE", secao_style))
        
        # Preparar dados dos envios com header
        dados_envios = [['PROJETO/DESTINO', 'VALOR ENVIADO']]
        total_envio = 0
        
        # Mapeamento de nomes para exibição
        nomes_exibicao = {
            'oferta_voluntaria_conchas': '🌊 Oferta Voluntária Conchas',
            'site': '💻 Site OBPC',
            'projeto_filipe': '👨‍⚕️ Projeto Filipe',
            'forca_para_viver': '💪 Força para Viver',
            'contador_sede': '📊 Contador Sede'
        }
        
        for chave, valor in envios.items():
            nome_exibir = nomes_exibicao.get(chave, chave.replace('_', ' ').title())
            dados_envios.append([nome_exibir, self._formatar_moeda(valor)])
            total_envio += valor
        
        # Adicionar valor do conselho (30% do total)
        percentual_conselho = self.config.percentual_conselho if hasattr(self.config, 'percentual_conselho') else 30
        valor_conselho = totais['total_geral'] * (percentual_conselho / 100)
        dados_envios.append([f'🏛️ Conselho ({percentual_conselho}% do total)', self._formatar_moeda(valor_conselho)])
        total_envio += valor_conselho
        
        # Tabela de envios com header
        tabela_envios = Table(dados_envios, colWidths=[12*cm, 4*cm])
        tabela_envios.setStyle(TableStyle([
            # Header (primeira linha)
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2E86AB')),  # Azul do logo
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('ALIGN', (0, 0), (0, 0), 'LEFT'),
            ('ALIGN', (1, 0), (1, 0), 'CENTER'),
            
            # Dados (demais linhas)
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 1), (-1, -1), 11),
            ('ALIGN', (0, 1), (0, -1), 'LEFT'),
            ('ALIGN', (1, 1), (1, -1), 'RIGHT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('LEFTPADDING', (0, 0), (-1, -1), 12),
            ('RIGHTPADDING', (0, 0), (-1, -1), 12),
            
            # Cores alternadas para as linhas de dados
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.HexColor('#F0F8FF'), colors.HexColor('#E8F0FF')]),
            ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#CCCCCC')),
            ('TEXTCOLOR', (1, 1), (1, -1), colors.HexColor('#2E86AB')),  # Azul para valores
            
            # Bordas mais elegantes
            ('LINEBELOW', (0, 0), (-1, 0), 2, colors.HexColor('#2E86AB')),  # Linha abaixo do header
        ]))
        
        elementos.append(tabela_envios)
        
        # Espaçamento antes do total
        elementos.append(Spacer(1, 10))
        
        # Total de envio destacado
        total_dados = [['🏛️ TOTAL ENVIADO PARA SEDE', self._formatar_moeda(total_envio)]]
        tabela_total_envio = Table(total_dados, colWidths=[12*cm, 4*cm])
        tabela_total_envio.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#2E86AB')),  # Azul do logo
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 14),
            ('ALIGN', (0, 0), (0, -1), 'LEFT'),
            ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('TOPPADDING', (0, 0), (-1, -1), 12),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
            ('LEFTPADDING', (0, 0), (-1, -1), 12),
            ('RIGHTPADDING', (0, 0), (-1, -1), 12),
            ('GRID', (0, 0), (-1, -1), 2, colors.HexColor('#1A5A7A')),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.white),
            # Sombra sutil
            ('LINEBEFORE', (0, 0), (-1, -1), 3, colors.HexColor('#5CA7C9')),
        ]))
        
        elementos.append(tabela_total_envio)
        elementos.append(Spacer(1, 30))
        
        return elementos
    
    def _criar_secao_total_envio_sede(self, totais, envios):
        """Cria seção do total de envio para sede (conselho + projetos)"""
        elementos = []
        
        secao_style = ParagraphStyle(
            'SecaoSede',
            parent=self.styles['cabecalho_secao'],
            fontSize=14,
            textColor=colors.HexColor('#2E86AB'),  # Azul do logo OBPC
            alignment=TA_LEFT,
            spaceAfter=10,
            fontName='Helvetica-Bold'
        )
        
        elementos.append(Paragraph("📋 TOTAL DE ENVIO PARA SEDE", secao_style))
        
        # Calcular total dos envios (projetos/contador/etc)
        total_envio_projetos = sum(envios.values())
        
        # Valor do conselho administrativo
        valor_conselho = totais['valor_conselho']
        
        # Total geral para sede
        total_geral_sede = valor_conselho + total_envio_projetos
        
        # Preparar dados da tabela
        dados_total_envio = [
            [f'Valor do Conselho Administrativo ({int(self.config.percentual_conselho)}%)', self._formatar_moeda(valor_conselho)],
            ['Total dos Projetos/Contador/Ofertas', self._formatar_moeda(total_envio_projetos)],
        ]
        
        # Tabela de composição
        tabela_composicao = Table(dados_total_envio, colWidths=[12*cm, 4*cm])
        tabela_composicao.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 11),
            ('ALIGN', (0, 0), (0, -1), 'LEFT'),
            ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('ROWBACKGROUNDS', (0, 0), (-1, -1), [colors.HexColor('#F0F8F0')]),  # Verde muito claro
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('TEXTCOLOR', (1, 0), (1, -1), colors.HexColor('#2E86AB')),  # Azul do logo
        ]))
        
        elementos.append(tabela_composicao)
        
        # Total geral destacado
        total_geral_dados = [['TOTAL GERAL PARA SEDE', self._formatar_moeda(total_geral_sede)]]
        tabela_total_geral = Table(total_geral_dados, colWidths=[12*cm, 4*cm])
        tabela_total_geral.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#4A7C59')),  # Verde do logo
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 14),
            ('ALIGN', (0, 0), (0, -1), 'LEFT'),
            ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('TOPPADDING', (0, 0), (-1, -1), 12),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
            ('GRID', (0, 0), (-1, -1), 2, colors.black),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.white),  # Texto branco sobre verde do logo
        ]))
        
        elementos.append(tabela_total_geral)
        elementos.append(Spacer(1, 30))
        
        return elementos
    
    def _criar_assinaturas_sede(self):
        """Cria seções de assinaturas oficiais"""
        elementos = []
        
        elementos.append(Spacer(1, 40))
        
        # Campos de assinatura em tabela
        dados_assinatura = [
            ['_' * 40, '_' * 40],
            ['Pastor João Silva', 'Maria Santos'],
            ['DIRIGENTE', 'TESOUREIRO(A)']
        ]
        
        tabela_assinatura = Table(dados_assinatura, colWidths=[8*cm, 8*cm])
        tabela_assinatura.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('FONTNAME', (0, 1), (-1, 1), 'Helvetica-Bold'),  # Nomes
            ('FONTNAME', (0, 2), (-1, 2), 'Helvetica'),        # Cargos
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('FONTSIZE', (0, 2), (-1, 2), 9),                  # Cargos menores
            ('TOPPADDING', (0, 0), (-1, 0), 5),               # Linha de assinatura
            ('TOPPADDING', (0, 1), (-1, 1), 10),              # Nomes
            ('TOPPADDING', (0, 2), (-1, 2), 5),               # Cargos
            ('TEXTCOLOR', (0, 2), (-1, 2), colors.grey),      # Cargos em cinza
        ]))
        
        elementos.append(tabela_assinatura)
        elementos.append(Spacer(1, 30))
        
        return elementos
    
    def _criar_rodape_sede(self):
        """Cria rodapé com data e local"""
        elementos = []
        
        # Data e local
        data_atual = datetime.now()
        meses = [
            '', 'Janeiro', 'Fevereiro', 'Março', 'Abril', 'Maio', 'Junho',
            'Julho', 'Agosto', 'Setembro', 'Outubro', 'Novembro', 'Dezembro'
        ]
        
        data_extenso = f"Tietê, {data_atual.day} de {meses[data_atual.month]} de {data_atual.year}"
        
        data_style = ParagraphStyle(
            'DataLocal',
            parent=self.styles['texto_normal'],
            fontSize=12,
            textColor=colors.black,
            alignment=TA_CENTER,
            fontName='Helvetica-Bold'
        )
        
        elementos.append(Paragraph(data_extenso, data_style))
        elementos.append(Spacer(1, 20))
        
        # Linha de separação
        elementos.append(HRFlowable(width="100%", thickness=0.5, color=colors.grey))
        elementos.append(Spacer(1, 10))
        
        # Rodapé do sistema
        rodape_style = ParagraphStyle(
            'RodapeSistema',
            parent=self.styles['texto_normal'],
            fontSize=9,
            textColor=colors.grey,
            alignment=TA_CENTER,
            fontName='Helvetica'
        )
        
        sistema_info = f"Sistema Administrativo OBPC - Relatório gerado em {data_atual.strftime('%d/%m/%Y às %H:%M')}"
        elementos.append(Paragraph(sistema_info, rodape_style))
        
        return elementos
    
    def _truncar_texto(self, texto, max_chars):
        """Trunca texto para evitar sobreposição nas células da tabela"""
        if not texto or len(texto) <= max_chars:
            return texto
        return texto[:max_chars-3] + "..."


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