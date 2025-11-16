from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, make_response
from flask_login import login_required
from app.extensoes import db
from app.escala_ministerial.escala_model import EscalaMinisterial
from app.midia.midia_model import AgendaSemanal
from app.configuracoes.configuracoes_model import Configuracao
from datetime import datetime, date
import calendar

# Blueprint para Agenda Pastoral
escala_ministerial_bp = Blueprint('escala_ministerial', __name__, template_folder='templates')

@escala_ministerial_bp.route('/escala-ministerial')
@escala_ministerial_bp.route('/escala-ministerial/')
@login_required
def listar_escalas():
    """Lista todas as escalas ministeriais"""
    try:
        # Filtros
        mes = request.args.get('mes', type=int)
        ano = request.args.get('ano', type=int, default=datetime.now().year)
        
        # Query base
        query = EscalaMinisterial.query.filter_by(ativo=True)
        
        # Aplicar filtros
        if mes:
            query = query.filter(
                db.extract('month', EscalaMinisterial.data_evento) == mes,
                db.extract('year', EscalaMinisterial.data_evento) == ano
            )
        else:
            # Se não especificar mês, mostrar do ano atual
            query = query.filter(db.extract('year', EscalaMinisterial.data_evento) == ano)
        
        escalas = query.order_by(EscalaMinisterial.data_evento.asc()).all()
        
        # Dados para filtros
        meses = [
            (1, 'Janeiro'), (2, 'Fevereiro'), (3, 'Março'), (4, 'Abril'),
            (5, 'Maio'), (6, 'Junho'), (7, 'Julho'), (8, 'Agosto'),
            (9, 'Setembro'), (10, 'Outubro'), (11, 'Novembro'), (12, 'Dezembro')
        ]
        
        anos = list(range(2024, 2030))
        
        return render_template('escala_ministerial/lista_escala.html',
                             escalas=escalas,
                             meses=meses,
                             anos=anos,
                             mes_atual=mes,
                             ano_atual=ano)
                             
    except Exception as e:
        flash(f'Erro ao carregar escalas: {str(e)}', 'danger')
        return render_template('escala_ministerial/lista_escala.html',
                             escalas=[],
                             meses=[], anos=[], 
                             mes_atual=None, ano_atual=datetime.now().year)

@escala_ministerial_bp.route('/escala-ministerial/nova')
@login_required
def nova_escala():
    """Exibe formulário para nova escala"""
    try:
        # Buscar eventos disponíveis da agenda semanal
        eventos = AgendaSemanal.query.filter_by(ativo=True).order_by(AgendaSemanal.data_evento.asc()).all()
        
        return render_template('escala_ministerial/cadastro_escala.html', 
                             eventos=eventos, escala=None)
    except Exception as e:
        flash(f'Erro ao carregar formulário: {str(e)}', 'danger')
        return redirect(url_for('escala_ministerial.listar_escalas'))

@escala_ministerial_bp.route('/escala-ministerial/salvar', methods=['POST'])
@login_required
def salvar_escala():
    """Salva nova escala ou atualiza existente"""
    try:
        # Capturar dados do formulário
        escala_id = request.form.get('id')
        evento_id = request.form.get('evento_id', type=int)
        data_evento_str = request.form.get('data_evento')
        pregador = request.form.get('pregador', '').strip()
        dirigente = request.form.get('dirigente', '').strip()
        louvor = request.form.get('louvor', '').strip()
        intercessor = request.form.get('intercessor', '').strip()
        diaconia = request.form.get('diaconia', '').strip()
        observacoes = request.form.get('observacoes', '').strip()
        
        # Validações
        if not data_evento_str:
            flash('Data do evento é obrigatória!', 'danger')
            return redirect(url_for('escala_ministerial.nova_escala'))
        
        try:
            data_evento = datetime.strptime(data_evento_str, '%Y-%m-%d').date()
        except ValueError:
            flash('Data do evento inválida!', 'danger')
            return redirect(url_for('escala_ministerial.nova_escala'))
        
        # Verificar se já existe escala para esta data
        escala_existente = EscalaMinisterial.query.filter_by(
            data_evento=data_evento, ativo=True
        ).first()
        
        if escala_existente and (not escala_id or str(escala_existente.id) != escala_id):
            flash(f'Já existe uma escala para a data {data_evento.strftime("%d/%m/%Y")}!', 'danger')
            return redirect(url_for('escala_ministerial.nova_escala'))
        
        if escala_id:
            # Atualizar escala existente
            escala = EscalaMinisterial.query.get_or_404(escala_id)
            escala.evento_id = evento_id if evento_id else None
            escala.data_evento = data_evento
            escala.pregador = pregador if pregador else None
            escala.dirigente = dirigente if dirigente else None
            escala.louvor = louvor if louvor else None
            escala.intercessor = intercessor if intercessor else None
            escala.diaconia = diaconia if diaconia else None
            escala.observacoes = observacoes if observacoes else None
            escala.atualizado_em = datetime.utcnow()
            
            flash('Agenda pastoral atualizada com sucesso!', 'success')
        else:
            # Criar nova escala
            nova_escala = EscalaMinisterial(
                evento_id=evento_id if evento_id else None,
                data_evento=data_evento,
                pregador=pregador if pregador else None,
                dirigente=dirigente if dirigente else None,
                louvor=louvor if louvor else None,
                intercessor=intercessor if intercessor else None,
                diaconia=diaconia if diaconia else None,
                observacoes=observacoes if observacoes else None
            )
            
            db.session.add(nova_escala)
            flash('Agenda pastoral cadastrada com sucesso!', 'success')
        
        db.session.commit()
        return redirect(url_for('escala_ministerial.listar_escalas'))
        
    except Exception as e:
        db.session.rollback()
        flash(f'Erro ao salvar escala: {str(e)}', 'danger')
        return redirect(url_for('escala_ministerial.nova_escala'))

