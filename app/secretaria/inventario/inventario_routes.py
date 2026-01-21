from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app, make_response, send_file
from flask_login import login_required
from app.extensoes import db
from .inventario_model import ItemInventario
from datetime import datetime
import os

# Importação condicional do weasyprint
try:
    import weasyprint
    WEASYPRINT_AVAILABLE = True
except ImportError:
    WEASYPRINT_AVAILABLE = False
    print("WeasyPrint não disponível. Funcionalidade de PDF será limitada.")

# Importar ReportLab para fallback de PDF
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm, mm
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT
from io import BytesIO

inventario_bp = Blueprint('inventario', __name__, template_folder='templates')

@inventario_bp.route('/inventario-teste')
@login_required
def lista_itens_teste():
    """ROTA DE TESTE - Lista itens do inventário"""
    print("🔥🔥🔥 ROTA TESTE CHAMADA! 🔥🔥🔥")
    
    # Query direta sem filtros
    itens = ItemInventario.query.filter_by(ativo=True).order_by(ItemInventario.codigo.asc()).all()
    print(f"📊 ENCONTRADOS: {len(itens)} itens")
    
    categorias = ['Móveis', 'Eletrônicos', 'Instrumentos']
    estados = ['Novo', 'Bom', 'Regular']
    
    return render_template('inventario/lista_itens.html', 
                         itens=itens, 
                         categorias=categorias,
                         estados=estados,
                         busca="",
                         categoria_selecionada="",
                         estado_selecionado="",
                         ativo_selecionado="",
                         valor_total=0)

@inventario_bp.route('/secretaria/inventario/lista')
@login_required
def lista_itens():
    """Lista todos os itens do inventário"""
    print("DEBUG ROTA: Iniciando lista_itens()")
    try:
        # Filtros
        busca = request.args.get('busca', '').strip()
        categoria = request.args.get('categoria', '').strip()
        estado = request.args.get('estado', '').strip()
        ativo = request.args.get('ativo', '').strip()
        
        print(f"DEBUG ROTA: Parâmetros: busca='{busca}', categoria='{categoria}', estado='{estado}', ativo='{ativo}'")
        
        # Query base
        query = ItemInventario.query
        print(f"DEBUG ROTA: Query base criada")
        
        # Aplicar filtros
        if busca:
            query = query.filter(
                (ItemInventario.nome.ilike(f'%{busca}%')) |
                (ItemInventario.codigo.ilike(f'%{busca}%')) |
                (ItemInventario.descricao.ilike(f'%{busca}%')) |
                (ItemInventario.responsavel.ilike(f'%{busca}%'))
            )
            print(f"DEBUG ROTA: Filtro de busca aplicado")
        
        if categoria and categoria != 'Todas':
            query = query.filter(ItemInventario.categoria == categoria)
        
        if estado and estado != 'Todos':
            query = query.filter(ItemInventario.estado_conservacao == estado)
        
        if ativo == 'true':
            query = query.filter(ItemInventario.ativo == True)
        elif ativo == 'false':
            query = query.filter(ItemInventario.ativo == False)
        else:
            # Por padrão, mostrar apenas itens ativos
            query = query.filter(ItemInventario.ativo == True)
        
        # Ordenação
        itens = query.order_by(ItemInventario.codigo.asc()).all()
        
        # Calcular valor total
        valor_total = 0
        for item in itens:
            if item.valor_aquisicao:
                valor_total += float(item.valor_aquisicao)
        
        # Categorias padrão
        categorias_padrao = [
            'Móveis e Utensílios',
            'Equipamentos Eletrônicos',
            'Instrumentos Musicais',
            'Equipamentos de Som',
            'Equipamentos de Iluminação',
            'Livros e Material Didático',
            'Veículos',
            'Imóveis',
            'Outros'
        ]
        
        # Obter todas as categorias para o filtro
        categorias_banco = db.session.query(ItemInventario.categoria).distinct().all()
        categorias_banco = [cat[0] for cat in categorias_banco if cat[0]]
        
        # Combinar categorias (banco + padrão), removendo duplicatas e ordenando
        categorias = sorted(list(set(categorias_padrao + categorias_banco)))
        
        # Estados de conservação
        estados = ['Novo', 'Bom', 'Regular', 'Ruim', 'Péssimo']
        
        # DEBUG: Log para verificar se dados estão chegando aqui
        print(f"DEBUG ROTA: {len(itens)} itens encontrados, valor total: R$ {valor_total}")
        if len(itens) > 0:
            print(f"   Primeiros 3 itens: {[f'{i.codigo}: {i.nome}' for i in itens[:3]]}")
        else:
            print(f"   AVISO: LISTA VAZIA! Verificando banco...")
            total_banco = ItemInventario.query.count()
            ativos_banco = ItemInventario.query.filter_by(ativo=True).count()
            print(f"   Total no banco: {total_banco}, Ativos: {ativos_banco}")
        
        return render_template('inventario/lista_itens.html', 
                             itens=itens, 
                             categorias=categorias,
                             estados=estados,
                             busca=busca,
                             categoria_selecionada=categoria,
                             estado_selecionado=estado,
                             ativo_selecionado=ativo,
                             valor_total=valor_total)
    except Exception as e:
        print(f"DEBUG ROTA: ERRO CAPTURADO - {str(e)}")
        import traceback
        traceback.print_exc()
        flash(f'Erro ao carregar inventário: {str(e)}', 'danger')
        return render_template('inventario/lista_itens.html', itens=[], valor_total=0)

