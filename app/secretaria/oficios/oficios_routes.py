import os
from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for, flash, send_file, make_response, current_app
from flask_login import login_required
from app import db
from app.secretaria.oficios.oficios_model import Oficio

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

oficios_bp = Blueprint('oficios', __name__, 
                      template_folder='templates',
                      url_prefix='/secretaria/oficios')

@oficios_bp.route('/')
@login_required
def lista_oficios():
    """Lista todos os ofícios com busca e filtros"""
    busca = request.args.get('busca', '').strip()
    status = request.args.get('status', '').strip()
    
    query = Oficio.query
    
    # Filtro por busca (destinatário, assunto ou número)
    if busca:
        query = query.filter(
            db.or_(
                Oficio.destinatario.ilike(f'%{busca}%'),
                Oficio.assunto.ilike(f'%{busca}%'),
                Oficio.numero.ilike(f'%{busca}%')
            )
        )
    
    # Filtro por status
    if status:
        query = query.filter(Oficio.status == status)
    
    # Ordenação por data de criação (mais recentes primeiro)
    oficios = query.order_by(Oficio.criado_em.desc()).all()
    
    return render_template('oficios/lista_oficios.html', 
                         oficios=oficios,
                         busca=busca,
                         status_selecionado=status,
                         status_options=Oficio.get_status_options())

@oficios_bp.route('/novo')
@login_required
def novo_oficio():
    """Formulário para criar novo ofício"""
    return render_template('oficios/cadastro_oficio.html')

@oficios_bp.route('/visualizar/<int:id>')
@login_required
def visualizar_oficio(id):
    """Visualiza detalhes do ofício"""
    oficio = Oficio.query.get_or_404(id)
    return render_template('oficios/visualizar_oficio.html', oficio=oficio)

@oficios_bp.route('/editar/<int:id>')
@login_required
def editar_oficio(id):
    """Formulário para editar ofício existente"""
    oficio = Oficio.query.get_or_404(id)
    return render_template('oficios/editar_oficio.html', oficio=oficio)

@oficios_bp.route('/atualizar/<int:id>', methods=['POST'])
@login_required
def atualizar_oficio(id):
    """Atualiza os dados do ofício"""
    try:
        oficio = Oficio.query.get_or_404(id)
        
        # Captura dados do formulário
        destinatario = request.form.get('destinatario', '').strip()
        assunto = request.form.get('assunto', '').strip()
        descricao = request.form.get('descricao', '').strip()
        status = request.form.get('status', 'Emitido').strip()
        
        # Validações
        if not destinatario:
            flash('Destinatário é obrigatório!', 'error')
            return redirect(url_for('oficios.editar_oficio', id=id))
        
        if not assunto:
            flash('Assunto é obrigatório!', 'error')
            return redirect(url_for('oficios.editar_oficio', id=id))
        
        if not descricao:
            flash('Descrição é obrigatória!', 'error')
            return redirect(url_for('oficios.editar_oficio', id=id))
        
        # Atualiza os dados
        oficio.destinatario = destinatario
        oficio.assunto = assunto
        oficio.descricao = descricao
        oficio.status = status
        
        db.session.commit()
        flash('Ofício atualizado com sucesso!', 'success')
        
        return redirect(url_for('oficios.lista_oficios'))
        
    except Exception as e:
        db.session.rollback()
        flash(f'Erro ao atualizar ofício: {str(e)}', 'error')
        return redirect(url_for('oficios.editar_oficio', id=id))

@oficios_bp.route('/salvar', methods=['POST'])
@login_required
def salvar_oficio():
    """Salva o ofício (novo ou editado)"""
    try:
        # Captura dados do formulário
        oficio_id = request.form.get('id')
        destinatario = request.form.get('destinatario', '').strip()
        assunto = request.form.get('assunto', '').strip()
        descricao = request.form.get('descricao', '').strip()
        status = request.form.get('status', 'Emitido').strip()
        
        # Validações
        if not destinatario:
            flash('Destinatário é obrigatório!', 'error')
            return redirect(url_for('oficios.novo_oficio'))
        
        if not assunto:
            flash('Assunto é obrigatório!', 'error')
            return redirect(url_for('oficios.novo_oficio'))
        
        if not descricao:
            flash('Descrição é obrigatória!', 'error')
            return redirect(url_for('oficios.novo_oficio'))
        
        if oficio_id:
            # Editando ofício existente
            oficio = Oficio.query.get_or_404(oficio_id)
            oficio.destinatario = destinatario
            oficio.assunto = assunto
            oficio.descricao = descricao
            oficio.status = status
            
            flash('Ofício atualizado com sucesso!', 'success')
        else:
            # Criando novo ofício
            numero = Oficio.gerar_proximo_numero()
            
            oficio = Oficio(
                numero=numero,
                destinatario=destinatario,
                assunto=assunto,
                descricao=descricao,
                status=status,
                data=datetime.now().date()
            )
            
            db.session.add(oficio)
            flash(f'Ofício {numero} criado com sucesso!', 'success')
        
        db.session.commit()
        
        return redirect(url_for('oficios.lista_oficios'))
        
    except Exception as e:
        db.session.rollback()
        flash(f'Erro ao salvar ofício: {str(e)}', 'error')
        return redirect(url_for('oficios.novo_oficio'))

