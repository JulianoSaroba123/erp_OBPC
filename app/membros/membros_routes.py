from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required
from app.extensoes import db
from app.membros.membros_model import Membro
from datetime import datetime

membros_bp = Blueprint('membros', __name__, template_folder='templates')

@membros_bp.route('/membros')
@login_required
def lista_membros():
    """Lista todos os membros cadastrados com filtros avançados"""
    try:
        # Parâmetros de filtro
        busca = request.args.get('busca', '').strip()
        tipo_filtro = request.args.get('tipo', '').strip()
        
        # Query base
        query = Membro.query
        
        # Aplicar filtro de busca por nome, email ou telefone
        if busca:
            query = query.filter(
                (Membro.nome.ilike(f'%{busca}%')) |
                (Membro.email.ilike(f'%{busca}%')) |
                (Membro.telefone.ilike(f'%{busca}%'))
            )
        
        # Aplicar filtro por tipo
        if tipo_filtro and tipo_filtro != 'Todos':
            query = query.filter(Membro.tipo == tipo_filtro)
        
        # Executar query e ordenar
        membros = query.order_by(Membro.nome.asc()).all()
        
        # Estatísticas para os filtros
        total_membros = Membro.query.count()
        total_obreiros = Membro.query.filter_by(tipo='Obreiro').count()
        total_lideres = Membro.query.filter_by(tipo='Lider').count()
        total_membros_simples = Membro.query.filter_by(tipo='Membro').count()
        
        return render_template('membros/lista_membros.html', 
                             membros=membros,
                             busca=busca,
                             tipo_filtro=tipo_filtro,
                             total_membros=total_membros,
                             total_obreiros=total_obreiros,
                             total_lideres=total_lideres,
                             total_membros_simples=total_membros_simples)
    except Exception as e:
        flash(f'Erro ao carregar lista de membros: {str(e)}', 'danger')
        return render_template('membros/lista_membros.html', membros=[])

@membros_bp.route('/membros/novo')
@login_required
def novo_membro():
    """Exibe formulário para cadastro de novo membro"""
    try:
        # Buscar listas para exibir condicionalmente
        obreiros = Membro.query.filter_by(tipo='Obreiro').order_by(Membro.nome.asc()).all()
        lideres = Membro.query.filter_by(tipo='Lider').order_by(Membro.nome.asc()).all()
        return render_template('membros/cadastro_membro.html', obreiros=obreiros or [], lideres=lideres or [])
    except Exception as e:
        return render_template('membros/cadastro_membro.html', obreiros=[], lideres=[])

@membros_bp.route('/membros/salvar', methods=['POST'])
@login_required
def salvar_membro():
    """Salva novo membro ou atualiza membro existente"""
    try:
        # Captura dados do formulário
        membro_id = request.form.get('id')
        nome = request.form.get('nome', '').strip()
        cpf = request.form.get('cpf', '').strip()
        telefone = request.form.get('telefone', '').strip()
        email = request.form.get('email', '').strip()
        endereco = request.form.get('endereco', '').strip()
        numero = request.form.get('numero', '').strip()
        bairro = request.form.get('bairro', '').strip()
        cidade = request.form.get('cidade', '').strip()
        estado = request.form.get('estado', '').strip()
        cep = request.form.get('cep', '').strip()
        data_nascimento = request.form.get('data_nascimento')
        data_batismo = request.form.get('data_batismo')
        estado_civil = request.form.get('estado_civil', '').strip()
        curso_teologia = request.form.get('curso_teologia') == 'on'  # Checkbox
        nivel_teologia = request.form.get('nivel_teologia', '').strip()
        instituto = request.form.get('instituto', '').strip()
        deseja_servir = request.form.get('deseja_servir') == 'on'  # Checkbox
        area_servir = request.form.get('area_servir', '').strip()
        status = request.form.get('status', 'Ativo')
        tipo = request.form.get('tipo', 'Membro')  # Novo campo tipo
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
            membro.cpf = cpf if cpf else None
            membro.telefone = telefone if telefone else None
            membro.email = email if email else None
            membro.endereco = endereco if endereco else None
            membro.numero = numero if numero else None
            membro.bairro = bairro if bairro else None
            membro.cidade = cidade if cidade else None
            membro.estado = estado if estado else None
            membro.cep = cep if cep else None
            membro.data_nascimento = data_nasc_obj
            membro.data_batismo = data_bat_obj
            membro.estado_civil = estado_civil if estado_civil else None
            membro.curso_teologia = curso_teologia
            membro.nivel_teologia = nivel_teologia if nivel_teologia else None
            membro.instituto = instituto if instituto else None
            membro.deseja_servir = deseja_servir
            membro.area_servir = area_servir if area_servir else None
            membro.status = status
            membro.tipo = tipo  # Atualizar tipo
            membro.observacoes = observacoes if observacoes else None
            
            flash('Membro atualizado com sucesso!', 'success')
        else:
            # Criar novo membro
            novo_membro = Membro(
                nome=nome,
                cpf=cpf if cpf else None,
                telefone=telefone if telefone else None,
                email=email if email else None,
                endereco=endereco if endereco else None,
                numero=numero if numero else None,
                bairro=bairro if bairro else None,
                cidade=cidade if cidade else None,
                estado=estado if estado else None,
                cep=cep if cep else None,
                data_nascimento=data_nasc_obj,
                data_batismo=data_bat_obj,
                estado_civil=estado_civil if estado_civil else None,
                curso_teologia=curso_teologia,
                nivel_teologia=nivel_teologia if nivel_teologia else None,
                instituto=instituto if instituto else None,
                deseja_servir=deseja_servir,
                area_servir=area_servir if area_servir else None,
                status=status,
                tipo=tipo,  # Incluir tipo no novo membro
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
        # Buscar listas para exibir condicionalmente
        obreiros = Membro.query.filter_by(tipo='Obreiro').order_by(Membro.nome.asc()).all()
        lideres = Membro.query.filter_by(tipo='Lider').order_by(Membro.nome.asc()).all()
        return render_template('membros/cadastro_membro.html', membro=membro, obreiros=obreiros or [], lideres=lideres or [])
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

@membros_bp.route('/obreiros')
@login_required
def lista_obreiros():
    """Lista todos os obreiros"""
    try:
        obreiros = Membro.query.filter_by(tipo='Obreiro').order_by(Membro.nome.asc()).all()
        return render_template('membros/lista_obreiros.html', obreiros=obreiros)
    except Exception as e:
        flash(f'Erro ao carregar lista de obreiros: {str(e)}', 'danger')
        return render_template('membros/lista_obreiros.html', obreiros=[])

@membros_bp.route('/lideres')
@login_required
def lista_lideres():
    """Lista todos os líderes de departamento"""
    try:
        lideres = Membro.query.filter_by(tipo='Lider').order_by(Membro.nome.asc()).all()
        return render_template('membros/lista_lideres.html', lideres=lideres)
    except Exception as e:
        flash(f'Erro ao carregar lista de líderes: {str(e)}', 'danger')
        return render_template('membros/lista_lideres.html', lideres=[])