@inventario_bp.route('/secretaria/inventario/novo')
@login_required  
def novo_item():
    """Página para cadastrar novo item"""
    from .inventario_model import ItemInventario
    from app.extensoes import db
    
    # Categorias padrão
    categorias_padrao = [
        'Móveis e Utensílios',
        'Equipamentos Eletrônicos',
        'Instrumentos Musicais',
        'Equipamentos de Som',
        'Equipamentos de Iluminação',
        'Livros e Material Didático',
        'Veículos',
        'Imóveis',
        'Outros'
    ]
    
    # Buscar categorias distintas do banco
    categorias_banco = db.session.query(ItemInventario.categoria).distinct().all()
    categorias_banco = [cat[0] for cat in categorias_banco if cat[0]]
    
    # Combinar categorias (banco + padrão), removendo duplicatas e ordenando
    categorias = sorted(list(set(categorias_padrao + categorias_banco)))
    
    # Estados de conservação
    estados = ['Novo', 'Bom', 'Regular', 'Ruim', 'Péssimo']
    # Gerar próximo código automático
    ultimo_item = ItemInventario.query.order_by(ItemInventario.id.desc()).first()
    if ultimo_item and ultimo_item.codigo:
        # Extrai prefixo e número
        import re
        match = re.match(r"([A-Z]+)(\d+)", ultimo_item.codigo)
        if match:
            prefixo = match.group(1)
            numero = int(match.group(2)) + 1
            proximo_codigo = f"{prefixo}{numero:03d}"
        else:
            proximo_codigo = "ITM001"
    else:
        proximo_codigo = "ITM001"
    return render_template('inventario/cadastro_item.html', categorias=categorias, estados=estados, proximo_codigo=proximo_codigo)