@escala_ministerial_bp.route('/escala-ministerial/editar/<int:id>')
@login_required
def editar_escala(id):
    """Carrega dados da escala para edição"""
    try:
        escala = EscalaMinisterial.query.get_or_404(id)
        eventos = AgendaSemanal.query.filter_by(ativo=True).order_by(AgendaSemanal.data_evento.asc()).all()
        
        return render_template('escala_ministerial/cadastro_escala.html', 
                             eventos=eventos, escala=escala)
    except Exception as e:
        flash(f'Erro ao carregar dados da escala: {str(e)}', 'danger')
        return redirect(url_for('escala_ministerial.listar_escalas'))

@escala_ministerial_bp.route('/escala-ministerial/excluir/<int:id>', methods=['POST'])
@login_required
def excluir_escala(id):
    """Exclui uma agenda pastoral"""
    try:
        escala = EscalaMinisterial.query.get_or_404(id)
        data_escala = escala.data_formatada
        
        # Exclusão lógica
        escala.ativo = False
        escala.atualizado_em = datetime.utcnow()
        
        db.session.commit()
        flash(f'Escala de {data_escala} excluída com sucesso!', 'success')
        
    except Exception as e:
        db.session.rollback()
        flash(f'Erro ao excluir escala: {str(e)}', 'danger')
    
    return redirect(url_for('escala_ministerial.listar_escalas'))

@escala_ministerial_bp.route('/escala-ministerial/pdf')
@login_required
def gerar_pdf_escala():
    """Gera PDF da agenda pastoral"""
    try:
        # Filtros para PDF
        mes = request.args.get('mes', type=int)
        ano = request.args.get('ano', type=int, default=datetime.now().year)
        
        # Query para PDF
        query = EscalaMinisterial.query.filter_by(ativo=True)
        
        if mes:
            query = query.filter(
                db.extract('month', EscalaMinisterial.data_evento) == mes,
                db.extract('year', EscalaMinisterial.data_evento) == ano
            )
            periodo = f"{calendar.month_name[mes]} de {ano}"
        else:
            query = query.filter(db.extract('year', EscalaMinisterial.data_evento) == ano)
            periodo = f"Ano {ano}"
        
        escalas = query.order_by(EscalaMinisterial.data_evento.asc()).all()
        
        # Configurações da igreja
        config = Configuracao.query.first()
        
        return render_template('escala_ministerial/pdf_escala.html',
                             escalas=escalas,
                             config=config,
                             periodo=periodo,
                             data_geracao=datetime.now())
                             
    except Exception as e:
        flash(f'Erro ao gerar PDF: {str(e)}', 'danger')
        return redirect(url_for('escala_ministerial.listar_escalas'))

@escala_ministerial_bp.route('/api/escala-ministerial/autocomplete/<campo>')
@login_required
def autocomplete_obreiros(campo):
    """API para autocomplete de obreiros"""
    try:
        term = request.args.get('term', '').strip()
        
        if not term or len(term) < 2:
            return jsonify([])
        
        # Campos válidos para autocomplete
        campos_validos = ['pregador', 'dirigente', 'louvor', 'intercessor', 'diaconia']
        
        if campo not in campos_validos:
            return jsonify([])
        
        # Buscar nomes únicos no campo específico
        query = db.session.query(getattr(EscalaMinisterial, campo)).filter(
            getattr(EscalaMinisterial, campo).ilike(f'%{term}%'),
            EscalaMinisterial.ativo == True,
            getattr(EscalaMinisterial, campo).isnot(None)
        ).distinct().limit(10)
        
        resultados = [nome[0] for nome in query.all() if nome[0]]
        
        return jsonify(resultados)
        
    except Exception as e:
        return jsonify([])

@escala_ministerial_bp.route('/api/escala-ministerial/evento/<int:evento_id>')
@login_required
def buscar_dados_evento(evento_id):
    """API para buscar dados do evento selecionado"""
    try:
        evento = AgendaSemanal.query.get_or_404(evento_id)
        
        return jsonify({
            'sucesso': True,
            'evento': {
                'id': evento.id,
                'titulo': evento.titulo,
                'data_evento': evento.data_evento.strftime('%Y-%m-%d'),
                'horario': evento.horario.strftime('%H:%M') if evento.horario else None,
                'local': evento.local,
                'descricao': evento.descricao
            }
        })
        
    except Exception as e:
        return jsonify({'sucesso': False, 'erro': str(e)})
