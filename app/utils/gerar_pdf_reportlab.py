import os
from datetime import datetime, timedelta
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
        
        # Logo da configuração sempre presente
        try:
            # Usar logo da configuração se disponível
            if self.config.logo and os.path.exists(self.config.logo):
                logo_path = self.config.logo
            else:
                # Fallback para logo padrão
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
        
        # Cidade da configuração abaixo do logo (mais limpo)
        cidade_texto = f"{self.config.cidade.upper()} - SP" if self.config.cidade else "TIETÊ - SP"
        elementos.append(Paragraph(cidade_texto, self.styles['subtitulo_igreja']))
        
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
            larguras = [2.0*cm, 5.0*cm, 2.5*cm, 1.6*cm, 2.2*cm, 2.2*cm, 2.5*cm]  # Total: 18cm
        else:
            colunas = ['Data', 'Descrição', 'Categoria', 'Tipo', 'Valor', 'Comprovante']
            larguras = [2.0*cm, 6.0*cm, 2.8*cm, 1.8*cm, 2.2*cm, 2.2*cm]  # Total: 17cm
        
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
            descricao = self._truncar_texto(lancamento.descricao or '-', 32)
            categoria = self._truncar_texto(lancamento.categoria or '-', 14)
            
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
            altura_minima = [28]  # Cabeçalho maior
            for _ in range(len(dados) - 1):  # Dados
                altura_minima.append(32)  # Altura aumentada para não sobrepor as linhas
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
            ('TOPPADDING', (0, 1), (-1, -1), 12),    # Mais espaçamento vertical
            ('BOTTOMPADDING', (0, 1), (-1, -1), 12), # Mais espaçamento vertical
            ('LEFTPADDING', (0, 0), (-1, -1), 8),    # Mais espaçamento lateral
            ('RIGHTPADDING', (0, 0), (-1, -1), 8),   # Mais espaçamento lateral
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
            
            # Ajustar larguras para evitar sobreposição
            tabela_entradas = Table(dados_entradas, colWidths=[9*cm, 4.5*cm, 2.5*cm])
            self._aplicar_estilo_tabela_resumo(tabela_entradas, colors.green)
            elementos.append(tabela_entradas)
            elementos.append(Spacer(1, 15))
            
            # Seção 2: Saídas/Despesas (incluindo fixas)
            elementos.append(Paragraph("SAÍDAS E DESPESAS", self.styles['cabecalho_secao']))
            
            dados_saidas = [
                ['CATEGORIA', 'VALOR', '%']
            ]
            
            # Calcular total de saídas dos lançamentos REAIS (SEM despesas fixas e conselho)
            # O relatório de CAIXA mostra apenas movimentações reais, não projeções
            total_saidas_lancamentos = sum(totais_categoria['saidas'].values())
            
            # Total de saídas = apenas lançamentos reais
            total_saidas_geral = total_saidas_lancamentos
            
            # Adicionar apenas categorias de lançamentos REAIS
            for categoria, valor in totais_categoria['saidas'].items():
                percentual = (valor / total_saidas_geral * 100) if total_saidas_geral > 0 else 0
                dados_saidas.append([
                    categoria.title(),
                    f"-{self._formatar_moeda(valor)}",
                    f"{percentual:.1f}%"
                ])
            
            dados_saidas.append([
                'TOTAL SAÍDAS',
                f"-{self._formatar_moeda(total_saidas_geral)}",
                '100.0%'
            ])
            
            # Ajustar larguras para evitar sobreposição
            tabela_saidas = Table(dados_saidas, colWidths=[9*cm, 4.5*cm, 2.5*cm])
            self._aplicar_estilo_tabela_resumo(tabela_saidas, colors.red)
            elementos.append(tabela_saidas)
            elementos.append(Spacer(1, 20))
            
            # Seção 3: Resumo por Tipo de Conta
            # Usar KeepTogether para manter a tabela na mesma página
            elementos_conta = []
            elementos_conta.append(Paragraph("RESUMO POR CONTA", self.styles['cabecalho_secao']))
            
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
            
            # Ajustar larguras para evitar sobreposição
            tabela_conta = Table(dados_conta, colWidths=[5*cm, 3.5*cm, 3.5*cm, 4*cm])
            self._aplicar_estilo_tabela_resumo(tabela_conta, colors.HexColor('#001f3f'))
            elementos_conta.append(tabela_conta)
            
            # Manter tudo junto na mesma página
            from reportlab.platypus import KeepTogether
            elementos.append(KeepTogether(elementos_conta))
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
            
            # Ajustar larguras para evitar sobreposição
            tabela_distribuicao = Table(dados_distribuicao, colWidths=[5*cm, 3*cm, 5*cm, 3*cm])
            
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
            # Relatório de CAIXA: apenas lançamentos reais, sem despesas fixas ou conselho
            total_saidas_final = sum(totais_categoria['saidas'].values())
        else:
            total_entradas_final = entradas_total
            total_saidas_final = saidas_total
        
        saldo_bruto = saldo_anterior + total_entradas_final - total_saidas_final
        
        # Calcular total a ser enviado para a sede (30% + despesas fixas)
        # 1. Calcular 30% administrativo
        dizimos = 0.0
        ofertas_alcadas = 0.0
        
        if lancamentos:
            for lancamento in lancamentos:
                if lancamento.tipo.lower() == 'entrada':
                    categoria_lower = lancamento.categoria.lower() if lancamento.categoria else ''
                    valor = lancamento.valor or 0.0
                    
                    # Dízimos
                    if 'dizimo' in categoria_lower or 'dízimo' in categoria_lower:
                        dizimos += valor
                    # Ofertas Alçadas (excluindo OMN e Outras Ofertas)
                    elif 'oferta' in categoria_lower:
                        if 'omn' in categoria_lower or 'missionaria' in categoria_lower or 'missionária' in categoria_lower:
                            continue
                        elif any(x in categoria_lower for x in ['outras', 'especial', 'voluntaria', 'voluntária']):
                            continue
                        else:
                            ofertas_alcadas += valor
        
        base_calculo = dizimos + ofertas_alcadas
        valor_administrativo = base_calculo * (self.config.percentual_conselho / 100)
        
        # 2. Buscar despesas fixas
        total_despesas_fixas = 0.0
        try:
            from app.financeiro.despesas_fixas_model import DespesaFixaConselho
            despesas_fixas = DespesaFixaConselho.obter_despesas_ativas()
            total_despesas_fixas = sum(d.valor_padrao for d in despesas_fixas)
        except Exception as e:
            current_app.logger.warning(f'Erro ao buscar despesas fixas: {str(e)}')
        
        # 3. Total a ser enviado
        total_envio_sede = valor_administrativo + total_despesas_fixas
        
        # 4. Saldo real disponível = igual ao saldo bruto
        # (Administrativo e Despesas Fixas JÁ estão incluídas nas saídas, são apenas informativos)
        saldo_real_disponivel = saldo_bruto
        
        dados_resumo = [
            ['DESCRIÇÃO', 'VALOR'],
            ['Saldo Anterior', self._formatar_moeda(saldo_anterior)],
            ['Total de Entradas', f"+{self._formatar_moeda(total_entradas_final)}"],
            ['Total de Saídas', f"-{self._formatar_moeda(total_saidas_final)}"],
            ['Saldo Bruto do Período', self._formatar_moeda(saldo_bruto)],
            ['(INFORME) Total a Enviar Sede', f"{self._formatar_moeda(total_envio_sede)}"],
            ['    • Administrativo (30%)', f"{self._formatar_moeda(valor_administrativo)}"],
            ['    • Despesas Fixas', f"{self._formatar_moeda(total_despesas_fixas)}"],
            ['SALDO DISPONÍVEL', self._formatar_moeda(saldo_bruto)]
        ]
        
        # Ajustar larguras para evitar sobreposição
        tabela_resumo = Table(dados_resumo, colWidths=[10*cm, 5*cm])
        
        estilo_resumo = [
            # Cabeçalho
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#001f3f')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            
            # Dados normais
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -4), 11),
            ('ALIGN', (0, 1), (0, -1), 'LEFT'),
            ('ALIGN', (1, 1), (1, -1), 'RIGHT'),
            
            # Linha "Total a Enviar Sede" em destaque
            ('BACKGROUND', (0, -4), (-1, -4), colors.HexColor('#FFE4E1')),
            ('FONTNAME', (0, -4), (-1, -4), 'Helvetica-Bold'),
            ('TEXTCOLOR', (0, -4), (1, -4), colors.HexColor('#DC143C')),
            
            # Sublinhas de detalhamento (administrativo e despesas fixas) - menor e indentadas
            ('FONTSIZE', (0, -3), (0, -2), 9),
            ('TEXTCOLOR', (0, -3), (1, -2), colors.grey),
            ('LEFTPADDING', (0, -3), (0, -2), 20),
            
            # Linha do saldo disponível (final)
            # Cor será definida dinamicamente abaixo (verde se positivo, vermelho se negativo)
            ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, -1), (-1, -1), 14),
            ('TEXTCOLOR', (0, -1), (-1, -1), colors.white),
            
            # Bordas
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ]
        
        # Cores para entradas e saídas
        estilo_resumo.append(('TEXTCOLOR', (1, 2), (1, 2), colors.green))  # Entradas
        estilo_resumo.append(('TEXTCOLOR', (1, 3), (1, 3), colors.red))    # Saídas
        
        # Cor para movimento do período (Saldo Bruto)
        if saldo_bruto >= 0:
            estilo_resumo.append(('TEXTCOLOR', (1, 4), (1, 4), colors.green))
        else:
            estilo_resumo.append(('TEXTCOLOR', (1, 4), (1, 4), colors.red))
        
        # Cor para Saldo Disponível (verde se positivo, vermelho se negativo)
        if saldo_bruto >= 0:
            estilo_resumo.append(('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#4A7C59')))  # Verde
        else:
            estilo_resumo.append(('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#DC143C')))  # Vermelho
        
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
        
        # Usar timezone de Brasília (UTC-3)
        from datetime import timezone, timedelta
        brasilia_tz = timezone(timedelta(hours=-3))
        data_atual = datetime.now(brasilia_tz).strftime('%d/%m/%Y às %H:%M')
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
        try:
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
                        " "  # Espaço em vez de string vazia
                    ])
                elif self.config.campo_assinatura_2:
                    dados_assinatura.append([
                        " ",  # Espaço em vez de string vazia
                        f"______________________________\n{self.config.campo_assinatura_2}"
                    ])
                
                # Só cria tabela se houver dados válidos
                if dados_assinatura and len(dados_assinatura) > 0:
                    tabela_assinatura = Table(dados_assinatura, colWidths=[8*cm, 8*cm])
                    # Usar índices específicos ao invés de -1
                    num_rows = len(dados_assinatura)
                    num_cols = len(dados_assinatura[0]) if dados_assinatura else 0
                    
                    if num_rows > 0 and num_cols > 0:
                        tabela_assinatura.setStyle(TableStyle([
                            ('ALIGN', (0, 0), (num_cols-1, num_rows-1), 'CENTER'),
                            ('VALIGN', (0, 0), (num_cols-1, num_rows-1), 'TOP'),
                            ('FONTNAME', (0, 0), (num_cols-1, num_rows-1), self.config.fonte_relatorio or 'Helvetica'),
                            ('FONTSIZE', (0, 0), (num_cols-1, num_rows-1), 10),
                            ('TOPPADDING', (0, 0), (num_cols-1, num_rows-1), 20),
                        ]))
                        elementos.append(tabela_assinatura)
        except Exception as e:
            # Se houver erro na tabela de assinatura, apenas loga e continua sem ela
            import logging
            logging.error(f"Erro ao criar campos de assinatura: {e}")
        
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
            # Truncar nome para caber na coluna (mais espaço agora)
            nome_truncado = nome_arquivo if len(nome_arquivo) <= 20 else nome_arquivo[:17] + '...'
            link_html = f'<link href="{url_comprovante}">📎 {nome_truncado}</link>'
            return Paragraph(link_html, self.styles['texto_normal'])
        else:
            return "-"
    
    def gerar_relatorio_caixa(self, lancamentos, mes, ano, saldo_anterior=0):
        """Gera relatório de caixa profissional com padrão oficial"""
        try:
            doc = SimpleDocTemplate(
                self.buffer, 
                pagesize=self.pagesize,
                rightMargin=2*cm, 
                leftMargin=2*cm,
                topMargin=1.5*cm, 
                bottomMargin=2*cm,
                title=f"Relatório de Caixa {mes:02d}/{ano}"
            )
            
            elementos = []
            
            # Cabeçalho oficial (mesmo padrão do relatório sede)
            try:
                elementos.extend(self._criar_cabecalho_caixa_oficial())
            except Exception as e:
                current_app.logger.error(f"Erro ao criar cabeçalho: {e}")
            
            # Informações do período e igreja
            try:
                elementos.extend(self._criar_info_periodo_caixa(mes, ano))
            except Exception as e:
                current_app.logger.error(f"Erro ao criar info período: {e}")
            
            if lancamentos:
                # Tabela de lançamentos
                try:
                    elementos.extend(self._criar_tabela_lancamentos(lancamentos, mostrar_saldo=True))
                except Exception as e:
                    current_app.logger.error(f"Erro ao criar tabela lançamentos: {e}")
                
                # Calcular totais corrigindo o problema das saídas
                entradas_total = sum(float(l.valor) for l in lancamentos if l.tipo.lower() == 'entrada')
                saidas_total = sum(float(l.valor) for l in lancamentos if l.tipo.lower() in ['saída', 'saida'])
                
                # Resumo financeiro
                try:
                    elementos.extend(self._criar_resumo_financeiro(entradas_total, saidas_total, saldo_anterior, lancamentos))
                except Exception as e:
                    current_app.logger.error(f"Erro ao criar resumo financeiro: {e}")
            else:
                elementos.append(Paragraph("Nenhum lançamento encontrado para este período.", 
                                         self.styles['texto_normal']))
            
            # Campos de assinatura
            try:
                elementos.extend(self._criar_campos_assinatura())
            except Exception as e:
                current_app.logger.error(f"Erro ao criar campos assinatura: {e}")
            
            # Rodapé
            try:
                elementos.extend(self._criar_rodape())
            except Exception as e:
                current_app.logger.error(f"Erro ao criar rodapé: {e}")
            
            # Gerar PDF
            doc.build(elementos)
            self.buffer.seek(0)
            return self.buffer
            
        except Exception as e:
            current_app.logger.error(f"Erro geral ao gerar relatório caixa: {e}")
            import traceback
            current_app.logger.error(traceback.format_exc())
            raise
    
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
            
            # Obter envios reais dos lançamentos
            envios, envios_detalhados = self._calcular_envios_reais_sede(lancamentos)
            
            # SEÇÃO 1: ARRECADAÇÃO DO MÊS
            elementos.extend(self._criar_secao_arrecadacao_sede(totais))
            
            # SEÇÃO 2: DESPESAS FINANCEIRAS
            elementos.extend(self._criar_secao_despesas_sede(totais))
            
            # SEÇÃO 3: SALDO DO MÊS
            elementos.extend(self._criar_secao_saldo_sede(totais))
            
            # SEÇÃO 4: VALOR DO CONSELHO ADMINISTRATIVO
            elementos.extend(self._criar_secao_conselho_sede(totais))
            
            # SEÇÃO 5: DETALHAMENTO DOS ENVIOS À SEDE
            elementos.extend(self._criar_secao_detalhamento_envios_sede(envios_detalhados))
            
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
        
        # Logo da configuração no cabeçalho da sede
        logo_carregada = False
        try:
            # Usar logo da configuração se disponível
            if self.config and self.config.logo:
                current_app.logger.info(f'Tentando carregar logo: {self.config.logo}')
                
                # Construir caminho absoluto do logo
                if self.config.logo.startswith('static/'):
                    # Remove 'static/' do início para usar com static_folder
                    logo_filename = self.config.logo.replace('static/', '')
                    logo_path = os.path.join(current_app.static_folder, logo_filename)
                    current_app.logger.info(f'Caminho logo (static/): {logo_path}')
                elif self.config.logo.startswith('uploads/'):
                    # Logo está em uploads
                    logo_path = os.path.join(current_app.root_path, '..', self.config.logo)
                    current_app.logger.info(f'Caminho logo (uploads/): {logo_path}')
                else:
                    # Tenta diretamente
                    logo_path = os.path.join(current_app.root_path, '..', self.config.logo)
                    current_app.logger.info(f'Caminho logo (direto): {logo_path}')
                
                if os.path.exists(logo_path):
                    current_app.logger.info(f'Logo encontrada em: {logo_path}')
                    logo = Image(logo_path, width=180, height=120)
                    logo.hAlign = 'CENTER'
                    elementos.append(logo)
                    elementos.append(Spacer(1, 20))
                    logo_carregada = True
                else:
                    current_app.logger.warning(f'Logo não encontrada em: {logo_path}')
            
            # Se não carregou, tenta fallback
            if not logo_carregada:
                current_app.logger.info('Tentando logos de fallback...')
                fallback_logos = ['Logo_OBPC.jpg', 'logo_obpc_novo.jpg', 'logo_igreja_20251025_164525.jpg']
                for fallback_logo in fallback_logos:
                    test_path = os.path.join(current_app.static_folder, fallback_logo)
                    current_app.logger.info(f'Testando: {test_path}')
                    if os.path.exists(test_path):
                        current_app.logger.info(f'Logo fallback encontrada: {test_path}')
                        logo = Image(test_path, width=180, height=120)
                        logo.hAlign = 'CENTER'
                        elementos.append(logo)
                        elementos.append(Spacer(1, 20))
                        logo_carregada = True
                        break
                
                if not logo_carregada:
                    current_app.logger.warning('Nenhuma logo encontrada (nem configuração nem fallback)')
                    
        except Exception as e:
            # Log do erro para debug
            current_app.logger.error(f'Erro ao carregar logo no PDF: {str(e)}')
            import traceback
            current_app.logger.error(traceback.format_exc())
        
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
        
        # Cidade da configuração (mais limpo e profissional)
        cidade_texto = f"{self.config.cidade.upper()} - SP" if self.config.cidade else "TIETÊ - SP"
        elementos.append(Paragraph(cidade_texto, subtitulo_style))
        
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
        periodo_formatado = f'{mes:02d}/{ano}'
        
        # Garantir que todos os valores sejam strings não vazias
        dados_igreja = [
            ['Cidade:', str(self.config.cidade or 'Tietê'), 'Dirigente:', str(self.config.presidente or 'Pastor não informado')],
            ['Bairro:', str(self.config.bairro or 'Centro'), 'Tesoureiro:', str(self.config.primeiro_tesoureiro or 'Tesoureiro não informado')],
            ['Mês/Ano:', periodo_formatado, 'Data Relatório:', datetime.now().strftime('%d/%m/%Y')],
        ]
        
        # Calcular índices explícitos
        num_rows = len(dados_igreja)  # 3
        num_cols = len(dados_igreja[0])  # 4
        
        tabela_info = Table(dados_igreja, colWidths=[3*cm, 4*cm, 3*cm, 4*cm])
        tabela_info.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (num_cols-1, num_rows-1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (num_cols-1, num_rows-1), 10),
            ('FONTNAME', (0, 0), (0, num_rows-1), 'Helvetica-Bold'),  # Labels primeira coluna
            ('FONTNAME', (2, 0), (2, num_rows-1), 'Helvetica-Bold'),  # Labels terceira coluna
            ('ALIGN', (0, 0), (num_cols-1, num_rows-1), 'LEFT'),
            ('VALIGN', (0, 0), (num_cols-1, num_rows-1), 'MIDDLE'),
            ('TOPPADDING', (0, 0), (num_cols-1, num_rows-1), 8),
            ('BOTTOMPADDING', (0, 0), (num_cols-1, num_rows-1), 8),
            ('LEFTPADDING', (0, 0), (num_cols-1, num_rows-1), 0),
            ('RIGHTPADDING', (1, 0), (1, num_rows-1), 20),  # Espaço entre colunas
        ]))
        
        elementos.append(tabela_info)
        elementos.append(Spacer(1, 20))
        elementos.append(HRFlowable(width="100%", thickness=1, color=colors.grey))
        elementos.append(Spacer(1, 20))
        
        return elementos
    
    def _criar_cabecalho_caixa_oficial(self):
        """Cria cabeçalho oficial da igreja para relatório de caixa (mesmo padrão do relatório sede)"""
        elementos = []
        
        # Logo da configuração
        try:
            if self.config.logo and self.config.exibir_logo_relatorio:
                # Construir caminho absoluto do logo
                if self.config.logo.startswith('static/'):
                    logo_filename = self.config.logo.replace('static/', '')
                    logo_path = os.path.join(current_app.static_folder, logo_filename)
                else:
                    logo_path = os.path.join(current_app.root_path, '..', self.config.logo)
            else:
                # Fallback para logos padrão
                fallback_logos = ['Logo_OBPC.jpg', 'logo_obpc_novo.jpg', 'logo_igreja_20251025_164525.jpg']
                logo_path = None
                for fallback_logo in fallback_logos:
                    test_path = os.path.join(current_app.static_folder, fallback_logo)
                    if os.path.exists(test_path):
                        logo_path = test_path
                        break
            
            if logo_path and os.path.exists(logo_path):
                logo = Image(logo_path, width=180, height=120)
                logo.hAlign = 'CENTER'
                elementos.append(logo)
                elementos.append(Spacer(1, 20))
        except Exception as e:
            current_app.logger.warning(f'Erro ao carregar logo: {str(e)}')
            pass
        
        # Estilos
        titulo_style = ParagraphStyle(
            'TituloCaixa',
            parent=self.styles['titulo_principal'],
            fontSize=18,
            textColor=colors.HexColor('#4A7C59'),
            alignment=TA_CENTER,
            spaceAfter=5,
            fontName='Helvetica-Bold'
        )
        
        subtitulo_style = ParagraphStyle(
            'SubtituloCaixa',
            parent=self.styles['titulo_principal'],
            fontSize=14,
            textColor=colors.black,
            alignment=TA_CENTER,
            spaceAfter=15,
            fontName='Helvetica-Bold'
        )
        
        # Cidade da configuração
        cidade_texto = f"{self.config.cidade.upper()} - SP" if self.config.cidade else "TIETÊ - SP"
        elementos.append(Paragraph(cidade_texto, subtitulo_style))
        
        # Título do relatório
        elementos.append(Paragraph("RELATÓRIO DE CAIXA (INTERNO)", subtitulo_style))
        
        # Linha horizontal decorativa
        elementos.append(HRFlowable(width="60%", thickness=2, color=colors.HexColor('#2E86AB')))
        elementos.append(Spacer(1, 15))
        
        return elementos
    
    def _criar_info_periodo_caixa(self, mes, ano):
        """Cria seção com informações do período e dados da igreja para relatório de caixa"""
        elementos = []
        
        # Dados da igreja em tabela
        periodo_formatado = f'{mes:02d}/{ano}'
        
        # Garantir que todos os valores sejam strings não vazias
        dados_igreja = [
            ['Cidade:', str(self.config.cidade or 'Tietê'), 'Dirigente:', str(self.config.presidente or 'Pastor não informado')],
            ['Bairro:', str(self.config.bairro or 'Centro'), 'Tesoureiro:', str(self.config.primeiro_tesoureiro or 'Tesoureiro não informado')],
            ['Mês/Ano:', periodo_formatado, 'Data Relatório:', datetime.now().strftime('%d/%m/%Y')],
        ]
        
        # Calcular índices explícitos
        num_rows = len(dados_igreja)  # 3
        num_cols = len(dados_igreja[0])  # 4
        
        tabela_info = Table(dados_igreja, colWidths=[3*cm, 4*cm, 3*cm, 4*cm])
        tabela_info.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (num_cols-1, num_rows-1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (num_cols-1, num_rows-1), 10),
            ('FONTNAME', (0, 0), (0, num_rows-1), 'Helvetica-Bold'),  # Labels primeira coluna
            ('FONTNAME', (2, 0), (2, num_rows-1), 'Helvetica-Bold'),  # Labels terceira coluna
            ('ALIGN', (0, 0), (num_cols-1, num_rows-1), 'LEFT'),
            ('VALIGN', (0, 0), (num_cols-1, num_rows-1), 'MIDDLE'),
            ('TOPPADDING', (0, 0), (num_cols-1, num_rows-1), 8),
            ('BOTTOMPADDING', (0, 0), (num_cols-1, num_rows-1), 8),
            ('LEFTPADDING', (0, 0), (num_cols-1, num_rows-1), 0),
            ('RIGHTPADDING', (1, 0), (1, num_rows-1), 20),
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
            'oferta_omn': 0,
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
                    # Lógica corrigida e padronizada das ofertas:
                    # 1º: Verificar se é OMN (não computa no conselho, mas registrado)
                    if 'omn' in categoria_lower or 'missionaria' in categoria_lower or 'missionária' in categoria_lower:
                        totais['oferta_omn'] += valor
                    # 2º: Verificar se é "Outras Ofertas" (não computa no conselho)
                    elif any(x in categoria_lower for x in ['outras', 'especial', 'voluntaria', 'voluntária']):
                        totais['outras_ofertas'] += valor
                    # 3º: O resto são Ofertas Alçadas (computa 30% conselho)
                    else:
                        # Ofertas Alçadas = ofertas normais do ofertório
                        totais['ofertas_alcadas'] += valor
                
                totais['total_geral'] += valor
            
            elif lancamento.tipo == 'Saída':
                totais['despesas_financeiras'] += valor
        
        # Calcular valores finais
        # Buscar percentual do conselho das configurações
        percentual = self.config.percentual_conselho / 100
        # Calcular valor do conselho: APENAS Dízimos + Ofertas Alçadas (excluindo OMN e Outras Ofertas)
        base_conselho = totais['dizimos'] + totais['ofertas_alcadas']
        totais['valor_conselho'] = base_conselho * percentual
        
        # Calcular saldo do mês: Entradas - Saídas Lançadas (despesas fixas e conselho são informativos)
        totais['saldo_mes'] = totais['total_geral'] - totais['despesas_financeiras']
        
        return totais
    
    def _calcular_envios_reais_sede(self, lancamentos):
        """Calcula envios reais baseados nos lançamentos de saída"""
        # Buscar lançamentos de saída que correspondem aos envios
        lancamentos_saida = [l for l in lancamentos if l.tipo == 'Saída']
        
        envios = {
            'oferta_voluntaria_conchas': 0.0,
            'site': 0.0,
            'projeto_filipe': 0.0,
            'forca_para_viver': 0.0,
            'contador_sede': 0.0
        }
        
        # Lista detalhada para o PDF
        envios_detalhados = {
            'oferta_voluntaria_conchas': [],
            'site': [],
            'projeto_filipe': [],
            'forca_para_viver': [],
            'contador_sede': [],
            'omn': []
        }
        
        # Mapear descrições para chaves
        mapeamento_envios = {
            'oferta_voluntaria_conchas': ['conchas', 'voluntaria conchas', 'oferta voluntaria conchas'],
            'site': ['site'],
            'projeto_filipe': ['projeto filipe', 'filipe'],
            'forca_para_viver': ['força para viver', 'forca para viver'],
            'contador_sede': ['contador sede', 'contador'],
            'omn': ['omn', 'obra missionaria', 'missionaria']
        }
        
        # Buscar valores nos lançamentos de saída
        for lancamento in lancamentos_saida:
            if lancamento.descricao:
                descricao_lower = lancamento.descricao.lower()
                
                # Verificar cada tipo de envio
                for chave, termos_busca in mapeamento_envios.items():
                    for termo in termos_busca:
                        if termo in descricao_lower:
                            envios[chave] += lancamento.valor
                            # Adicionar detalhes para o PDF
                            envios_detalhados[chave].append({
                                'data': lancamento.data,
                                'descricao': lancamento.descricao,
                                'valor': lancamento.valor,
                                'conta': lancamento.conta
                            })
                            break  # Para evitar dupla contagem
        
        # Adicionar ofertas OMN automaticamente aos envios detalhados
        for lancamento in lancamentos:
            if lancamento.tipo == 'Entrada' and lancamento.categoria:
                categoria_lower = lancamento.categoria.lower()
                if 'omn' in categoria_lower or 'missionaria' in categoria_lower:
                    envios_detalhados['omn'].append({
                        'data': lancamento.data,
                        'descricao': lancamento.categoria,
                        'conta': getattr(lancamento, 'conta', None),
                        'valor': float(lancamento.valor) if lancamento.valor else 0
                    })
        
        return envios, envios_detalhados

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
            ['Ofertas OMN', self._formatar_moeda(totais.get('oferta_omn', 0))],
            ['Outras Ofertas', self._formatar_moeda(totais['outras_ofertas'])],
        ]
        
        tabela_arrecadacao = Table(dados_arrecadacao, colWidths=[11*cm, 5*cm])
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
        # Calcular valor do conselho: APENAS Dízimos + Ofertas Alçadas
        base_calculo = totais.get('dizimos', 0) + totais.get('ofertas_alcadas', 0)
        valor_conselho = base_calculo * (percentual_conselho / 100)
        
        texto_info = f"""
        <b>INFORMAÇÕES IMPORTANTES:</b><br/>
        • Base para cálculo 30%: <b>{self._formatar_moeda(base_calculo)}</b> (Dízimos + Ofertas Alçadas, EXCLUINDO Outras Ofertas de {self._formatar_moeda(totais.get('outras_ofertas', 0))})<br/>
        • 30% para Sede: <b>{self._formatar_moeda(valor_conselho)}</b> (valor informativo, não deduzido do saldo)<br/>
        • As Ofertas OMN são direcionadas diretamente à convenção (não passam pelo caixa local)<br/>
        • As OUTRAS OFERTAS não entram no cálculo do valor administrativo<br/>
        • Saldo correto: <b>{self._formatar_moeda(totais.get('saldo_mes', 0))}</b> (considerando apenas lançamentos reais)
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
        
        elementos.append(Paragraph("SALDO DO MÊS", secao_style))
        
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
        # Base de cálculo: Dízimos + Ofertas Alçadas (excluindo OMN e Outras Ofertas)
        base_calculo = totais['dizimos'] + totais['ofertas_alcadas']
        descricao = f'Valor a ser entregue à sede ({percentual}% de Dízimos + Ofertas Alçadas)'
        
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
    
    def _criar_secao_envios_sede(self, envios, totais):
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
        
        elementos.append(Paragraph("LISTA DE ENVIOS À SEDE", secao_style))
        
        # Preparar dados dos envios com header
        dados_envios = [['PROJETO/DESTINO', 'VALOR ENVIADO']]
        total_envio = 0
        
        # Mapeamento de nomes para exibição
        nomes_exibicao = {
            'oferta_voluntaria_conchas': 'Oferta Voluntária Conchas',
            'site': 'Site',
            'projeto_filipe': 'Projeto Filipe',
            'forca_para_viver': 'Força para Viver',
            'contador_sede': 'Contador Sede'
        }
        
        for chave, valor in envios.items():
            nome_exibir = nomes_exibicao.get(chave, chave.replace('_', ' ').title())
            dados_envios.append([nome_exibir, self._formatar_moeda(valor)])
            total_envio += valor
        
        # Adicionar valor do conselho (30% de Dízimos + Ofertas Alçadas)
        percentual_conselho = self.config.percentual_conselho if hasattr(self.config, 'percentual_conselho') else 30
        # Usar o valor já calculado corretamente nos totais
        valor_conselho = totais.get('valor_conselho', 0)
        dados_envios.append([f'Conselho ({percentual_conselho}% de Dízimos + Ofertas Alçadas)', self._formatar_moeda(valor_conselho)])
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
        total_dados = [['TOTAL ENVIADO PARA SEDE', self._formatar_moeda(total_envio)]]
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
        
    def _criar_secao_detalhamento_envios_sede(self, envios_detalhados):
        """Cria seção detalhada dos envios à sede"""
        elementos = []
        
        # Verificar se há envios detalhados
        tem_envios = any(envios_detalhados[chave] for chave in envios_detalhados)
        
        if not tem_envios:
            return elementos  # Retorna vazio se não houver envios
        
        secao_style = ParagraphStyle(
            'SecaoSede',
            parent=self.styles['cabecalho_secao'],
            fontSize=14,
            textColor=colors.HexColor('#6c757d'),  # Cinza
            alignment=TA_LEFT,
            spaceAfter=15,
            fontName='Helvetica-Bold'
        )
        
        elementos.append(Paragraph("DETALHAMENTO DOS ENVIOS", secao_style))
        
        # Mapeamento de nomes para exibição
        nomes_exibicao = {
            'oferta_voluntaria_conchas': 'Oferta Voluntária Conchas',
            'site': 'Site',
            'projeto_filipe': 'Projeto Filipe',
            'forca_para_viver': 'Força para Viver',
            'contador_sede': 'Contador Sede',
            'omn': 'Ofertas OMN'
        }
        
        for chave, detalhes in envios_detalhados.items():
            if detalhes:  # Se há lançamentos para esta categoria
                nome_categoria = nomes_exibicao.get(chave, chave.replace('_', ' ').title())
                
                # Subtítulo da categoria
                subtitulo_style = ParagraphStyle(
                    'SubtituloCategoria',
                    fontSize=12,
                    textColor=colors.HexColor('#4A7C59'),
                    alignment=TA_LEFT,
                    spaceAfter=8,
                    spaceBefore=5,
                    fontName='Helvetica-Bold'
                )
                
                elementos.append(Paragraph(nome_categoria, subtitulo_style))
                
                # Tabela de detalhes
                dados_detalhes = [['Data', 'Descrição', 'Conta', 'Valor']]
                
                for detalhe in detalhes:
                    data_formatada = detalhe['data'].strftime('%d/%m/%Y')
                    dados_detalhes.append([
                        data_formatada,
                        detalhe['descricao'][:40] + '...' if len(detalhe['descricao']) > 40 else detalhe['descricao'],
                        detalhe['conta'] or '-',
                        self._formatar_moeda(detalhe['valor'])
                    ])
                
                tabela_detalhes = Table(dados_detalhes, colWidths=[2.5*cm, 7*cm, 3*cm, 3.5*cm])
                tabela_detalhes.setStyle(TableStyle([
                    # Header
                    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#f8f9fa')),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 9),
                    ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
                    
                    # Dados
                    ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                    ('FONTSIZE', (0, 1), (-1, -1), 8),
                    ('ALIGN', (0, 1), (0, -1), 'CENTER'),  # Data
                    ('ALIGN', (1, 1), (1, -1), 'LEFT'),    # Descrição
                    ('ALIGN', (2, 1), (2, -1), 'CENTER'),  # Conta
                    ('ALIGN', (3, 1), (3, -1), 'RIGHT'),   # Valor
                    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                    ('TOPPADDING', (0, 0), (-1, -1), 4),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
                    ('LEFTPADDING', (0, 0), (-1, -1), 8),
                    ('RIGHTPADDING', (0, 0), (-1, -1), 8),
                    
                    # Bordas
                    ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                    
                    # Cores alternadas
                    ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8f9fa')]),
                ]))
                
                elementos.append(tabela_detalhes)
                elementos.append(Spacer(1, 10))
        
        if not any(envios_detalhados[chave] for chave in envios_detalhados):
            # Mensagem se não há envios
            texto_info = Paragraph(
                "Nenhum lançamento de envio foi encontrado para este período.",
                ParagraphStyle('InfoEnvios', fontSize=10, textColor=colors.grey, alignment=TA_CENTER)
            )
            elementos.append(texto_info)
        
        elementos.append(Spacer(1, 15))
        return elementos
    
    def _criar_secao_total_envio_sede(self, totais, envios):
        """Cria seção do total de envio para sede (conselho + projetos + despesas fixas)"""
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
        
        elementos.append(Paragraph("💰 TOTAL A SER ENVIADO PARA SEDE", secao_style))
        
        # Valor do conselho administrativo (30%)
        valor_conselho = totais['valor_conselho']
        
        # Buscar despesas fixas ativas do banco de dados
        try:
            from app.financeiro.despesas_fixas_model import DespesaFixaConselho
            despesas_fixas = DespesaFixaConselho.obter_despesas_ativas()
        except Exception as e:
            current_app.logger.warning(f'Erro ao buscar despesas fixas: {str(e)}')
            despesas_fixas = []
        
        # Organizar despesas fixas por nome
        despesas_dict = {
            'contador': 0.0,
            'site': 0.0,
            'forca_viver': 0.0,
            'conchas': 0.0,
            'outras': 0.0
        }
        
        for despesa in despesas_fixas:
            nome_lower = despesa.nome.lower()
            if 'contador' in nome_lower:
                despesas_dict['contador'] = despesa.valor_padrao
            elif 'site' in nome_lower:
                despesas_dict['site'] = despesa.valor_padrao
            elif 'força' in nome_lower or 'forca' in nome_lower or 'viver' in nome_lower:
                despesas_dict['forca_viver'] = despesa.valor_padrao
            elif 'conchas' in nome_lower or 'auxilio' in nome_lower or 'auxílio' in nome_lower:
                despesas_dict['conchas'] = despesa.valor_padrao
            else:
                despesas_dict['outras'] += despesa.valor_padrao
        
        # Preparar dados da tabela detalhada - SEMPRE MOSTRAR TODAS AS LINHAS
        dados_total_envio = [
            [f'💼 Administrativo ({int(self.config.percentual_conselho)}%)', self._formatar_moeda(valor_conselho)],
            ['📊 Contador', self._formatar_moeda(despesas_dict['contador'])],
            ['🌐 Site', self._formatar_moeda(despesas_dict['site'])],
            ['💪 Força para Viver', self._formatar_moeda(despesas_dict['forca_viver'])],
            ['🤝 Auxílio Conchas', self._formatar_moeda(despesas_dict['conchas'])],
        ]
        
        # Adicionar outras despesas fixas se houver
        if despesas_dict['outras'] > 0:
            dados_total_envio.append(['📋 Outras Despesas Fixas', self._formatar_moeda(despesas_dict['outras'])])
        
        # Calcular total geral
        total_despesas_fixas = sum(despesas_dict.values())
        total_geral_sede = valor_conselho + total_despesas_fixas
        
        # Tabela de composição detalhada
        tabela_composicao = Table(dados_total_envio, colWidths=[12*cm, 4*cm])
        tabela_composicao.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 11),
            ('ALIGN', (0, 0), (0, -1), 'LEFT'),
            ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('ROWBACKGROUNDS', (0, 0), (-1, -1), [colors.HexColor('#F0F8F0'), colors.HexColor('#FFFFFF')]),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('TEXTCOLOR', (1, 0), (1, -1), colors.HexColor('#2E86AB')),  # Azul do logo
        ]))
        
        elementos.append(tabela_composicao)
        elementos.append(Spacer(1, 10))
        
        # Total geral destacado
        total_geral_dados = [['✅ TOTAL A SER ENVIADO', self._formatar_moeda(total_geral_sede)]]
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
        
        # Observação explicativa
        obs_style = ParagraphStyle(
            'ObsEnvio',
            fontSize=9,
            textColor=colors.grey,
            alignment=TA_LEFT,
            spaceAfter=10,
            fontName='Helvetica'
        )
        
        observacao = f"""
        <i>Observação: Este valor representa o total mensal a ser enviado para a Sede, 
        incluindo o {int(self.config.percentual_conselho)}% administrativo e as despesas fixas cadastradas no sistema.
        Configure os valores em Financeiro > Gerenciar Despesas Fixas.</i>
        """
        
        elementos.append(Spacer(1, 5))
        elementos.append(Paragraph(observacao, obs_style))
        elementos.append(Spacer(1, 20))
        
        return elementos
    
    def _criar_assinaturas_sede(self):
        """Cria seções de assinaturas oficiais"""
        elementos = []
        
        elementos.append(Spacer(1, 40))
        
        # Campos de assinatura em tabela
        dados_assinatura = [
            ['_' * 40, '_' * 40],
            [self.config.presidente or 'Pastor não informado', self.config.primeiro_tesoureiro or 'Tesoureiro não informado'],
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
        
        # Data e local com timezone correto (Brasília UTC-3)
        from datetime import timezone, timedelta
        brasilia_tz = timezone(timedelta(hours=-3))
        data_atual = datetime.now(brasilia_tz)
        
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


def gerar_recibo_pdf(dados_recibo, config=None):
    """
    Gera PDF de recibo de doação profissional
    
    Args:
        dados_recibo (dict): Dicionário com os dados do recibo contendo:
            - nome_doador: Nome completo do doador
            - cpf_cnpj: CPF ou CNPJ do doador (opcional)
            - valor: Valor da doação (float)
            - forma_pagamento: Forma de pagamento utilizada
            - tipo_doacao: Tipo da doação (Oferta, Dízimo, etc)
            - data_doacao: Data da doação (date)
            - observacoes: Observações adicionais (opcional)
            - numero_recibo: Número do recibo
        config: Configuração do sistema (opcional)
    
    Returns:
        BytesIO: Buffer com o PDF gerado
    """
    if config is None:
        config = Configuracao.obter_configuracao()
    
    # Criar buffer
    buffer = BytesIO()
    
    # Configurar documento COM MARGENS REDUZIDAS para caber em 1 página
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=1.5*cm,
        leftMargin=1.5*cm,
        topMargin=1.5*cm,
        bottomMargin=1.5*cm
    )
    
    # Criar estilos
    styles = getSampleStyleSheet()
    
    cor_primaria = colors.HexColor(config.cor_principal)
    cor_secundaria = colors.HexColor(config.cor_secundaria)
    fonte_configurada = config.fonte_relatorio or 'Helvetica'
    
    style_titulo = ParagraphStyle(
        'TituloRecibo',
        parent=styles['Heading1'],
        fontSize=20,
        textColor=cor_primaria,
        alignment=TA_CENTER,
        fontName=f'{fonte_configurada}-Bold',
        spaceAfter=6,
        spaceBefore=6
    )
    
    style_subtitulo = ParagraphStyle(
        'SubtituloRecibo',
        parent=styles['Normal'],
        fontSize=14,
        textColor=cor_secundaria,
        alignment=TA_CENTER,
        fontName=fonte_configurada,
        spaceAfter=5
    )
    
    style_numero = ParagraphStyle(
        'NumeroRecibo',
        parent=styles['Normal'],
        fontSize=12,
        textColor=colors.black,
        alignment=TA_RIGHT,
        fontName=f'{fonte_configurada}-Bold'
    )
    
    style_corpo = ParagraphStyle(
        'CorpoRecibo',
        parent=styles['Normal'],
        fontSize=11,
        textColor=colors.black,
        alignment=TA_JUSTIFY,
        fontName=fonte_configurada,
        leading=18
    )
    
    style_destaque = ParagraphStyle(
        'DestaqueRecibo',
        parent=styles['Normal'],
        fontSize=12,
        textColor=cor_primaria,
        alignment=TA_CENTER,
        fontName=f'{fonte_configurada}-Bold',
        spaceBefore=6,
        spaceAfter=6
    )
    
    style_info = ParagraphStyle(
        'InfoRecibo',
        parent=styles['Normal'],
        fontSize=10,
        textColor=colors.black,
        alignment=TA_LEFT,
        fontName=fonte_configurada,
        leading=14
    )
    
    style_rodape = ParagraphStyle(
        'RodapeRecibo',
        parent=styles['Normal'],
        fontSize=8,
        textColor=colors.grey,
        alignment=TA_CENTER,
        fontName=fonte_configurada
    )
    
    # Elementos do documento
    elementos = []
    
    # Logo (se existir)
    try:
        if config.logo and os.path.exists(config.logo):
            logo_path = config.logo
        else:
            logo_path = os.path.join(current_app.static_folder, 'Logo_OBPC.jpg')
        
        if os.path.exists(logo_path):
            logo = Image(logo_path, width=60, height=60)
            logo.hAlign = 'CENTER'
            elementos.append(logo)
            elementos.append(Spacer(1, 6))
    except:
        pass
    
    # Nome da Igreja
    nome_igreja = config.nome_igreja or "IGREJA EVANG PENTECOSTAL O BRASIL PARA CRISTO DE TIETÊ"
    elementos.append(Paragraph(nome_igreja, style_subtitulo))
    
    # Endereço
    if config.endereco:
        elementos.append(Paragraph(config.endereco, style_rodape))
    
    cidade = config.cidade or "Tietê"
    elementos.append(Paragraph(f"{cidade} - SP", style_rodape))
    
    if config.cnpj:
        elementos.append(Paragraph(f"CNPJ: {config.cnpj}", style_rodape))
    
    elementos.append(Spacer(1, 8))
    
    # Linha separadora
    elementos.append(HRFlowable(width="100%", thickness=2, color=cor_primaria))
    elementos.append(Spacer(1, 8))
    
    # Título
    elementos.append(Paragraph("RECIBO DE PAGAMENTO", style_titulo))
    elementos.append(Spacer(1, 10))
    
    # Número e Data do recibo
    numero_recibo = dados_recibo.get('numero_recibo', 'S/N')
    data_doacao = dados_recibo.get('data_doacao')
    if isinstance(data_doacao, str):
        data_formatada = datetime.strptime(data_doacao, '%Y-%m-%d').strftime('%d/%m/%Y')
    else:
        data_formatada = data_doacao.strftime('%d/%m/%Y')
    
    info_recibo = f"""
    <b>RECIBO Nº:</b> {numero_recibo}<br/>
    <b>DATA:</b> {data_formatada}
    """
    elementos.append(Paragraph(info_recibo, style_corpo))
    elementos.append(Spacer(1, 10))
    
    # Recebi de (Igreja)
    cnpj_igreja = config.cnpj if config.cnpj else "50.780.642/0031-44"
    texto_recebi = f"""
    <b>Recebi de:</b> {nome_igreja}<br/>
    <b>CPF/CNPJ:</b> {cnpj_igreja}
    """
    elementos.append(Paragraph(texto_recebi, style_corpo))
    elementos.append(Spacer(1, 10))
    
    # Valor
    valor = float(dados_recibo['valor'])
    valor_formatado = f"R$ {valor:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
    valor_extenso = converter_valor_extenso(valor)
    
    texto_valor = f"""
    <b>A importância de:</b><br/>
    <font size="13"><b>{valor_formatado}</b></font><br/>
    <b>Valor por extenso:</b> {valor_extenso.capitalize()}
    """
    elementos.append(Paragraph(texto_valor, style_corpo))
    elementos.append(Spacer(1, 10))
    
    # Referente a
    tipo_doacao = dados_recibo.get('tipo_doacao', 'Pagamento')
    texto_referente = f"""
    <b>Referente a:</b> {tipo_doacao}
    """
    elementos.append(Paragraph(texto_referente, style_corpo))
    elementos.append(Spacer(1, 10))
    
    # Forma de pagamento
    forma_pag = dados_recibo.get('forma_pagamento', 'Dinheiro')
    texto_forma_pagamento = f"""
    <b>Forma de pagamento:</b> {forma_pag}
    """
    elementos.append(Paragraph(texto_forma_pagamento, style_corpo))
    elementos.append(Spacer(1, 12))
    
    # Dados do Recebedor
    elementos.append(Paragraph("<b>DADOS DO RECEBEDOR</b>", style_destaque))
    elementos.append(Spacer(1, 6))
    
    nome_recebedor = dados_recibo.get('nome_doador', '')
    cpf_recebedor = dados_recibo.get('cpf_cnpj', '')
    
    texto_recebedor = f"""
    <b>Nome/Razão Social:</b> {nome_recebedor}<br/>
    <b>CPF/CNPJ:</b> {cpf_recebedor}
    """
    elementos.append(Paragraph(texto_recebedor, style_corpo))
    elementos.append(Spacer(1, 8))
    
    # Declaração
    declaracao = "Declaro para os devidos fins que recebi o valor acima descrito."
    elementos.append(Paragraph(declaracao, style_corpo))
    elementos.append(Spacer(1, 25))
    
    # Observações (se houver)
    if dados_recibo.get('observacoes'):
        elementos.append(Paragraph("<b>Observações:</b>", style_info))
        elementos.append(Paragraph(dados_recibo['observacoes'], style_info))
        elementos.append(Spacer(1, 10))
    
    # Linha de assinatura
    elementos.append(Spacer(1, 15))
    elementos.append(HRFlowable(width="60%", thickness=1, color=colors.black, hAlign='CENTER'))
    elementos.append(Spacer(1, 3))
    assinatura_texto = f"<b>Assinatura do Recebedor</b><br/>{nome_recebedor}"
    elementos.append(Paragraph(assinatura_texto, ParagraphStyle(
        'AssinaturaRecebedor',
        parent=style_corpo,
        alignment=TA_CENTER,
        fontSize=9
    )))
    elementos.append(Spacer(1, 15))
    
    # Local e data
    data_recibo = dados_recibo.get('data_doacao')
    if isinstance(data_recibo, str):
        data_recibo = datetime.strptime(data_recibo, '%Y-%m-%d').date()
    
    meses = [
        '', 'janeiro', 'fevereiro', 'março', 'abril', 'maio', 'junho',
        'julho', 'agosto', 'setembro', 'outubro', 'novembro', 'dezembro'
    ]
    
    cidade = config.cidade or "Tietê"
    data_extenso = f"{cidade}, {data_recibo.day} de {meses[data_recibo.month]} de {data_recibo.year}."
    elementos.append(Paragraph(data_extenso, style_corpo))
    elementos.append(Spacer(1, 12))
    
    # Rodapé
    elementos.append(HRFlowable(width="100%", thickness=0.5, color=colors.grey))
    elementos.append(Spacer(1, 5))
    
    # Data/hora de emissão em horário de Brasília (UTC-3)
    try:
        import pytz
        fuso_brasilia = pytz.timezone('America/Sao_Paulo')
        agora = datetime.now(fuso_brasilia)
    except:
        # Fallback: ajustar manualmente UTC-3
        agora = datetime.utcnow() - timedelta(hours=3)
    
    data_emissao = agora.strftime('%d/%m/%Y')
    hora_emissao = agora.strftime('%H:%M')
    
    texto_rodape = f"""
    Este recibo é válido como comprovante de pagamento.<br/>
    Emitido em {data_emissao} às {hora_emissao} - Sistema Administrativo OBPC
    """
    elementos.append(Paragraph(texto_rodape, style_rodape))
    
    # Construir PDF
    doc.build(elementos)
    
    # Retornar buffer
    buffer.seek(0)
    return buffer


def converter_valor_extenso(valor):
    """
    Converte valor numérico para extenso em português
    Simplificado para valores até 999.999,99
    """
    unidades = ['', 'um', 'dois', 'três', 'quatro', 'cinco', 'seis', 'sete', 'oito', 'nove']
    dezenas = ['', '', 'vinte', 'trinta', 'quarenta', 'cinquenta', 'sessenta', 'setenta', 'oitenta', 'noventa']
    especiais = ['dez', 'onze', 'doze', 'treze', 'quatorze', 'quinze', 'dezesseis', 'dezessete', 'dezoito', 'dezenove']
    centenas = ['', 'cento', 'duzentos', 'trezentos', 'quatrocentos', 'quinhentos', 'seiscentos', 'setecentos', 'oitocentos', 'novecentos']
    
    def converter_grupo(num):
        if num == 0:
            return ''
        elif num < 10:
            return unidades[num]
        elif num < 20:
            return especiais[num - 10]
        elif num < 100:
            d = num // 10
            u = num % 10
            if u == 0:
                return dezenas[d]
            return dezenas[d] + ' e ' + unidades[u]
        else:
            c = num // 100
            resto = num % 100
            if resto == 0:
                return 'cem' if num == 100 else centenas[c]
            return centenas[c] + ' e ' + converter_grupo(resto)
    
    # Separar reais e centavos
    reais = int(valor)
    centavos = int(round((valor - reais) * 100))
    
    # Converter reais
    if reais == 0:
        texto_reais = 'zero reais'
    elif reais == 1:
        texto_reais = 'um real'
    elif reais < 1000:
        texto_reais = converter_grupo(reais) + ' reais'
    else:
        milhar = reais // 1000
        resto = reais % 1000
        texto_milhar = converter_grupo(milhar) + (' mil' if milhar > 0 else '')
        if resto > 0:
            texto_reais = texto_milhar + ' e ' + converter_grupo(resto) + ' reais'
        else:
            texto_reais = texto_milhar + ' reais'
    
    # Converter centavos
    if centavos == 0:
        return texto_reais
    elif centavos == 1:
        texto_centavos = 'um centavo'
    else:
        texto_centavos = converter_grupo(centavos) + ' centavos'
    
    return texto_reais + ' e ' + texto_centavos