@inventario_bp.route('/secretaria/inventario/cadastrar', methods=['POST'])
@login_required
def cadastrar_item():
    """Cadastra um novo item no inventário"""
    try:
        # Dados do formulário
        codigo = request.form.get('codigo')
        nome = request.form.get('nome')
        categoria = request.form.get('categoria')
        descricao = request.form.get('descricao')
        valor_aquisicao = request.form.get('valor_aquisicao')
        data_aquisicao = request.form.get('data_aquisicao')
        estado_conservacao = request.form.get('estado_conservacao')
        localizacao = request.form.get('localizacao')
        responsavel = request.form.get('responsavel')
        observacoes = request.form.get('observacoes')
        ativo = request.form.get('ativo') == 'on'
        
        # Validações básicas
        if not codigo or not nome or not categoria:
            flash('Código, nome e categoria são obrigatórios!', 'danger')
            return redirect(url_for('inventario.novo_item'))
        
        # Verificar se código já existe
        item_existente = ItemInventario.query.filter_by(codigo=codigo).first()
        if item_existente:
            flash('Código já está em uso! Use um código único.', 'danger')
            return redirect(url_for('inventario.novo_item'))
        
        # Converter valor para decimal se fornecido
        valor_decimal = None
        if valor_aquisicao:
            try:
                valor_decimal = float(valor_aquisicao.replace(',', '.'))
            except ValueError:
                flash('Valor de aquisição inválido!', 'danger')
                return redirect(url_for('inventario.novo_item'))
        
        # Converter data se fornecida
        data_obj = None
        if data_aquisicao:
            try:
                data_obj = datetime.strptime(data_aquisicao, '%Y-%m-%d').date()
            except ValueError:
                flash('Data de aquisição inválida!', 'danger')
                return redirect(url_for('inventario.novo_item'))
        
        # Criar novo item
        item = ItemInventario(
            codigo=codigo,
            nome=nome,
            categoria=categoria,
            descricao=descricao,
            valor_aquisicao=valor_decimal,
            data_aquisicao=data_obj,
            estado_conservacao=estado_conservacao,
            localizacao=localizacao,
            responsavel=responsavel,
            observacoes=observacoes,
            ativo=ativo
        )
        
        db.session.add(item)
        flash('Item cadastrado com sucesso!', 'success')
        
        db.session.commit()
        return redirect(url_for('inventario.lista_itens'))
        
    except Exception as e:
        import traceback
        db.session.rollback()
        flash(f'Erro ao cadastrar item: {str(e)}', 'danger')
        flash(traceback.format_exc(), 'warning')
        return redirect(url_for('inventario.novo_item'))

