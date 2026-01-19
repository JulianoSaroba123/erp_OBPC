from flask import Blueprint, render_template, request, redirect, url_for, flash, send_file, current_app, make_response
from flask_login import login_required
from app.extensoes import db
from .atas_model import Ata
from datetime import datetime
import os

# Importação condicional do weasyprint
try:
    import weasyprint
    WEASYPRINT_AVAILABLE = True
except ImportError:
    WEASYPRINT_AVAILABLE = False
    print("WeasyPrint não disponível. Funcionalidade de PDF será limitada.")

# Importar ReportLab para geração alternativa de PDF
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm, mm
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT
from io import BytesIO

atas_bp = Blueprint('atas', __name__, template_folder='templates')

@atas_bp.route('/secretaria/atas')
@login_required
def lista_atas():
    """Lista todas as atas de reunião"""
    try:
        # Busca com filtro opcional
        busca = request.args.get('busca', '').strip()
        
        if busca:
            atas = Ata.query.filter(
                (Ata.titulo.ilike(f'%{busca}%')) |
                (Ata.responsavel.ilike(f'%{busca}%')) |
                (Ata.local.ilike(f'%{busca}%'))
            ).order_by(Ata.data.desc()).all()
        else:
            atas = Ata.query.order_by(Ata.data.desc()).all()
        
        return render_template('atas/lista_atas.html', atas=atas, busca=busca)
    except Exception as e:
        flash(f'Erro ao carregar lista de atas: {str(e)}', 'danger')
        return render_template('atas/lista_atas.html', atas=[])

@atas_bp.route('/secretaria/atas/nova')
@login_required
def nova_ata():
    """Exibe formulário para nova ata"""
    return render_template('atas/cadastro_ata.html')

@atas_bp.route('/secretaria/atas/editar/<int:id>')
@login_required
def editar_ata(id):
    """Exibe formulário para editar ata"""
    try:
        ata = Ata.query.get_or_404(id)
        return render_template('atas/cadastro_ata.html', ata=ata)
    except Exception as e:
        flash(f'Erro ao carregar ata: {str(e)}', 'danger')
        return redirect(url_for('atas.lista_atas'))

@atas_bp.route('/secretaria/atas/salvar', methods=['POST'])
@login_required
def salvar_ata():
    """Salva nova ata ou atualiza existente"""
    try:
        ata_id = request.form.get('ata_id')
        titulo = request.form.get('titulo', '').strip()
        data_str = request.form.get('data', '').strip()
        local = request.form.get('local', '').strip()
        responsavel = request.form.get('responsavel', '').strip()
        descricao = request.form.get('descricao', '').strip()
        
        # Validações
        if not titulo:
            flash('Título é obrigatório', 'danger')
            return redirect(url_for('atas.nova_ata'))
        
        if not data_str:
            flash('Data é obrigatória', 'danger')
            return redirect(url_for('atas.nova_ata'))
        
        # Converter data
        try:
            data = datetime.strptime(data_str, '%Y-%m-%d').date()
        except ValueError:
            flash('Data inválida', 'danger')
            return redirect(url_for('atas.nova_ata'))
        
        if ata_id:
            # Atualizar ata existente
            ata = Ata.query.get_or_404(ata_id)
            ata.titulo = titulo
            ata.data = data
            ata.local = local
            ata.responsavel = responsavel
            ata.descricao = descricao
            flash('Ata atualizada com sucesso!', 'success')
        else:
            # Criar nova ata
            ata = Ata(
                titulo=titulo,
                data=data,
                local=local,
                responsavel=responsavel,
                descricao=descricao
            )
            db.session.add(ata)
            flash('Ata cadastrada com sucesso!', 'success')
        
        db.session.commit()
        return redirect(url_for('atas.lista_atas'))
        
    except Exception as e:
        db.session.rollback()
        flash(f'Erro ao salvar ata: {str(e)}', 'danger')
        return redirect(url_for('atas.nova_ata'))