@oficios_bp.route('/pdf/<int:id>')
@login_required
def gerar_pdf_oficio(id):
    """Gera e serve o PDF do ofício"""
    try:
        oficio = Oficio.query.get_or_404(id)
        
        # Obter configurações da igreja
        from app.configuracoes.configuracoes_model import Configuracao
        config = Configuracao.obter_configuracao()
        
        if not config:
            flash('Erro: Configurações do sistema não encontradas. Configure o sistema primeiro.', 'danger')
            return redirect(url_for('oficios.lista_oficios'))
        
        # Tentar renderizar template HTML
        try:
            html_content = render_template('oficios/pdf_oficio.html', 
                                         oficio=oficio,
                                         config=config,
                                         data_geracao=datetime.now().strftime('%d/%m/%Y'),
                                         base_url=request.url_root)
        except Exception as template_error:
            print(f"Erro ao renderizar template HTML: {str(template_error)}")
            # Fallback direto para ReportLab
            return gerar_pdf_oficio_reportlab(oficio, config)
        
        # Verifica se WeasyPrint está disponível
        if WEASYPRINT_AVAILABLE:
            try:
                # Gera o PDF
                pdf = weasyprint.HTML(string=html_content, base_url=request.url_root).write_pdf()
                
                # Define nome do arquivo
                nome_arquivo = f"oficio_{oficio.numero}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
                caminho_arquivo = os.path.join('app', 'static', 'oficios', nome_arquivo)
                
                # Salva o arquivo
                os.makedirs(os.path.dirname(caminho_arquivo), exist_ok=True)
                with open(caminho_arquivo, 'wb') as f:
                    f.write(pdf)
                
                # Atualiza o registro do ofício com o caminho do arquivo
                oficio.arquivo = f"static/oficios/{nome_arquivo}"
                db.session.commit()
                
                # Retorna o PDF para download
                response = make_response(pdf)
                response.headers['Content-Type'] = 'application/pdf'
                response.headers['Content-Disposition'] = f'inline; filename="{nome_arquivo}"'
                return response
            except Exception as weasy_error:
                print(f"Erro ao gerar PDF com WeasyPrint: {str(weasy_error)}")
                # Fallback para ReportLab
                return gerar_pdf_oficio_reportlab(oficio, config)
        else:
            # Usar ReportLab como alternativa
            print("WeasyPrint não disponível, usando ReportLab")
            return gerar_pdf_oficio_reportlab(oficio, config)
        
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        print(f"ERRO DETALHADO ao gerar PDF do ofício {id}:")
        print(error_trace)
        flash(f'Erro ao gerar PDF: {str(e)}. Verifique os logs para mais detalhes.', 'danger')
        return redirect(url_for('oficios.lista_oficios'))