def gerar_pdf_inventario_reportlab(itens, inventario_por_categoria, valor_total, config):
    """Gera PDF do inventário usando ReportLab como alternativa ao WeasyPrint"""
    try:
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=2*cm, leftMargin=2*cm, topMargin=2*cm, bottomMargin=2*cm)
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle('CustomTitle', parent=styles['Heading1'], fontSize=16, spaceAfter=20, alignment=TA_CENTER, textColor=colors.darkblue)
        subtitle_style = ParagraphStyle('CustomSubtitle', parent=styles['Heading2'], fontSize=12, spaceAfter=15, alignment=TA_CENTER)
        content_style = ParagraphStyle('CustomContent', parent=styles['Normal'], fontSize=11, spaceAfter=12, alignment=TA_JUSTIFY, leftIndent=10, rightIndent=10)
        story = []

        # Logo da igreja (usando configurações do sistema)
        if config and config.logo and config.exibir_logo_relatorio:
            try:
                # Caminho do logo configurado pelo usuário
                logo_path = os.path.join(current_app.root_path, '..', config.logo)
                if os.path.exists(logo_path):
                    logo = Image(logo_path, width=150, height=150)
                    logo.hAlign = 'CENTER'
                    story.append(logo)
                    story.append(Spacer(1, 10))
                else:
                    current_app.logger.warning(f'Logo configurado não encontrado: {logo_path}')
            except Exception as e:
                current_app.logger.warning(f'Erro ao carregar logo configurado: {str(e)}')
        else:
            # Fallback para logos padrão
            try:
                fallback_logos = ['logo_obpc_novo.jpg', 'Logo_OBPC.jpg']
                for fallback_logo in fallback_logos:
                    try:
                        logo_path = os.path.join(current_app.static_folder, fallback_logo)
                        if os.path.exists(logo_path):
                            logo = Image(logo_path, width=150, height=150)
                            logo.hAlign = 'CENTER'
                            story.append(logo)
                            story.append(Spacer(1, 10))
                            break
                    except Exception as e:
                        continue
            except Exception:
                pass

        # Cabeçalho da igreja
        story.append(Paragraph(config.nome_igreja, title_style))
        story.append(Paragraph(f"{config.endereco}, {config.cidade}", subtitle_style))
        story.append(Paragraph(f"CNPJ: {config.cnpj} | Tel: {config.telefone}", subtitle_style))
        story.append(Spacer(1, 20))

        # Título do relatório
        story.append(Paragraph("INVENTÁRIO PATRIMONIAL", title_style))
        story.append(Spacer(1, 15))

        # Data de geração
        story.append(Paragraph(f"Gerado em {datetime.now().strftime('%d/%m/%Y às %H:%M')}", subtitle_style))
        story.append(Spacer(1, 15))

        # Valor total e total de itens
        story.append(Paragraph(f"<b>Total de Itens:</b> {len(itens)}", content_style))
        story.append(Paragraph(f"<b>Valor Total:</b> R$ {valor_total:,.2f}", content_style))
        story.append(Spacer(1, 20))

        # Tabela por categoria
        for categoria, itens_cat in inventario_por_categoria.items():
            # Título da categoria
            story.append(Paragraph(f"<b>Categoria: {categoria}</b>", subtitle_style))
            story.append(Spacer(1, 10))
            
            # Cabeçalho da tabela
            data = [["Código", "Nome", "Descrição", "Valor Aquisição", "Estado", "Responsável"]]
            
            # Estilo para texto das células
            cell_style = ParagraphStyle('CellText', parent=styles['Normal'], fontSize=8, leading=10)
            
            # Dados dos itens
            for item in itens_cat:
                # Usar Paragraph para permitir quebra de linha automática
                codigo_p = Paragraph(item.codigo or '-', cell_style)
                nome_p = Paragraph(item.nome or '-', cell_style)
                descricao_p = Paragraph(item.descricao or '-', cell_style)
                valor_p = Paragraph(f"R$ {item.valor_aquisicao:,.2f}" if item.valor_aquisicao else "-", cell_style)
                estado_p = Paragraph(item.estado_conservacao or '-', cell_style)
                responsavel_p = Paragraph(item.responsavel or '-', cell_style)
                
                data.append([
                    codigo_p,
                    nome_p,
                    descricao_p,
                    valor_p,
                    estado_p,
                    responsavel_p
                ])
            
            # Criar tabela com larguras melhor distribuídas para A4 (total: ~17cm)
            table = Table(data, colWidths=[1.5*cm, 4.0*cm, 5.0*cm, 2.5*cm, 2.0*cm, 2.0*cm])
            table.setStyle(TableStyle([
                # Cabeçalho
                ('BACKGROUND', (0, 0), (-1, 0), colors.lightblue),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.darkblue),
                ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 9),
                
                # Dados - alinhamentos específicos
                ('ALIGN', (0, 1), (0, -1), 'CENTER'),  # Código centralizado
                ('ALIGN', (1, 1), (1, -1), 'LEFT'),    # Nome à esquerda
                ('ALIGN', (2, 1), (2, -1), 'LEFT'),    # Descrição à esquerda
                ('ALIGN', (3, 1), (3, -1), 'RIGHT'),   # Valor à direita
                ('ALIGN', (4, 1), (4, -1), 'CENTER'),  # Estado centralizado
                ('ALIGN', (5, 1), (5, -1), 'LEFT'),    # Responsável à esquerda
                
                # Bordas e grid
                ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
                ('LINEABOVE', (0, 0), (-1, 0), 1, colors.darkblue),
                ('LINEBELOW', (0, 0), (-1, 0), 1, colors.darkblue),
                
                # Espaçamento vertical e quebra de linha
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.lightgrey]),
                
                # Padding para acomodar quebras de linha
                ('LEFTPADDING', (0, 0), (-1, -1), 6),
                ('RIGHTPADDING', (0, 0), (-1, -1), 6),
                ('TOPPADDING', (0, 0), (-1, -1), 8),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
                
                # Permitir altura dinâmica das linhas para quebra de texto
                ('SPLITBYROW', (0, 0), (-1, -1), True),
            ]))
            
            story.append(table)
            story.append(Spacer(1, 15))

        # Rodapé
        story.append(Paragraph(f"Relatório gerado automaticamente pelo Sistema OBPC", ParagraphStyle('Footer', parent=styles['Normal'], fontSize=8, alignment=TA_CENTER, textColor=colors.grey)))

        doc.build(story)
        pdf_data = buffer.getvalue()
        buffer.close()

        filename = f"inventario_patrimonial_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        filepath = os.path.join('app', 'static', 'inventario', filename)
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        with open(filepath, 'wb') as f:
            f.write(pdf_data)

        response = make_response(pdf_data)
        response.headers['Content-Type'] = 'application/pdf'
        response.headers['Content-Disposition'] = f'inline; filename="{filename}"'
        return response
    except Exception as e:
        raise Exception(f"Erro na geração com ReportLab: {str(e)}")

