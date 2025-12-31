from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, current_app, send_from_directory
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
import os
import json
from app.extensoes import db
from app.departamentos.departamentos_model import Departamento, CronogramaDepartamento, AulaDepartamento
from datetime import datetime

departamentos_bp = Blueprint('departamentos', __name__, template_folder='templates')

# Configurações para upload de arquivos
ALLOWED_EXTENSIONS = {'pdf', 'doc', 'docx', 'txt', 'jpg', 'jpeg', 'png'}
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB

def allowed_file(filename):
    """Verifica se o arquivo é permitido"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def save_uploaded_file(file, departamento_id):
    """Salva arquivo enviado e retorna o nome do arquivo"""
    if file and allowed_file(file.filename):
        # Criar nome seguro para o arquivo
        filename = secure_filename(file.filename)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        safe_filename = f"dept_{departamento_id}_{timestamp}_{filename}"
        
        # Criar diretório se não existir
        upload_folder = os.path.join(current_app.root_path, 'static', 'uploads', 'aulas')
        os.makedirs(upload_folder, exist_ok=True)
        
        # Salvar arquivo
        file_path = os.path.join(upload_folder, safe_filename)
        file.save(file_path)
        
        return safe_filename
    return None

@departamentos_bp.route('/departamentos')
@login_required  
def lista_departamentos():
    """Lista todos os departamentos cadastrados"""
    try:
        # Forçar refresh da sessão
        db.session.expire_all()
        
        # Verificar se é líder de departamento
        if current_user.eh_lider_departamento():
            # Líder vê apenas seu departamento
            departamentos = Departamento.query.filter_by(id=current_user.departamento_id).all()
            current_app.logger.info(f">>> LÍDER DE DEPARTAMENTO: Mostrando apenas departamento ID {current_user.departamento_id}")
        else:
            # Admin/Master vê todos
            departamentos = Departamento.query.all()
        
        current_app.logger.info(f">>> LISTAGEM: {len(departamentos)} departamentos encontrados")
        
        if len(departamentos) == 0:
            current_app.logger.warning(">>> ATENÇÃO: Nenhum departamento encontrado na query!")
            current_app.logger.info(">>> Tentando query direta com SQL...")
            
            # Tentar query SQL direta para debug
            result = db.session.execute(db.text("SELECT COUNT(*) FROM departamentos"))
            count = result.scalar()
            current_app.logger.info(f">>> SQL direto: {count} departamentos na tabela")
        
        for dep in departamentos:
            current_app.logger.info(f"    - {dep.nome} (ID: {dep.id})")
            
        return render_template('departamentos/lista_departamentos.html', departamentos=departamentos)
    except Exception as e:
        current_app.logger.error(f">>> ERRO ao listar departamentos: {str(e)}")
        import traceback
        traceback.print_exc()
        flash(f'Erro ao carregar departamentos: {str(e)}', 'danger')
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
        current_app.logger.info(">>> Rota salvar_departamento chamada!")
        
        # Captura dados do formulário
        departamento_id = request.form.get('id')
        nome = request.form.get('nome', '').strip()
        lider = request.form.get('lider', '').strip()
        vice_lider = request.form.get('vice_lider', '').strip()
        descricao = request.form.get('descricao', '').strip()
        contato = request.form.get('contato', '').strip()
        status = request.form.get('status', 'Ativo')
        cronograma_mensal = request.form.get('cronograma_mensal', '').strip()
        possui_aulas = bool(request.form.get('possui_aulas'))  # Checkbox retorna valor ou None
        planejamento_aulas = request.form.get('planejamento_aulas', '').strip()
        
        current_app.logger.info(f">>> Dados recebidos - Nome: {nome}, Lider: {lider}, ID: {departamento_id}")
        
        # Validação básica
        if not nome:
            flash('Nome do departamento é obrigatório!', 'danger')
            return redirect(url_for('departamentos.novo_departamento'))
        
        # Validação condicional: se possui aulas, planejamento é recomendado
        if possui_aulas and not planejamento_aulas:
            flash('Recomenda-se preencher o planejamento de aulas para departamentos que oferecem aulas.', 'warning')
        
        if departamento_id:
            # Atualizar departamento existente
            departamento = Departamento.query.get_or_404(departamento_id)
            departamento.nome = nome
            departamento.lider = lider if lider else None
            departamento.vice_lider = vice_lider if vice_lider else None
            departamento.descricao = descricao if descricao else None
            departamento.contato = contato if contato else None
            departamento.status = status
            departamento.cronograma_mensal = cronograma_mensal if cronograma_mensal else None
            departamento.possui_aulas = possui_aulas
            departamento.planejamento_aulas = planejamento_aulas if planejamento_aulas else None
            
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
                status=status,
                cronograma_mensal=cronograma_mensal if cronograma_mensal else None,
                possui_aulas=possui_aulas,
                planejamento_aulas=planejamento_aulas if planejamento_aulas else None
            )
            
            db.session.add(novo_departamento)
            db.session.flush()  # Gera o ID antes do commit
            departamento_id = novo_departamento.id
            flash('Departamento cadastrado com sucesso!', 'success')
            current_app.logger.info(f">>> Novo departamento criado: {nome} (ID: {departamento_id})")
        
        db.session.commit()
        current_app.logger.info(">>> Departamento salvo no banco com sucesso!")
        
        # Se há dados de cronogramas/aulas enviados via JSON, salvar
        if request.is_json:
            dept_id = departamento_id if not request.form.get('id') else request.form.get('id')
            return jsonify({'sucesso': True, 'departamento_id': dept_id})
        
        return redirect(url_for('departamentos.lista_departamentos'))
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f">>> ERRO ao salvar departamento: {str(e)}")
        import traceback
        traceback.print_exc()
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


# ============================================================================
# ROTAS PARA CRONOGRAMAS DE DEPARTAMENTOS
# ============================================================================

@departamentos_bp.route('/departamentos/<int:departamento_id>/cronogramas/listar')
@login_required
def listar_cronogramas_json(departamento_id):
    """Lista cronogramas de um departamento em formato JSON"""
    try:
        cronogramas = CronogramaDepartamento.query.filter_by(
            departamento_id=departamento_id, 
            ativo=True
        ).order_by(CronogramaDepartamento.data_evento.asc()).all()
        
        cronogramas_list = []
        for c in cronogramas:
            cronogramas_list.append({
                'id': c.id,
                'titulo': c.titulo,
                'descricao': c.descricao or '',
                'data_evento': c.data_evento.strftime('%d/%m/%Y'),
                'horario': c.horario or '',
                'local': c.local or '',
                'responsavel': c.responsavel or '',
                'exibir_no_painel': c.exibir_no_painel
            })
        
        return jsonify({'cronogramas': cronogramas_list})
        
    except Exception as e:
        return jsonify({'erro': str(e)}), 500

@departamentos_bp.route('/departamentos/<int:departamento_id>/cronogramas')
@login_required
def listar_cronogramas(departamento_id):
    """Lista cronogramas de um departamento"""
    try:
        departamento = Departamento.query.get_or_404(departamento_id)
        cronogramas = CronogramaDepartamento.query.filter_by(
            departamento_id=departamento_id, 
            ativo=True
        ).order_by(CronogramaDepartamento.data_evento.asc()).all()
        
        return render_template('departamentos/cronogramas.html', 
                             departamento=departamento, 
                             cronogramas=cronogramas)
    except Exception as e:
        flash(f'Erro ao carregar cronogramas: {str(e)}', 'danger')
        return redirect(url_for('departamentos.lista_departamentos'))

@departamentos_bp.route('/departamentos/<int:departamento_id>/cronogramas/adicionar', methods=['POST'])
@login_required
def adicionar_cronograma(departamento_id):
    """Adiciona cronograma via AJAX"""
    try:
        data = request.get_json()
        
        # Validar dados
        if not data.get('titulo') or not data.get('data_evento'):
            return jsonify({'erro': 'Título e data são obrigatórios'}), 400
        
        # Converter data
        data_evento = datetime.strptime(data['data_evento'], '%Y-%m-%d').date()
        
        # Criar cronograma
        cronograma = CronogramaDepartamento(
            departamento_id=departamento_id,
            data_evento=data_evento,
            titulo=data['titulo'],
            descricao=data.get('descricao', ''),
            horario=data.get('horario', ''),
            local=data.get('local', ''),
            responsavel=data.get('responsavel', ''),
            exibir_no_painel=data.get('exibir_no_painel', False)
        )
        
        db.session.add(cronograma)
        db.session.commit()
        
        return jsonify({
            'sucesso': True,
            'cronograma': {
                'id': cronograma.id,
                'titulo': cronograma.titulo,
                'data_formatada': cronograma.data_formatada,
                'descricao': cronograma.descricao,
                'horario': cronograma.horario,
                'local': cronograma.local,
                'responsavel': cronograma.responsavel,
                'exibir_no_painel': cronograma.exibir_no_painel
            }
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'erro': str(e)}), 500

@departamentos_bp.route('/cronogramas/<int:cronograma_id>/excluir', methods=['DELETE'])
@login_required
def excluir_cronograma(cronograma_id):
    """Exclui cronograma via AJAX"""
    try:
        cronograma = CronogramaDepartamento.query.get_or_404(cronograma_id)
        db.session.delete(cronograma)
        db.session.commit()
        
        return jsonify({'sucesso': True})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'erro': str(e)}), 500


# ============================================================================
# ROTAS PARA AULAS DE DEPARTAMENTOS  
# ============================================================================

@departamentos_bp.route('/departamentos/<int:departamento_id>/aulas/listar')
@login_required
def listar_aulas_json(departamento_id):
    """Lista aulas de um departamento em formato JSON"""
    try:
        aulas = AulaDepartamento.query.filter_by(
            departamento_id=departamento_id,
            ativo=True
        ).order_by(AulaDepartamento.data_inicio.desc()).all()
        
        aulas_list = []
        for a in aulas:
            aulas_list.append({
                'id': a.id,
                'titulo': a.titulo,
                'descricao': a.descricao or '',
                'professora': a.professora or '',
                'dia_semana': a.dia_semana or '',
                'horario': a.horario or '',
                'local': a.local or '',
                'max_alunos': a.max_alunos,
                'data_inicio': a.data_inicio.strftime('%d/%m/%Y') if a.data_inicio else '',
                'data_fim': a.data_fim.strftime('%d/%m/%Y') if a.data_fim else ''
            })
        
        return jsonify({'aulas': aulas_list})
        
    except Exception as e:
        return jsonify({'erro': str(e)}), 500

@departamentos_bp.route('/departamentos/<int:departamento_id>/aulas')
@login_required
def listar_aulas(departamento_id):
    """Lista aulas de um departamento"""
    try:
        departamento = Departamento.query.get_or_404(departamento_id)
        aulas = AulaDepartamento.query.filter_by(
            departamento_id=departamento_id,
            ativo=True
        ).order_by(AulaDepartamento.data_inicio.desc()).all()
        
        return render_template('departamentos/aulas.html',
                             departamento=departamento,
                             aulas=aulas)
    except Exception as e:
        flash(f'Erro ao carregar aulas: {str(e)}', 'danger')
        return redirect(url_for('departamentos.lista_departamentos'))

@departamentos_bp.route('/departamentos/<int:departamento_id>/aulas/adicionar', methods=['POST'])
@login_required
def adicionar_aula(departamento_id):
    """Adiciona aula via AJAX ou formulário"""
    try:
        # Verificar se é requisição AJAX (JSON) ou formulário
        if request.is_json:
            # Requisição AJAX - sem arquivo
            data = request.get_json()
            arquivo_nome = None
        else:
            # Requisição de formulário - com possível arquivo
            data = request.form.to_dict()
            
            # Processar arquivo se enviado
            arquivo_nome = None
            if 'arquivo' in request.files:
                file = request.files['arquivo']
                if file and file.filename:
                    arquivo_nome = save_uploaded_file(file, departamento_id)
        
        # Validar dados
        if not data.get('titulo'):
            if request.is_json:
                return jsonify({'erro': 'Título é obrigatório'}), 400
            else:
                flash('Título da aula é obrigatório!', 'danger')
                return redirect(url_for('departamentos.editar_departamento', id=departamento_id))
        
        # Converter datas se fornecidas
        data_inicio = None
        data_fim = None
        
        if data.get('data_inicio'):
            data_inicio = datetime.strptime(data['data_inicio'], '%Y-%m-%d').date()
        if data.get('data_fim'):
            data_fim = datetime.strptime(data['data_fim'], '%Y-%m-%d').date()
        
        # Criar aula
        aula = AulaDepartamento(
            departamento_id=departamento_id,
            titulo=data['titulo'],
            descricao=data.get('descricao', ''),
            professora=data.get('professora', ''),
            dia_semana=data.get('dia_semana', ''),
            horario=data.get('horario', ''),
            local=data.get('local', ''),
            data_inicio=data_inicio,
            data_fim=data_fim,
            max_alunos=int(data['max_alunos']) if data.get('max_alunos') else None,
            material_necessario=data.get('material_necessario', ''),
            arquivo_anexo=arquivo_nome,  # Novo campo
            exibir_no_painel=data.get('exibir_no_painel', False)
        )
        
        db.session.add(aula)
        db.session.commit()
        
        if request.is_json:
            return jsonify({
                'sucesso': True,
                'aula': {
                    'id': aula.id,
                    'titulo': aula.titulo,
                    'professora': aula.professora,
                    'dia_semana': aula.dia_semana,
                    'horario': aula.horario,
                    'local': aula.local,
                    'duracao_formatada': aula.duracao_formatada,
                    'arquivo_anexo': aula.arquivo_anexo,
                    'exibir_no_painel': aula.exibir_no_painel
                }
            })
        else:
            flash(f'Aula "{aula.titulo}" adicionada com sucesso!', 'success')
            return redirect(url_for('departamentos.editar_departamento', id=departamento_id))
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'erro': str(e)}), 500

@departamentos_bp.route('/aulas/<int:aula_id>/excluir', methods=['DELETE'])
@login_required
def excluir_aula(aula_id):
    """Exclui aula via AJAX"""
    try:
        aula = AulaDepartamento.query.get_or_404(aula_id)
        db.session.delete(aula)
        db.session.commit()
        
        return jsonify({'sucesso': True})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'erro': str(e)}), 500


# ============================================================================
# ROTAS PARA PAINEL DE DASHBOARD
# ============================================================================

@departamentos_bp.route('/api/cronogramas-painel')
@login_required
def cronogramas_painel():
    """API para buscar cronogramas que devem aparecer no painel"""
    try:
        from datetime import timedelta
        
        # Buscar cronogramas dos próximos 30 dias que devem aparecer no painel
        hoje = datetime.now().date()
        limite = hoje + timedelta(days=30)
        
        cronogramas = db.session.query(CronogramaDepartamento).\
            join(Departamento).\
            filter(
                CronogramaDepartamento.exibir_no_painel == True,
                CronogramaDepartamento.ativo == True,
                CronogramaDepartamento.data_evento >= hoje,
                CronogramaDepartamento.data_evento <= limite,
                Departamento.status == 'Ativo'
            ).\
            order_by(CronogramaDepartamento.data_evento.asc()).\
            limit(10).all()
        
        return jsonify([{
            'id': c.id,
            'titulo': c.titulo,
            'data_formatada': c.data_formatada,
            'horario': c.horario,
            'departamento': c.departamento.nome,
            'responsavel': c.responsavel
        } for c in cronogramas])
        
    except Exception as e:
        return jsonify({'erro': str(e)}), 500

@departamentos_bp.route('/api/aulas-painel')
@login_required
def aulas_painel():
    """API para buscar aulas que devem aparecer no painel"""
    try:
        aulas = db.session.query(AulaDepartamento).\
            join(Departamento).\
            filter(
                AulaDepartamento.exibir_no_painel == True,
                AulaDepartamento.ativo == True,
                Departamento.status == 'Ativo'
            ).\
            order_by(AulaDepartamento.criado_em.desc()).\
            limit(10).all()
        
        return jsonify([{
            'id': a.id,
            'titulo': a.titulo,
            'professora': a.professora,
            'dia_semana': a.dia_semana,
            'horario': a.horario,
            'departamento': a.departamento.nome,
            'arquivo_anexo': a.arquivo_anexo,
            'duracao_formatada': a.duracao_formatada
        } for a in aulas])
        
    except Exception as e:
        return jsonify({'erro': str(e)}), 500


@departamentos_bp.route('/uploads/aulas/<filename>')
@login_required
def download_arquivo_aula(filename):
    """Serve arquivos anexados às aulas"""
    try:
        upload_folder = os.path.join(current_app.root_path, 'static', 'uploads', 'aulas')
        return send_from_directory(upload_folder, filename)
    except Exception as e:
        flash(f'Erro ao baixar arquivo: {str(e)}', 'danger')
        return redirect(url_for('departamentos.lista_departamentos'))