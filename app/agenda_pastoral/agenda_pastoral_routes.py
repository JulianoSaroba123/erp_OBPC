"""
Rotas da Agenda Pastoral
Cada pastor gerencia sua agenda privada
"""

from flask import Blueprint, render_template, redirect, url_for, request, flash, jsonify
from flask_login import login_required, current_user
from app.extensoes import db
from app.agenda_pastoral.agenda_pastoral_model import AgendaPastoral
from datetime import datetime, date, timedelta

agenda_pastoral_bp = Blueprint('agenda_pastoral', __name__, template_folder='templates')

@agenda_pastoral_bp.route('/agenda-pastoral')
@login_required
def lista_agenda():
    """Lista a agenda do pastor logado"""
    try:
        # Filtros
        mes = request.args.get('mes', type=int)
        ano = request.args.get('ano', type=int)
        status = request.args.get('status', '')
        tipo = request.args.get('tipo', '')
        
        # Data atual se não especificado
        hoje = date.today()
        mes = mes or hoje.month
        ano = ano or hoje.year
        
        # Query base - apenas atividades do usuário logado
        query = AgendaPastoral.query.filter_by(usuario_id=current_user.id)
        
        # Filtros
        if status:
            query = query.filter_by(status=status)
        if tipo:
            query = query.filter_by(tipo_atividade=tipo)
        
        # Filtro por mês/ano
        data_inicio = date(ano, mes, 1)
        if mes == 12:
            data_fim = date(ano + 1, 1, 1) - timedelta(days=1)
        else:
            data_fim = date(ano, mes + 1, 1) - timedelta(days=1)
        
        query = query.filter(AgendaPastoral.data >= data_inicio, AgendaPastoral.data <= data_fim)
        
        # Ordenar por data e hora
        atividades = query.order_by(AgendaPastoral.data, AgendaPastoral.hora_inicio).all()
        
        # Estatísticas
        total = len(atividades)
        concluidas = sum(1 for a in atividades if a.concluida)
        pendentes = total - concluidas
        
        return render_template('agenda_pastoral/lista_agenda.html',
                             atividades=atividades,
                             mes=mes,
                             ano=ano,
                             status_filtro=status,
                             tipo_filtro=tipo,
                             total=total,
                             concluidas=concluidas,
                             pendentes=pendentes)
    except Exception as e:
        print(f"[ERRO] Erro ao carregar agenda: {str(e)}")
        import traceback
        traceback.print_exc()
        flash(f'Erro ao carregar agenda: {str(e)}', 'danger')
        # Retornar com valores padrão
        hoje = date.today()
        return render_template('agenda_pastoral/lista_agenda.html', 
                             atividades=[], 
                             mes=hoje.month,
                             ano=hoje.year,
                             status_filtro='',
                             tipo_filtro='',
                             total=0,
                             concluidas=0,
                             pendentes=0)