@inventario_bp.route('/secretaria/inventario/pdf')
@login_required
def gerar_pdf_inventario():
    """Gera PDF do inventário completo"""
    try:
        # Buscar apenas itens ativos
        itens = ItemInventario.query.filter_by(ativo=True).order_by(
            ItemInventario.categoria.asc(), 
            ItemInventario.codigo.asc()
        ).all()
        
        # Agrupar por categoria
        inventario_por_categoria = {}
        valor_total = 0
        
        for item in itens:
            if item.categoria not in inventario_por_categoria:
                inventario_por_categoria[item.categoria] = []
            inventario_por_categoria[item.categoria].append(item)
            if item.valor_aquisicao:
                valor_total += float(item.valor_aquisicao)
        
        # Obter configurações da igreja
        from app.configuracoes.configuracoes_model import Configuracao
        config = Configuracao.obter_configuracao()
        
        # Verifica se WeasyPrint está disponível
        if WEASYPRINT_AVAILABLE:
            # Renderizar template HTML
            html_content = render_template('inventario/pdf_inventario.html', 
                                         inventario_por_categoria=inventario_por_categoria,
                                         valor_total=valor_total,
                                         total_itens=len(itens),
                                         config=config,
                                         data_geracao=datetime.now().strftime('%d/%m/%Y às %H:%M'),
                                         base_url=request.url_root)
            
            # Configura o WeasyPrint
            base_url = request.url_root
            
            # Gerar PDF
            pdf = weasyprint.HTML(string=html_content, base_url=base_url).write_pdf()
            
            # Define nome do arquivo
            filename = f"inventario_patrimonial_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
            filepath = os.path.join('app', 'static', 'inventario', filename)
            
            # Salva o arquivo
            os.makedirs(os.path.dirname(filepath), exist_ok=True)
            with open(filepath, 'wb') as f:
                f.write(pdf)
            
            # Retorna o PDF para download
            response = make_response(pdf)
            response.headers['Content-Type'] = 'application/pdf'
            response.headers['Content-Disposition'] = f'inline; filename="{filename}"'
            
            return response
        else:
            # Usar ReportLab como alternativa
            return gerar_pdf_inventario_reportlab(itens, inventario_por_categoria, valor_total, config)
        
    except Exception as e:
        # Se WeasyPrint falhar, tentar ReportLab
        if WEASYPRINT_AVAILABLE:
            try:
                return gerar_pdf_inventario_reportlab(itens, inventario_por_categoria, valor_total, config)
            except Exception as e2:
                flash(f'Erro ao gerar PDF com ReportLab: {str(e2)}', 'danger')
        
        flash(f'Erro ao gerar PDF: {str(e)}', 'danger')
        return redirect(url_for('inventario.lista_itens'))

