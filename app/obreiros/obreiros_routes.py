from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required
from app.extensoes import db
from app.obreiros.obreiros_model import Obreiro
from datetime import datetime

obreiros_bp = Blueprint('obreiros', __name__, template_folder='templates')

@obreiros_bp.route('/obreiros')
@login_required
def lista_obreiros():
    """Lista todos os obreiros cadastrados"""
    try:
        obreiros = Obreiro.query.order_by(Obreiro.nome.asc()).all()
        return render_template('obreiros/lista_obreiros.html', obreiros=obreiros)
    except Exception as e:
        flash(f'Erro ao carregar lista de obreiros: {str(e)}', 'danger')
        return render_template('obreiros/lista_obreiros.html', obreiros=[])

@obreiros_bp.route('/obreiros/novo')
@login_required
def novo_obreiro():
    """Exibe formulário para cadastro de novo obreiro"""
    return render_template('obreiros/cadastro_obreiro.html')

@obreiros_bp.route('/obreiros/salvar', methods=['POST'])
@login_required
def salvar_obreiro():
    """Salva novo obreiro ou atualiza obreiro existente"""
    try:
        # Captura dados do formulário
        obreiro_id = request.form.get('id')
        nome = request.form.get('nome', '').strip()
        telefone = request.form.get('telefone', '').strip()
        email = request.form.get('email', '').strip()
        funcao = request.form.get('funcao', '').strip()
        data_consagracao = request.form.get('data_consagracao')
        status = request.form.get('status', 'Ativo')
        observacoes = request.form.get('observacoes', '').strip()
        
        # Validação básica
        if not nome:
            flash('Nome é obrigatório!', 'danger')
            return redirect(url_for('obreiros.novo_obreiro'))
        
        # Conversão da data de consagração
        data_consag_obj = None
        if data_consagracao:
            try:
                data_consag_obj = datetime.strptime(data_consagracao, '%Y-%m-%d').date()
            except ValueError:
                flash('Data de consagração inválida!', 'danger')
                return redirect(url_for('obreiros.novo_obreiro'))
        
        if obreiro_id:
            # Atualizar obreiro existente
            obreiro = Obreiro.query.get_or_404(obreiro_id)
            obreiro.nome = nome
            obreiro.telefone = telefone if telefone else None
            obreiro.email = email if email else None
            obreiro.funcao = funcao if funcao else None
            obreiro.data_consagracao = data_consag_obj
            obreiro.status = status
            obreiro.observacoes = observacoes if observacoes else None
            
            flash('Obreiro atualizado com sucesso!', 'success')
        else:
            # Criar novo obreiro
            novo_obreiro = Obreiro(
                nome=nome,
                telefone=telefone if telefone else None,
                email=email if email else None,
                funcao=funcao if funcao else None,
                data_consagracao=data_consag_obj,
                status=status,
                observacoes=observacoes if observacoes else None
            )
            
            db.session.add(novo_obreiro)
            flash('Obreiro cadastrado com sucesso!', 'success')
        
        db.session.commit()
        return redirect(url_for('obreiros.lista_obreiros'))
        
    except Exception as e:
        db.session.rollback()
        flash(f'Erro ao salvar obreiro: {str(e)}', 'danger')
        return redirect(url_for('obreiros.novo_obreiro'))

@obreiros_bp.route('/obreiros/editar/<int:id>')
@login_required
def editar_obreiro(id):
    """Carrega dados do obreiro para edição"""
    try:
        obreiro = Obreiro.query.get_or_404(id)
        return render_template('obreiros/cadastro_obreiro.html', obreiro=obreiro)
    except Exception as e:
        flash(f'Erro ao carregar dados do obreiro: {str(e)}', 'danger')
        return redirect(url_for('obreiros.lista_obreiros'))

@obreiros_bp.route('/obreiros/excluir/<int:id>')
@login_required
def excluir_obreiro(id):
    """Exclui um obreiro"""
    try:
        obreiro = Obreiro.query.get_or_404(id)
        nome_obreiro = obreiro.nome
        
        db.session.delete(obreiro)
        db.session.commit()
        
        flash(f'Obreiro "{nome_obreiro}" excluído com sucesso!', 'success')
        
    except Exception as e:
        db.session.rollback()
        flash(f'Erro ao excluir obreiro: {str(e)}', 'danger')
    
    return redirect(url_for('obreiros.lista_obreiros'))