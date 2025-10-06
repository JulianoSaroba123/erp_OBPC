from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required
from app.extensoes import db
from app.membros.membros_model import Membro
from datetime import datetime

membros_bp = Blueprint('membros', __name__, template_folder='templates')

@membros_bp.route('/membros')
@login_required
def lista_membros():
    """Lista todos os membros cadastrados"""
    try:
        membros = Membro.query.order_by(Membro.nome.asc()).all()
        return render_template('membros/lista_membros.html', membros=membros)
    except Exception as e:
        flash(f'Erro ao carregar lista de membros: {str(e)}', 'danger')
        return render_template('membros/lista_membros.html', membros=[])

@membros_bp.route('/membros/novo')
@login_required
def novo_membro():
    """Exibe formulário para cadastro de novo membro"""
    return render_template('membros/cadastro_membro.html')

@membros_bp.route('/membros/salvar', methods=['POST'])
@login_required
def salvar_membro():
    """Salva novo membro ou atualiza membro existente"""
    try:
        # Captura dados do formulário
        membro_id = request.form.get('id')
        nome = request.form.get('nome', '').strip()
        telefone = request.form.get('telefone', '').strip()
        email = request.form.get('email', '').strip()
        endereco = request.form.get('endereco', '').strip()
        cidade = request.form.get('cidade', '').strip()
        estado = request.form.get('estado', '').strip()
        cep = request.form.get('cep', '').strip()
        data_nascimento = request.form.get('data_nascimento')
        data_batismo = request.form.get('data_batismo')
        status = request.form.get('status', 'Ativo')
        observacoes = request.form.get('observacoes', '').strip()
        
        # Validação básica
        if not nome:
            flash('Nome é obrigatório!', 'danger')
            return redirect(url_for('membros.novo_membro'))
        
        # Conversão de datas
        data_nasc_obj = None
        data_bat_obj = None
        
        if data_nascimento:
            try:
                data_nasc_obj = datetime.strptime(data_nascimento, '%Y-%m-%d').date()
            except ValueError:
                flash('Data de nascimento inválida!', 'danger')
                return redirect(url_for('membros.novo_membro'))
        
        if data_batismo:
            try:
                data_bat_obj = datetime.strptime(data_batismo, '%Y-%m-%d').date()
            except ValueError:
                flash('Data de batismo inválida!', 'danger')
                return redirect(url_for('membros.novo_membro'))
        
        if membro_id:
            # Atualizar membro existente
            membro = Membro.query.get_or_404(membro_id)
            membro.nome = nome
            membro.telefone = telefone if telefone else None
            membro.email = email if email else None
            membro.endereco = endereco if endereco else None
            membro.cidade = cidade if cidade else None
            membro.estado = estado if estado else None
            membro.cep = cep if cep else None
            membro.data_nascimento = data_nasc_obj
            membro.data_batismo = data_bat_obj
            membro.status = status
            membro.observacoes = observacoes if observacoes else None
            
            flash('Membro atualizado com sucesso!', 'success')
        else:
            # Criar novo membro
            novo_membro = Membro(
                nome=nome,
                telefone=telefone if telefone else None,
                email=email if email else None,
                endereco=endereco if endereco else None,
                cidade=cidade if cidade else None,
                estado=estado if estado else None,
                cep=cep if cep else None,
                data_nascimento=data_nasc_obj,
                data_batismo=data_bat_obj,
                status=status,
                observacoes=observacoes if observacoes else None
            )
            
            db.session.add(novo_membro)
            flash('Membro cadastrado com sucesso!', 'success')
        
        db.session.commit()
        return redirect(url_for('membros.lista_membros'))
        
    except Exception as e:
        db.session.rollback()
        flash(f'Erro ao salvar membro: {str(e)}', 'danger')
        return redirect(url_for('membros.novo_membro'))

@membros_bp.route('/membros/editar/<int:id>')
@login_required
def editar_membro(id):
    """Carrega dados do membro para edição"""
    try:
        membro = Membro.query.get_or_404(id)
        return render_template('membros/cadastro_membro.html', membro=membro)
    except Exception as e:
        flash(f'Erro ao carregar dados do membro: {str(e)}', 'danger')
        return redirect(url_for('membros.lista_membros'))

@membros_bp.route('/membros/excluir/<int:id>')
@login_required
def excluir_membro(id):
    """Exclui um membro"""
    try:
        membro = Membro.query.get_or_404(id)
        nome_membro = membro.nome
        
        db.session.delete(membro)
        db.session.commit()
        
        flash(f'Membro "{nome_membro}" excluído com sucesso!', 'success')
        
    except Exception as e:
        db.session.rollback()
        flash(f'Erro ao excluir membro: {str(e)}', 'danger')
    
    return redirect(url_for('membros.lista_membros'))