@agenda_pastoral_bp.route('/agenda-pastoral/nova', methods=['GET', 'POST'])
@login_required
def nova_atividade():
    """Criar nova atividade na agenda"""
    if request.method == 'POST':
        try:
            titulo = request.form.get('titulo', '').strip()
            descricao = request.form.get('descricao', '').strip()
            data_str = request.form.get('data')
            hora_inicio_str = request.form.get('hora_inicio', '').strip()
            hora_fim_str = request.form.get('hora_fim', '').strip()
            local = request.form.get('local', '').strip()
            tipo_atividade = request.form.get('tipo_atividade', '').strip()
            prioridade = request.form.get('prioridade', 'Normal')
            status = request.form.get('status', 'Pendente')
            observacoes = request.form.get('observacoes', '').strip()
            
            # Validação
            if not titulo or not data_str:
                flash('Título e data são obrigatórios!', 'danger')
                return redirect(url_for('agenda_pastoral.nova_atividade'))
            
            # Converter data
            data_atividade = datetime.strptime(data_str, '%Y-%m-%d').date()
            
            # Converter horas
            hora_inicio = None
            hora_fim = None
            if hora_inicio_str:
                hora_inicio = datetime.strptime(hora_inicio_str, '%H:%M').time()
            if hora_fim_str:
                hora_fim = datetime.strptime(hora_fim_str, '%H:%M').time()
            
            # Criar atividade
            nova = AgendaPastoral(
                usuario_id=current_user.id,
                titulo=titulo,
                descricao=descricao if descricao else None,
                data=data_atividade,
                hora_inicio=hora_inicio,
                hora_fim=hora_fim,
                local=local if local else None,
                tipo_atividade=tipo_atividade if tipo_atividade else None,
                prioridade=prioridade,
                status=status,
                observacoes=observacoes if observacoes else None
            )
            
            db.session.add(nova)
            db.session.commit()
            
            flash('Atividade adicionada com sucesso!', 'success')
            return redirect(url_for('agenda_pastoral.lista_agenda'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao adicionar atividade: {str(e)}', 'danger')
    
    return render_template('agenda_pastoral/cadastro_atividade.html')

@agenda_pastoral_bp.route('/agenda-pastoral/<int:id>/editar', methods=['GET', 'POST'])
@login_required
def editar_atividade(id):
    """Editar atividade existente"""
    atividade = AgendaPastoral.query.filter_by(id=id, usuario_id=current_user.id).first_or_404()
    
    if request.method == 'POST':
        try:
            atividade.titulo = request.form.get('titulo', '').strip()
            atividade.descricao = request.form.get('descricao', '').strip() or None
            
            data_str = request.form.get('data')
            atividade.data = datetime.strptime(data_str, '%Y-%m-%d').date()
            
            hora_inicio_str = request.form.get('hora_inicio', '').strip()
            hora_fim_str = request.form.get('hora_fim', '').strip()
            
            atividade.hora_inicio = datetime.strptime(hora_inicio_str, '%H:%M').time() if hora_inicio_str else None
            atividade.hora_fim = datetime.strptime(hora_fim_str, '%H:%M').time() if hora_fim_str else None
            
            atividade.local = request.form.get('local', '').strip() or None
            atividade.tipo_atividade = request.form.get('tipo_atividade', '').strip() or None
            atividade.prioridade = request.form.get('prioridade', 'Normal')
            atividade.status = request.form.get('status', 'Pendente')
            atividade.observacoes = request.form.get('observacoes', '').strip() or None
            
            db.session.commit()
            flash('Atividade atualizada com sucesso!', 'success')
            return redirect(url_for('agenda_pastoral.lista_agenda'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao atualizar atividade: {str(e)}', 'danger')
    
    return render_template('agenda_pastoral/cadastro_atividade.html', atividade=atividade)

@agenda_pastoral_bp.route('/agenda-pastoral/<int:id>/excluir', methods=['POST'])
@login_required
def excluir_atividade(id):
    """Excluir atividade"""
    try:
        atividade = AgendaPastoral.query.filter_by(id=id, usuario_id=current_user.id).first_or_404()
        
        db.session.delete(atividade)
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Atividade excluída com sucesso!'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500

@agenda_pastoral_bp.route('/agenda-pastoral/<int:id>/concluir', methods=['POST'])
@login_required
def concluir_atividade(id):
    """Marcar atividade como concluída"""
    try:
        atividade = AgendaPastoral.query.filter_by(id=id, usuario_id=current_user.id).first_or_404()
        
        atividade.concluida = not atividade.concluida
        atividade.status = 'Concluída' if atividade.concluida else 'Pendente'
        atividade.data_conclusao = datetime.now() if atividade.concluida else None
        
        db.session.commit()
        
        return jsonify({
            'success': True, 
            'concluida': atividade.concluida,
            'message': 'Atividade concluída!' if atividade.concluida else 'Atividade reaberta!'
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500

@agenda_pastoral_bp.route('/agenda-pastoral/hoje')
@login_required
def atividades_hoje():
    """Atividades do dia atual"""
    hoje = date.today()
    atividades = AgendaPastoral.query.filter_by(
        usuario_id=current_user.id,
        data=hoje
    ).order_by(AgendaPastoral.hora_inicio).all()
    
    return render_template('agenda_pastoral/atividades_dia.html', 
                         atividades=atividades,
                         data=hoje)
