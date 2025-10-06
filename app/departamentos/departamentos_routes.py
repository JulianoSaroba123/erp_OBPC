from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required
from app.extensoes import db
from app.departamentos.departamentos_model import Departamento

departamentos_bp = Blueprint('departamentos', __name__, template_folder='templates')

@departamentos_bp.route('/departamentos')
@login_required
def lista_departamentos():
    """Lista todos os departamentos cadastrados"""
    try:
        departamentos = Departamento.query.order_by(Departamento.nome.asc()).all()
        return render_template('departamentos/lista_departamentos.html', departamentos=departamentos)
    except Exception as e:
        flash(f'Erro ao carregar lista de departamentos: {str(e)}', 'danger')
        return render_template('departamentos/lista_departamentos.html', departamentos=[])

@departamentos_bp.route('/departamentos/novo')
@login_required
def novo_departamento():
    """Exibe formulário para cadastro de novo departamento"""
    return render_template('departamentos/cadastro_departamento.html')

@departamentos_bp.route('/departamentos/salvar', methods=['POST'])
@login_required
def salvar_departamento():
    """Salva novo departamento ou atualiza departamento existente"""
    try:
        # Captura dados do formulário
        departamento_id = request.form.get('id')
        nome = request.form.get('nome', '').strip()
        lider = request.form.get('lider', '').strip()
        vice_lider = request.form.get('vice_lider', '').strip()
        descricao = request.form.get('descricao', '').strip()
        contato = request.form.get('contato', '').strip()
        status = request.form.get('status', 'Ativo')
        
        # Validação básica
        if not nome:
            flash('Nome do departamento é obrigatório!', 'danger')
            return redirect(url_for('departamentos.novo_departamento'))
        
        if departamento_id:
            # Atualizar departamento existente
            departamento = Departamento.query.get_or_404(departamento_id)
            departamento.nome = nome
            departamento.lider = lider if lider else None
            departamento.vice_lider = vice_lider if vice_lider else None
            departamento.descricao = descricao if descricao else None
            departamento.contato = contato if contato else None
            departamento.status = status
            
            flash('Departamento atualizado com sucesso!', 'success')
        else:
            # Verificar se já existe departamento com o mesmo nome
            departamento_existente = Departamento.query.filter_by(nome=nome).first()
            if departamento_existente:
                flash('Já existe um departamento com este nome!', 'danger')
                return redirect(url_for('departamentos.novo_departamento'))
            
            # Criar novo departamento
            novo_departamento = Departamento(
                nome=nome,
                lider=lider if lider else None,
                vice_lider=vice_lider if vice_lider else None,
                descricao=descricao if descricao else None,
                contato=contato if contato else None,
                status=status
            )
            
            db.session.add(novo_departamento)
            flash('Departamento cadastrado com sucesso!', 'success')
        
        db.session.commit()
        return redirect(url_for('departamentos.lista_departamentos'))
        
    except Exception as e:
        db.session.rollback()
        flash(f'Erro ao salvar departamento: {str(e)}', 'danger')
        return redirect(url_for('departamentos.novo_departamento'))

@departamentos_bp.route('/departamentos/editar/<int:id>')
@login_required
def editar_departamento(id):
    """Carrega dados do departamento para edição"""
    try:
        departamento = Departamento.query.get_or_404(id)
        return render_template('departamentos/cadastro_departamento.html', departamento=departamento)
    except Exception as e:
        flash(f'Erro ao carregar dados do departamento: {str(e)}', 'danger')
        return redirect(url_for('departamentos.lista_departamentos'))

@departamentos_bp.route('/departamentos/excluir/<int:id>')
@login_required
def excluir_departamento(id):
    """Exclui um departamento"""
    try:
        departamento = Departamento.query.get_or_404(id)
        nome_departamento = departamento.nome
        
        db.session.delete(departamento)
        db.session.commit()
        
        flash(f'Departamento "{nome_departamento}" excluído com sucesso!', 'success')
        
    except Exception as e:
        db.session.rollback()
        flash(f'Erro ao excluir departamento: {str(e)}', 'danger')
    
    return redirect(url_for('departamentos.lista_departamentos'))