@atas_bp.route('/secretaria/atas/pdf/<int:id>')
@login_required
def gerar_pdf_ata(id):
    """Gera PDF da ata"""
    try:
        ata = Ata.query.get_or_404(id)
        
        # Obter configurações da igreja
        from app.configuracoes.configuracoes_model import Configuracao
        config = Configuracao.obter_configuracao()
        
        if not config:
            flash('Erro: Configurações do sistema não encontradas. Configure o sistema primeiro.', 'danger')
            return redirect(url_for('atas.lista_atas'))
        
        # Renderizar template HTML
        try:
            html_content = render_template('atas/pdf_ata.html', 
                                         ata=ata, 
                                         config=config,
                                         data_geracao=datetime.now().strftime('%d/%m/%Y às %H:%M'),
                                         base_url=request.url_root)
        except Exception as template_error:
            print(f"Erro ao renderizar template HTML: {str(template_error)}")
            # Se falhar o template HTML, usa diretamente o ReportLab
            return gerar_pdf_ata_reportlab(ata, config)
        
        # Verificar se weasyprint está disponível
        if not WEASYPRINT_AVAILABLE:
            # Usar ReportLab como alternativa
            print("WeasyPrint não disponível, usando ReportLab")
            return gerar_pdf_ata_reportlab(ata, config)
        
        # Configura o WeasyPrint
        base_url = request.url_root
        
        # Gerar PDF
        try:
            pdf = weasyprint.HTML(string=html_content, base_url=base_url).write_pdf()
        except Exception as weasy_error:
            print(f"Erro ao gerar PDF com WeasyPrint: {str(weasy_error)}")
            # Fallback para ReportLab
            return gerar_pdf_ata_reportlab(ata, config)
        
        # Define nome do arquivo
        filename = f"ata_{ata.id}_{ata.data.strftime('%Y%m%d')}.pdf"
        filepath = os.path.join('app', 'static', 'atas', filename)
        
        # Salva o arquivo
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        with open(filepath, 'wb') as f:
            f.write(pdf)
        
        # Atualizar caminho do arquivo na ata
        ata.arquivo = f'static/atas/{filename}'
        db.session.commit()
        
        # Retorna o PDF para download
        response = make_response(pdf)
        response.headers['Content-Type'] = 'application/pdf'
        response.headers['Content-Disposition'] = f'inline; filename="{filename}"'
        
        return response
        
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        print(f"ERRO DETALHADO ao gerar PDF da ata {id}:")
        print(error_trace)
        flash(f'Erro ao gerar PDF: {str(e)}. Verifique os logs para mais detalhes.', 'danger')
        return redirect(url_for('atas.lista_atas'))

@atas_bp.route('/secretaria/atas/excluir/<int:id>', methods=['POST'])
@login_required
def excluir_ata(id):
    """Exclui uma ata"""
    try:
        ata = Ata.query.get_or_404(id)
        
        # Remover arquivo PDF se existir
        if ata.arquivo:
            filepath = os.path.join(current_app.static_folder, ata.arquivo)
            if os.path.exists(filepath):
                os.remove(filepath)
        
        db.session.delete(ata)
        db.session.commit()
        flash('Ata excluída com sucesso!', 'success')
        
    except Exception as e:
        db.session.rollback()
        flash(f'Erro ao excluir ata: {str(e)}', 'danger')
    
    return redirect(url_for('atas.lista_atas'))

@atas_bp.route('/secretaria/atas/download/<int:id>')
@login_required
def download_ata(id):
    """Download do PDF da ata"""
    try:
        ata = Ata.query.get_or_404(id)
        
        if not ata.arquivo:
            flash('PDF não encontrado. Gere o PDF primeiro.', 'warning')
            return redirect(url_for('atas.lista_atas'))
        
        filepath = os.path.join(current_app.static_folder, ata.arquivo)
        
        if not os.path.exists(filepath):
            flash('Arquivo PDF não encontrado.', 'danger')
            return redirect(url_for('atas.lista_atas'))
        
        filename = f"ata_{ata.titulo.replace(' ', '_')}_{ata.data.strftime('%Y%m%d')}.pdf"
        return send_file(filepath, as_attachment=True, download_name=filename)
        
    except Exception as e:
        flash(f'Erro ao baixar arquivo: {str(e)}', 'danger')
        return redirect(url_for('atas.lista_atas'))