# =================== CRUD COMPLETO ===================

@inventario_bp.route('/secretaria/inventario/visualizar/<int:id>')
@login_required
def visualizar_item(id):
    """Visualiza detalhes de um item"""
    item = ItemInventario.query.get_or_404(id)
    return render_template('inventario/visualizar_item.html', item=item)

@inventario_bp.route('/secretaria/inventario/editar/<int:id>')
@login_required
def editar_item(id):
    """Formulário para editar um item"""
    item = ItemInventario.query.get_or_404(id)
    
    # Categorias padrão
    categorias_padrao = [
        'Móveis e Utensílios',
        'Equipamentos Eletrônicos',
        'Instrumentos Musicais',
        'Equipamentos de Som',
        'Equipamentos de Iluminação',
        'Livros e Material Didático',
        'Veículos',
        'Imóveis',
        'Outros'
    ]
    
    # Buscar categorias distintas do banco
    categorias_banco = db.session.query(ItemInventario.categoria).distinct().all()
    categorias_banco = [cat[0] for cat in categorias_banco if cat[0]]
    
    # Combinar categorias (banco + padrão), removendo duplicatas e ordenando
    categorias = sorted(list(set(categorias_padrao + categorias_banco)))
    
    estados = ['Novo', 'Bom', 'Regular', 'Ruim', 'Péssimo']
    return render_template('inventario/editar_item.html', item=item, categorias=categorias, estados=estados)

@inventario_bp.route('/secretaria/inventario/atualizar/<int:id>', methods=['POST'])
@login_required
def atualizar_item(id):
    """Atualiza um item existente"""
    try:
        item = ItemInventario.query.get_or_404(id)
        
        item.codigo = request.form.get('codigo')
        item.nome = request.form.get('nome')
        item.categoria = request.form.get('categoria')
        item.descricao = request.form.get('descricao')
        item.valor_aquisicao = request.form.get('valor_aquisicao')
        item.data_aquisicao = datetime.strptime(request.form.get('data_aquisicao'), '%Y-%m-%d').date() if request.form.get('data_aquisicao') else None
        item.estado_conservacao = request.form.get('estado_conservacao')
        item.localizacao = request.form.get('localizacao')
        item.responsavel = request.form.get('responsavel')
        item.observacoes = request.form.get('observacoes')
        item.atualizado_em = datetime.utcnow()
        
        db.session.commit()
        flash('Item atualizado com sucesso!', 'success')
        return redirect(url_for('inventario.lista_itens'))
        
    except Exception as e:
        db.session.rollback()
        flash(f'Erro ao atualizar item: {str(e)}', 'danger')
        return redirect(url_for('inventario.editar_item', id=id))

@inventario_bp.route('/secretaria/inventario/excluir/<int:id>', methods=['POST'])
@login_required
def excluir_item(id):
    """Exclui um item permanentemente"""
    try:
        item = ItemInventario.query.get_or_404(id)
        nome_item = item.nome
        
        db.session.delete(item)
        db.session.commit()
        
        flash(f'Item "{nome_item}" excluído permanentemente!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Erro ao excluir item: {str(e)}', 'danger')
    
    return redirect(url_for('inventario.lista_itens'))

@inventario_bp.route('/secretaria/inventario/inativar/<int:id>', methods=['POST'])
@login_required
def inativar_item(id):
    """Inativa/ativa um item"""
    try:
        item = ItemInventario.query.get_or_404(id)
        item.ativo = not item.ativo
        item.atualizado_em = datetime.utcnow()
        db.session.commit()
        
        status = 'ativado' if item.ativo else 'inativado'
        flash(f'Item {status} com sucesso!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Erro ao alterar status: {str(e)}', 'danger')
    
    return redirect(url_for('inventario.lista_itens'))