def gerar_pdf_oficio_reportlab(oficio, config):
    """Gera PDF do ofício usando ReportLab como alternativa ao WeasyPrint"""
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
        
        # Logo da igreja (se existir)
        try:
            # Usar logo das configurações se habilitado
            if config.logo and config.exibir_logo_relatorio:
                logo_path = os.path.join(current_app.root_path, '..', config.logo)
                if os.path.exists(logo_path):
                    logo = Image(logo_path, width=150, height=150)
                    logo.hAlign = 'CENTER'
                    story.append(logo)
                    story.append(Spacer(1, 10))
                else:
                    # Fallback para logos disponíveis
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
                        except:
                            continue
        except Exception as e:
            # Se não conseguir carregar logo, continua sem ele
            pass
        
        # Cabeçalho da igreja
        story.append(Paragraph(config.nome_igreja or 'Igreja', title_style))
        endereco = config.endereco_completo() if hasattr(config, 'endereco_completo') else f"{config.endereco}, {config.cidade}"
        story.append(Paragraph(endereco, subtitle_style))
        cnpj = config.cnpj_formatado() if hasattr(config, 'cnpj_formatado') else config.cnpj
        telefone = config.telefone_formatado() if hasattr(config, 'telefone_formatado') else config.telefone
        story.append(Paragraph(f"CNPJ: {cnpj} | Tel: {telefone}", subtitle_style))
        story.append(Spacer(1, 30))
        
        # Título do ofício
        story.append(Paragraph(f"OFÍCIO Nº {oficio.numero}", title_style))
        story.append(Spacer(1, 20))
        
        # Data e local
        data_formatada = oficio.data.strftime('%d de %B de %Y') if oficio.data else datetime.now().strftime('%d de %B de %Y')
        story.append(Paragraph(f"Tietê, {data_formatada}", content_style))
        story.append(Spacer(1, 20))
        
        # Destinatário
        story.append(Paragraph(f"Ao(À) {oficio.destinatario}", content_style))
        story.append(Spacer(1, 15))
        
        # Assunto
        story.append(Paragraph(f"<b>Assunto:</b> {oficio.assunto}", content_style))
        story.append(Spacer(1, 20))
        
        # Conteúdo do ofício
        if oficio.descricao:
            paragrafos = oficio.descricao.split('\n')
            for paragrafo in paragrafos:
                if paragrafo.strip():
                    story.append(Paragraph(paragrafo.strip(), content_style))
                    story.append(Spacer(1, 10))
        
        story.append(Spacer(1, 30))
        
        # Assinatura
        story.append(Paragraph("Atenciosamente,", content_style))
        story.append(Spacer(1, 40))
        
        # Linhas de assinatura
        linha_assinatura = "_" * 50
        
        # Criar tabela para as duas assinaturas lado a lado
        assinaturas_data = [
            [linha_assinatura, linha_assinatura],
            [config.presidente or 'Pastor Dirigente', config.primeiro_secretario or 'Secretaria'],
            ["Pastor Dirigente", "Secretaria"]
        ]
        
        assinaturas_table = Table(assinaturas_data, colWidths=[8*cm, 8*cm])
        assinaturas_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('FONTSIZE', (0, 0), (-1, 0), 9),
            ('FONTSIZE', (0, 1), (-1, -1), 10),
            ('FONTNAME', (0, 1), (-1, 1), 'Helvetica-Bold'),
            ('TOPPADDING', (0, 0), (-1, -1), 5),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
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
        nome_arquivo = f"oficio_{oficio.numero}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        caminho_arquivo = os.path.join('app', 'static', 'oficios', nome_arquivo)
        
        # Salva o arquivo
        os.makedirs(os.path.dirname(caminho_arquivo), exist_ok=True)
        with open(caminho_arquivo, 'wb') as f:
            f.write(pdf_data)
        
        # Atualiza o registro do ofício com o caminho do arquivo
        oficio.arquivo = f"static/oficios/{nome_arquivo}"
        db.session.commit()
        
        # Retorna o PDF para download
        response = make_response(pdf_data)
        response.headers['Content-Type'] = 'application/pdf'
        response.headers['Content-Disposition'] = f'inline; filename="{nome_arquivo}"'
        
        return response
        
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        print(f"ERRO DETALHADO ao gerar PDF com ReportLab do ofício {oficio.numero if oficio else 'desconhecido'}:")
        print(error_trace)
        raise Exception(f"Erro na geração com ReportLab: {str(e)}")

@oficios_bp.route('/excluir/<int:id>', methods=['POST'])
@login_required
def excluir_oficio(id):
    """Exclui um ofício"""
    try:
        oficio = Oficio.query.get_or_404(id)
        numero = oficio.numero
        
        # Remove arquivo PDF se existir
        if oficio.arquivo:
            try:
                caminho_completo = os.path.join(oficio.arquivo)
                if os.path.exists(caminho_completo):
                    os.remove(caminho_completo)
            except:
                pass  # Ignora erro se não conseguir remover o arquivo
        
        db.session.delete(oficio)
        db.session.commit()
        
        flash(f'Ofício {numero} excluído com sucesso!', 'success')
        
    except Exception as e:
        db.session.rollback()
        flash(f'Erro ao excluir ofício: {str(e)}', 'error')
    
    return redirect(url_for('oficios.lista_oficios'))

@oficios_bp.route('/atualizar_status/<int:id>', methods=['POST'])
@login_required
def atualizar_status(id):
    """Atualiza o status do ofício"""
    try:
        oficio = Oficio.query.get_or_404(id)
        novo_status = request.form.get('status')
        
        if novo_status in Oficio.get_status_options():
            oficio.status = novo_status
            db.session.commit()
            flash(f'Status do ofício {oficio.numero} atualizado para "{novo_status}"!', 'success')
        else:
            flash('Status inválido!', 'error')
            
    except Exception as e:
        db.session.rollback()
        flash(f'Erro ao atualizar status: {str(e)}', 'error')
    
    return redirect(url_for('oficios.lista_oficios'))