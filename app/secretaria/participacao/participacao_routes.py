from flask import Blueprint, render_template, request, redirect, url_for, flash, make_response
from flask_login import login_required
from datetime import datetime, date

# Importação condicional do weasyprint
try:
    import weasyprint
    WEASYPRINT_AVAILABLE = True
except ImportError:
    WEASYPRINT_AVAILABLE = False
    print("WeasyPrint não disponível. Funcionalidade de PDF será limitada.")

from app.extensoes import db
from app.secretaria.participacao.participacao_model import ParticipacaoObreiro
from app.obreiros.obreiros_model import Obreiro
from app.configuracoes.configuracoes_model import Configuracao

participacao_bp = Blueprint('participacao', __name__, 
                           template_folder='templates',
                           url_prefix='/secretaria/participacao')

@participacao_bp.route('/')
@login_required
def listar_participacoes():
    """Lista todas as participações com filtros opcionais"""
    try:
        # Obter filtros da query string
        periodo = request.args.get('periodo')  # formato YYYY-MM
        tipo = request.args.get('tipo')
        presenca_filtro = request.args.get('presenca')
        
        # Construir query base
        query = ParticipacaoObreiro.query
        
        # Aplicar filtros
        if periodo:
            try:
                ano, mes = periodo.split('-')
                query = query.filter(
                    db.extract('year', ParticipacaoObreiro.data_reuniao) == int(ano),
                    db.extract('month', ParticipacaoObreiro.data_reuniao) == int(mes)
                )
            except ValueError:
                flash('Período inválido', 'warning')
        
        if tipo:
            query = query.filter(ParticipacaoObreiro.tipo_reuniao == tipo)
            
        if presenca_filtro:
            query = query.filter(ParticipacaoObreiro.presenca == presenca_filtro)
        
        # Ordenar por data mais recente
        participacoes = query.order_by(ParticipacaoObreiro.data_reuniao.desc()).all()
        
        # Estatísticas rápidas
        total_participacoes = len(participacoes)
        presentes = len([p for p in participacoes if p.presenca == 'Presente'])
        ausentes = len([p for p in participacoes if p.presenca == 'Ausente'])
        justificados = len([p for p in participacoes if p.presenca == 'Justificado'])
        
        return render_template('participacao/lista_participacao.html',
                             participacoes=participacoes,
                             tipos_reuniao=ParticipacaoObreiro.get_tipos_reuniao(),
                             status_presenca=ParticipacaoObreiro.get_status_presenca(),
                             total_participacoes=total_participacoes,
                             presentes=presentes,
                             ausentes=ausentes,
                             justificados=justificados)
    except Exception as e:
        flash(f'Erro ao carregar participações: {str(e)}', 'danger')
        return render_template('participacao/lista_participacao.html', participacoes=[])

@participacao_bp.route('/nova')
@login_required
def nova_participacao():
    """Exibe formulário para nova participação"""
    try:
        obreiros = Obreiro.query.filter_by(status='Ativo').order_by(Obreiro.nome).all()
        return render_template('participacao/cadastro_participacao.html',
                             obreiros=obreiros,
                             tipos_reuniao=ParticipacaoObreiro.get_tipos_reuniao(),
                             status_presenca=ParticipacaoObreiro.get_status_presenca())
    except Exception as e:
        flash(f'Erro ao carregar formulário: {str(e)}', 'danger')
        return redirect(url_for('participacao.listar_participacoes'))