@inventario_bp.route('/secretaria/inventario/pdf/<int:id>')
@login_required
def gerar_pdf_item(id):
    """Gera PDF para um único item do inventário"""
    try:
        item = ItemInventario.query.get_or_404(id)

        # Obter configurações da igreja
        from app.configuracoes.configuracoes_model import Configuracao
        config = Configuracao.obter_configuracao()
        
        if not config:
            flash('Erro: Configurações do sistema não encontradas.', 'danger')
            return redirect(url_for('inventario.lista_itens'))

        # Tentar renderizar template HTML para o item
        try:
            html_content = render_template('inventario/pdf_item.html', 
                                         item=item, 
                                         config=config, 
                                         data_geracao=datetime.now().strftime('%d/%m/%Y às %H:%M'), 
                                         base_url=request.url_root)
            
            if WEASYPRINT_AVAILABLE:
                try:
                    pdf = weasyprint.HTML(string=html_content, base_url=request.url_root).write_pdf()
                    filename = f"inventario_item_{item.codigo}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
                    response = make_response(pdf)
                    response.headers['Content-Type'] = 'application/pdf'
                    response.headers['Content-Disposition'] = f'inline; filename="{filename}"'
                    return response
                except Exception as weasy_error:
                    print(f"Erro WeasyPrint: {weasy_error}")
                    # Continua para fallback ReportLab
        except Exception as template_error:
            print(f"Erro template: {template_error}")
            # Continua para fallback ReportLab
        
        # Fallback: gerar PDF com ReportLab
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=2*cm, leftMargin=2*cm, topMargin=2*cm, bottomMargin=2*cm)
        styles = getSampleStyleSheet()
        story = []
        story.append(Paragraph(config.nome_igreja, styles['Title']))
        story.append(Spacer(1, 12))
        story.append(Paragraph(f"Código: {item.codigo}", styles['Normal']))
        story.append(Paragraph(f"Nome: {item.nome}", styles['Normal']))
        story.append(Paragraph(f"Categoria: {item.categoria or '-'}", styles['Normal']))
        story.append(Paragraph(f"Valor: R$ {item.valor_aquisicao:.2f}" if item.valor_aquisicao else "Valor: -", styles['Normal']))
        story.append(Paragraph(f"Estado: {item.estado_conservacao or '-'}", styles['Normal']))
        story.append(Paragraph(f"Local: {item.localizacao or '-'}", styles['Normal']))
        story.append(Paragraph(f"Responsável: {item.responsavel or '-'}", styles['Normal']))
        doc.build(story)
        pdf_data = buffer.getvalue()
        buffer.close()
        response = make_response(pdf_data)
        response.headers['Content-Type'] = 'application/pdf'
        response.headers['Content-Disposition'] = f'inline; filename="inventario_item_{item.codigo}.pdf"'
        return response
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        print(f"ERRO ao gerar PDF do item {id}:")
        print(error_trace)
        flash(f'Erro ao gerar PDF do item: {str(e)}', 'danger')
        return redirect(url_for('inventario.lista_itens'))


@inventario_bp.route('/secretaria/inventario/atualizar-estado/<int:id>', methods=['POST'])
@login_required
def atualizar_estado(id):
    """Atualiza o estado de conservação do item"""
    try:
        item = ItemInventario.query.get_or_404(id)
        novo_estado = request.form.get('estado')
        if not novo_estado:
            flash('Estado inválido!', 'danger')
            return redirect(url_for('inventario.lista_itens'))

        item.estado_conservacao = novo_estado
        item.atualizado_em = datetime.utcnow()
        db.session.commit()
        flash('Estado atualizado com sucesso!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Erro ao atualizar estado: {str(e)}', 'danger')

    return redirect(url_for('inventario.lista_itens'))