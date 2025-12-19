#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Rotas de Eventos - Sistema OBPC
Igreja O Brasil para Cristo - Tietê/SP

Rotas para gerenciamento de eventos da igreja
"""

from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app, jsonify
from flask_login import login_required
from app.extensoes import db
from app.eventos.eventos_model import Evento

# Criar blueprint
eventos_bp = Blueprint('eventos', __name__, url_prefix='/eventos', 
                      template_folder='templates')


@eventos_bp.route('/')
@login_required
def lista_eventos():
    """Lista todos os eventos ordenados por data de início (mais recentes primeiro)"""
    try:
        # Buscar todos os eventos ordenados por data
        eventos = Evento.query.order_by(Evento.data_inicio.desc()).all()
        
        # Estatísticas para o dashboard
        total_eventos = len(eventos)
        eventos_agendados = len([e for e in eventos if e.status == 'Agendado'])
        eventos_concluidos = len([e for e in eventos if e.status == 'Concluído'])
        eventos_cancelados = len([e for e in eventos if e.status == 'Cancelado'])
        
        # Próximos eventos
        proximos_eventos = Evento.eventos_proximos(3)
        
        # Eventos do mês atual
        eventos_mes = Evento.eventos_mes_atual()
        
        estatisticas = {
            'total': total_eventos,
            'agendados': eventos_agendados,
            'concluidos': eventos_concluidos,
            'cancelados': eventos_cancelados,
            'proximos': len(proximos_eventos),
            'mes_atual': len(eventos_mes)
        }
        
        return render_template('eventos/lista_eventos.html', 
                             eventos=eventos,
                             estatisticas=estatisticas,
                             proximos_eventos=proximos_eventos)
        
    except Exception as e:
        current_app.logger.error(f'Erro ao listar eventos: {str(e)}')
        flash('Erro ao carregar lista de eventos', 'danger')
        return render_template('eventos/lista_eventos.html', eventos=[], estatisticas={})


@eventos_bp.route('/novo')
@login_required
def novo_evento():
    """Formulário para cadastro de novo evento"""
    return render_template('eventos/cadastro_evento.html', evento=None)


@eventos_bp.route('/salvar', methods=['POST'])
@login_required
def salvar_evento():
    """Salva novo evento ou atualiza existente"""
    try:
        # Capturar dados do formulário
        evento_id = request.form.get('evento_id')
        titulo = request.form.get('titulo', '').strip()
        descricao = request.form.get('descricao', '').strip()
        data_inicio = request.form.get('data_inicio')
        hora_inicio = request.form.get('hora_inicio')
        data_fim = request.form.get('data_fim')
        hora_fim = request.form.get('hora_fim')
        local = request.form.get('local', '').strip()
        responsavel = request.form.get('responsavel', '').strip()
        status = request.form.get('status', 'Agendado')
        
        # Validações
        if not titulo:
            flash('Título é obrigatório', 'danger')
            return redirect(url_for('eventos.novo_evento'))
        
        if not data_inicio or not hora_inicio:
            flash('Data e hora de início são obrigatórias', 'danger')
            return redirect(url_for('eventos.novo_evento'))
        
        # Combinar data e hora em datetime
        try:
            data_inicio_str = f"{data_inicio} {hora_inicio}"
            data_inicio_dt = datetime.strptime(data_inicio_str, '%Y-%m-%d %H:%M')
            
            # Data/hora fim é opcional
            data_fim_dt = None
            if data_fim and hora_fim:
                data_fim_str = f"{data_fim} {hora_fim}"
                data_fim_dt = datetime.strptime(data_fim_str, '%Y-%m-%d %H:%M')
                
                # Validar se data fim é posterior à data início
                if data_fim_dt <= data_inicio_dt:
                    flash('Data/hora de fim deve ser posterior à data/hora de início', 'danger')
                    return redirect(url_for('eventos.novo_evento'))
            elif data_fim and not hora_fim:
                # Se só tem data fim, usar horário do início
                data_fim_str = f"{data_fim} {hora_inicio}"
                data_fim_dt = datetime.strptime(data_fim_str, '%Y-%m-%d %H:%M')
            elif not data_fim and hora_fim:
                # Se só tem hora fim, usar data do início
                data_fim_str = f"{data_inicio} {hora_fim}"
                data_fim_dt = datetime.strptime(data_fim_str, '%Y-%m-%d %H:%M')
                
        except ValueError:
            flash('Formato de data/hora inválido', 'danger')
            return redirect(url_for('eventos.novo_evento'))
        
        # Criar ou atualizar evento
        if evento_id:
            # Atualizar evento existente
            evento = Evento.query.get_or_404(int(evento_id))
            evento.titulo = titulo
            evento.descricao = descricao
            evento.data_inicio = data_inicio_dt
            evento.data_fim = data_fim_dt
            evento.local = local
            evento.responsavel = responsavel
            evento.status = status
            
            db.session.commit()
            flash(f'Evento "{titulo}" atualizado com sucesso!', 'success')
            
        else:
            # Criar novo evento
            novo_evento = Evento(
                titulo=titulo,
                descricao=descricao,
                data_inicio=data_inicio_dt,
                data_fim=data_fim_dt,
                local=local,
                responsavel=responsavel,
                status=status
            )
            
            db.session.add(novo_evento)
            db.session.commit()
            flash(f'Evento "{titulo}" cadastrado com sucesso!', 'success')
        
        return redirect(url_for('eventos.lista_eventos'))
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'Erro ao salvar evento: {str(e)}')
        flash('Erro ao salvar evento. Tente novamente.', 'danger')
        return redirect(url_for('eventos.novo_evento'))


@eventos_bp.route('/editar/<int:evento_id>')
@login_required
def editar_evento(evento_id):
    """Formulário para edição de evento existente"""
    try:
        evento = Evento.query.get_or_404(evento_id)
        return render_template('eventos/cadastro_evento.html', evento=evento)
        
    except Exception as e:
        current_app.logger.error(f'Erro ao carregar evento para edição: {str(e)}')
        flash('Evento não encontrado', 'danger')
        return redirect(url_for('eventos.lista_eventos'))


@eventos_bp.route('/excluir/<int:evento_id>')
@login_required
def excluir_evento(evento_id):
    """Exclui evento"""
    try:
        evento = Evento.query.get_or_404(evento_id)
        titulo = evento.titulo
        
        db.session.delete(evento)
        db.session.commit()
        
        flash(f'Evento "{titulo}" excluído com sucesso!', 'success')
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'Erro ao excluir evento: {str(e)}')
        flash('Erro ao excluir evento', 'danger')
    
    return redirect(url_for('eventos.lista_eventos'))


@eventos_bp.route('/detalhes/<int:evento_id>')
@login_required
def detalhes_evento(evento_id):
    """Visualiza detalhes completos do evento"""
    try:
        evento = Evento.query.get_or_404(evento_id)
        return render_template('eventos/detalhes_evento.html', evento=evento)
        
    except Exception as e:
        current_app.logger.error(f'Erro ao carregar detalhes do evento: {str(e)}')
        flash('Evento não encontrado', 'danger')
        return redirect(url_for('eventos.lista_eventos'))


@eventos_bp.route('/calendario')
@login_required
def calendario_eventos():
    """Visualização em calendário dos eventos"""
    try:
        return render_template('eventos/calendario_eventos.html')
        
    except Exception as e:
        current_app.logger.error(f'Erro ao carregar calendário: {str(e)}')
        flash('Erro ao carregar calendário de eventos', 'danger')
        return redirect(url_for('eventos.lista_eventos'))


@eventos_bp.route('/api/calendario')
@login_required
def api_eventos_calendario():
    """API para fornecer eventos em formato JSON para o calendário"""
    try:
        eventos = Evento.query.all()
        eventos_json = []
        
        for evento in eventos:
            eventos_json.append({
                'id': evento.id,
                'title': evento.titulo,
                'start': evento.data_inicio.isoformat(),
                'end': evento.data_fim.isoformat() if evento.data_fim else None,
                'extendedProps': {
                    'descricao': evento.descricao or '',
                    'local': evento.local or '',
                    'responsavel': evento.responsavel or '',
                    'status': evento.status
                }
            })
        
        return jsonify(eventos_json)
        
    except Exception as e:
        current_app.logger.error(f'Erro na API do calendário: {str(e)}')
        return jsonify({'error': 'Erro ao carregar eventos'}), 500