@participacao_bp.route('/salvar', methods=['POST'])
@login_required
def salvar_participacao():
    """Salva nova participação"""
    try:
        # Obter dados do formulário
        obreiro_id = request.form.get('obreiro_id')
        data_reuniao_str = request.form.get('data_reuniao')
        tipo_reuniao = request.form.get('tipo_reuniao')
        presenca = request.form.get('presenca', 'Presente')
        observacao = request.form.get('observacao', '').strip()
        
        # Validações
        if not obreiro_id:
            flash('Obreiro é obrigatório', 'danger')
            return redirect(url_for('participacao.nova_participacao'))
        
        if not data_reuniao_str:
            flash('Data da reunião é obrigatória', 'danger')
            return redirect(url_for('participacao.nova_participacao'))
        
        if not tipo_reuniao:
            flash('Tipo de reunião é obrigatório', 'danger')
            return redirect(url_for('participacao.nova_participacao'))
        
        # Converter data
        try:
            data_reuniao = datetime.strptime(data_reuniao_str, '%Y-%m-%d').date()
        except ValueError:
            flash('Data inválida', 'danger')
            return redirect(url_for('participacao.nova_participacao'))
        
        # Verificar se o obreiro existe
        obreiro = Obreiro.query.get(obreiro_id)
        if not obreiro:
            flash('Obreiro não encontrado', 'danger')
            return redirect(url_for('participacao.nova_participacao'))
        
        # Verificar se já existe registro para este obreiro nesta data e tipo
        participacao_existente = ParticipacaoObreiro.query.filter_by(
            obreiro_id=obreiro_id,
            data_reuniao=data_reuniao,
            tipo_reuniao=tipo_reuniao
        ).first()
        
        if participacao_existente:
            flash(f'Já existe registro de participação para {obreiro.nome} em {data_reuniao.strftime("%d/%m/%Y")} - {tipo_reuniao}', 'warning')
            return redirect(url_for('participacao.nova_participacao'))
        
        # Criar nova participação
        nova_participacao = ParticipacaoObreiro(
            obreiro_id=obreiro_id,
            data_reuniao=data_reuniao,
            tipo_reuniao=tipo_reuniao,
            presenca=presenca,
            observacao=observacao
        )
        
        db.session.add(nova_participacao)
        db.session.commit()
        
        flash(f'Participação de {obreiro.nome} registrada com sucesso!', 'success')
        return redirect(url_for('participacao.listar_participacoes'))
        
    except Exception as e:
        db.session.rollback()
        flash(f'Erro ao salvar participação: {str(e)}', 'danger')
        return redirect(url_for('participacao.nova_participacao'))

@participacao_bp.route('/editar/<int:id>', methods=['GET', 'POST'])
@login_required
def editar_participacao(id):
    """Edita uma participação existente"""
    try:
        participacao = ParticipacaoObreiro.query.get_or_404(id)
        
        if request.method == 'POST':
            # Salvar alterações
            obreiro_id = request.form.get('obreiro_id')
            data_reuniao_str = request.form.get('data_reuniao')
            tipo_reuniao = request.form.get('tipo_reuniao')
            presenca = request.form.get('presenca', 'Presente')
            observacao = request.form.get('observacao', '').strip()
            
            # Validações
            if not obreiro_id:
                flash('Obreiro é obrigatório', 'danger')
                return redirect(url_for('participacao.editar_participacao', id=id))
            
            if not data_reuniao_str:
                flash('Data da reunião é obrigatória', 'danger')
                return redirect(url_for('participacao.editar_participacao', id=id))
            
            if not tipo_reuniao:
                flash('Tipo de reunião é obrigatório', 'danger')
                return redirect(url_for('participacao.editar_participacao', id=id))
            
            # Converter data
            try:
                data_reuniao = datetime.strptime(data_reuniao_str, '%Y-%m-%d').date()
            except ValueError:
                flash('Data inválida', 'danger')
                return redirect(url_for('participacao.editar_participacao', id=id))
            
            # Verificar se o obreiro existe
            obreiro = Obreiro.query.get(obreiro_id)
            if not obreiro:
                flash('Obreiro não encontrado', 'danger')
                return redirect(url_for('participacao.editar_participacao', id=id))
            
            # Verificar se já existe participação para este obreiro nesta data e tipo (exceto a atual)
            participacao_existente = ParticipacaoObreiro.query.filter(
                ParticipacaoObreiro.obreiro_id == obreiro_id,
                ParticipacaoObreiro.data_reuniao == data_reuniao,
                ParticipacaoObreiro.tipo_reuniao == tipo_reuniao,
                ParticipacaoObreiro.id != id
            ).first()
            
            if participacao_existente:
                flash(f'Já existe participação registrada para {obreiro.nome} nesta data e tipo de reunião', 'warning')
                return redirect(url_for('participacao.editar_participacao', id=id))
            
            # Atualizar dados
            participacao.obreiro_id = obreiro_id
            participacao.data_reuniao = data_reuniao
            participacao.tipo_reuniao = tipo_reuniao
            participacao.presenca = presenca
            participacao.observacao = observacao if observacao else None
            
            db.session.commit()
            flash(f'Participação de {obreiro.nome} atualizada com sucesso!', 'success')
            return redirect(url_for('participacao.listar_participacoes'))
        
        else:
            # Exibir formulário de edição
            obreiros = Obreiro.query.filter_by(status='Ativo').order_by(Obreiro.nome).all()
            return render_template('participacao/cadastro_participacao.html',
                                 participacao=participacao,
                                 obreiros=obreiros,
                                 tipos_reuniao=ParticipacaoObreiro.get_tipos_reuniao(),
                                 status_presenca=ParticipacaoObreiro.get_status_presenca(),
                                 modo='editar')
        
    except Exception as e:
        db.session.rollback()
        flash(f'Erro ao editar participação: {str(e)}', 'danger')
        return redirect(url_for('participacao.listar_participacoes'))