def gerar_pdf_ata_reportlab(ata, config):
    """Gera PDF da ata usando ReportLab como alternativa ao WeasyPrint"""
    try:
        # Criar buffer em memória
        buffer = BytesIO()
        
        # Configurar documento
        doc = SimpleDocTemplate(buffer, pagesize=A4, 
                              rightMargin=2*cm, leftMargin=2*cm,
                              topMargin=2*cm, bottomMargin=2*cm)
        
        # Obter estilos
        styles = getSampleStyleSheet()
        
        # Criar estilos customizados
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=16,
            spaceAfter=20,
            alignment=TA_CENTER,
            textColor=colors.darkblue
        )
        
        subtitle_style = ParagraphStyle(
            'CustomSubtitle',
            parent=styles['Heading2'],
            fontSize=12,
            spaceAfter=15,
            alignment=TA_CENTER
        )
        
        content_style = ParagraphStyle(
            'CustomContent',
            parent=styles['Normal'],
            fontSize=11,
            spaceAfter=12,
            alignment=TA_JUSTIFY,
            leftIndent=10,
            rightIndent=10
        )
        
        # Construir conteúdo
        story = []
        
        # Logo da igreja das configurações
        try:
            logo_adicionado = False
            
            # Primeiro tenta usar a logo das configurações
            if config.logo:
                logo_path = os.path.join(current_app.static_folder, config.logo)
                if os.path.exists(logo_path):
                    current_app.logger.info(f'Usando logo das configurações: {logo_path}')
                    logo = Image(logo_path, width=120, height=120)
                    logo.hAlign = 'CENTER'
                    story.append(logo)
                    story.append(Spacer(1, 10))
                    logo_adicionado = True
            
            # Se não conseguiu usar a logo das configurações, tenta fallbacks
            if not logo_adicionado:
                fallback_logos = ['logo_obpc_novo.jpg', 'Logo_OBPC.jpg']
                for fallback_logo in fallback_logos:
                    try:
                        logo_path = os.path.join(current_app.static_folder, fallback_logo)
                        if os.path.exists(logo_path):
                            current_app.logger.info(f'Usando logo fallback: {logo_path}')
                            logo = Image(logo_path, width=120, height=120)
                            logo.hAlign = 'CENTER' 
                            story.append(logo)
                            story.append(Spacer(1, 10))
                            break
                    except Exception as e:
                        current_app.logger.warning(f'Erro ao carregar logo {fallback_logo}: {str(e)}')
                        continue
        except Exception as e:
            current_app.logger.error(f'Erro ao processar logo: {str(e)}')
            # Se não conseguir carregar logo, continua sem ele
            pass
        
        # Cabeçalho da igreja
        story.append(Paragraph(config.nome_igreja, title_style))
        story.append(Paragraph(f"{config.endereco}, {config.cidade}", subtitle_style))
        story.append(Paragraph(f"CNPJ: {config.cnpj} | Tel: {config.telefone}", subtitle_style))
        story.append(Spacer(1, 20))
        
        # Título da ata
        story.append(Paragraph(f"ATA DE REUNIÃO", title_style))
        story.append(Spacer(1, 15))
        
        # Informações da ata
        info_data = [
            ['Título:', ata.titulo],
            ['Data:', ata.data.strftime('%d/%m/%Y')],
            ['Local:', ata.local or 'Não informado'],
            ['Responsável:', ata.responsavel or 'Não informado']
        ]
        
        info_table = Table(info_data, colWidths=[3*cm, 12*cm])
        info_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ]))
        
        story.append(info_table)
        story.append(Spacer(1, 20))
        
        # Conteúdo da ata
        story.append(Paragraph("CONTEÚDO DA REUNIÃO:", subtitle_style))
        story.append(Spacer(1, 10))
        
        # Dividir descrição em parágrafos
        if ata.descricao:
            paragrafos = ata.descricao.split('\n')
            for paragrafo in paragrafos:
                if paragrafo.strip():
                    story.append(Paragraph(paragrafo.strip(), content_style))
        else:
            story.append(Paragraph("Nenhum conteúdo registrado.", content_style))
        
        story.append(Spacer(1, 30))
        
        # Assinaturas
        story.append(Paragraph("ASSINATURAS:", subtitle_style))
        story.append(Spacer(1, 20))
        
        # Criar tabela de assinaturas
        assinaturas_data = [
            ['Responsável:', '_' * 40, 'Data:', '_' * 20],
            ['', '', '', ''],
            ['Dirigente:', '_' * 40, 'Data:', '_' * 20],
            ['', '', '', '']
        ]
        
        assinaturas_table = Table(assinaturas_data, colWidths=[2.5*cm, 6*cm, 1.5*cm, 4*cm])
        assinaturas_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('ALIGN', (0, 0), (0, -1), 'LEFT'),
            ('ALIGN', (1, 0), (1, -1), 'CENTER'),
            ('ALIGN', (2, 0), (2, -1), 'LEFT'),
            ('ALIGN', (3, 0), (3, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ]))
        
        story.append(assinaturas_table)
        story.append(Spacer(1, 20))
        
        # Rodapé
        story.append(Paragraph(f"Documento gerado em {datetime.now().strftime('%d/%m/%Y às %H:%M')}", 
                             ParagraphStyle('Footer', parent=styles['Normal'], fontSize=8, 
                                          alignment=TA_CENTER, textColor=colors.grey)))
        
        # Gerar PDF
        doc.build(story)
        
        # Obter dados do buffer
        pdf_data = buffer.getvalue()
        buffer.close()
        
        # Define nome do arquivo
        filename = f"ata_{ata.id}_{ata.data.strftime('%Y%m%d')}.pdf"
        filepath = os.path.join('app', 'static', 'atas', filename)
        
        # Salva o arquivo
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        with open(filepath, 'wb') as f:
            f.write(pdf_data)
        
        # Atualizar caminho do arquivo na ata
        ata.arquivo = f'static/atas/{filename}'
        db.session.commit()
        
        # Retorna o PDF para download
        response = make_response(pdf_data)
        response.headers['Content-Type'] = 'application/pdf'
        response.headers['Content-Disposition'] = f'inline; filename="{filename}"'
        
        return response
        
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        print(f"ERRO DETALHADO ao gerar PDF com ReportLab da ata {ata.id}:")
        print(error_trace)
        flash(f'Erro ao gerar PDF com ReportLab: {str(e)}. Verifique os logs para mais detalhes.', 'danger')
        return redirect(url_for('atas.lista_atas'))