@participacao_bp.route('/excluir/<int:id>')
@login_required
def excluir_participacao(id):
    """Exclui uma participação"""
    try:
        participacao = ParticipacaoObreiro.query.get_or_404(id)
        nome_obreiro = participacao.obreiro.nome if participacao.obreiro else 'Obreiro'
        data_reuniao = participacao.data_reuniao.strftime('%d/%m/%Y')
        
        db.session.delete(participacao)
        db.session.commit()
        
        flash(f'Participação de {nome_obreiro} ({data_reuniao}) excluída com sucesso!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Erro ao excluir participação: {str(e)}', 'danger')
    
    return redirect(url_for('participacao.listar_participacoes'))

@participacao_bp.route('/pdf')
@login_required
def gerar_pdf_participacao():
    """Gera relatório PDF de participações"""
    try:
        # Obter filtros da query string (se houver)
        periodo = request.args.get('periodo')
        tipo = request.args.get('tipo')
        presenca_filtro = request.args.get('presenca')
        
        # Construir query
        query = ParticipacaoObreiro.query
        
        # Aplicar filtros
        filtros_aplicados = []
        if periodo:
            try:
                ano, mes = periodo.split('-')
                query = query.filter(
                    db.extract('year', ParticipacaoObreiro.data_reuniao) == int(ano),
                    db.extract('month', ParticipacaoObreiro.data_reuniao) == int(mes)
                )
                filtros_aplicados.append(f"Período: {mes}/{ano}")
            except ValueError:
                pass
        
        if tipo:
            query = query.filter(ParticipacaoObreiro.tipo_reuniao == tipo)
            filtros_aplicados.append(f"Tipo: {tipo}")
            
        if presenca_filtro:
            query = query.filter(ParticipacaoObreiro.presenca == presenca_filtro)
            filtros_aplicados.append(f"Presença: {presenca_filtro}")
        
        # Buscar participações
        participacoes = query.order_by(
            ParticipacaoObreiro.data_reuniao.desc(),
            ParticipacaoObreiro.tipo_reuniao.asc()
        ).all()
        
        # Buscar configurações da igreja
        try:
            config_obj = Configuracao.query.first()
        except:
            config_obj = None
        
        # Dados da igreja (com fallback se não houver configuração)
        if config_obj:
            config = {
                'nome_igreja': config_obj.nome_igreja,
                'endereco': config_obj.endereco if config_obj.endereco else 'Rua das Flores, 123',
                'cidade': f"{config_obj.cidade} - SP" if config_obj.cidade else 'Tietê - SP',
                'cnpj': config_obj.cnpj if config_obj.cnpj else '12.345.678/0001-99',
                'telefone': config_obj.telefone if config_obj.telefone else '(15) 3285-1234',
                'email': config_obj.email if config_obj.email else 'contato@obpctcp.org.br'
            }
        else:
            config = {
                'nome_igreja': 'ORGANIZAÇÃO BATISTA PEDRA DE CRISTO',
                'endereco': 'Rua das Flores, 123',
                'cidade': 'Tietê - SP',
                'cnpj': '12.345.678/0001-99',
                'telefone': '(15) 3285-1234',
                'email': 'contato@obpctcp.org.br'
            }
        
        # Estatísticas para o relatório
        total_participacoes = len(participacoes)
        presentes = len([p for p in participacoes if p.presenca == 'Presente'])
        ausentes = len([p for p in participacoes if p.presenca == 'Ausente'])
        justificados = len([p for p in participacoes if p.presenca == 'Justificado'])
        
        # Renderizar template HTML
        html_content = render_template('participacao/relatorio_participacao.html',
                                     participacoes=participacoes,
                                     config=config,
                                     data_geracao=datetime.now().strftime('%d/%m/%Y às %H:%M'),
                                     filtros_aplicados=filtros_aplicados,
                                     total_participacoes=total_participacoes,
                                     presentes=presentes,
                                     ausentes=ausentes,
                                     justificados=justificados)
        
        # Gerar PDF
        base_url = request.url_root
        pdf = weasyprint.HTML(string=html_content, base_url=base_url).write_pdf()
        
        # Criar resposta
        response = make_response(pdf)
        response.headers['Content-Type'] = 'application/pdf'
        response.headers['Content-Disposition'] = 'inline; filename=Participacao_Obreiros.pdf'
        
        return response
        
    except Exception as e:
        flash(f'Erro ao gerar PDF: {str(e)}', 'danger')
        return redirect(url_for('participacao.listar_participacoes'))