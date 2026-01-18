from flask import Blueprint, render_template, redirect, url_for, request, flash, jsonify, current_app
from flask_login import login_user, logout_user, login_required, current_user
from app.extensoes import db
from app.usuario.usuario_model import Usuario, NivelAcesso
from app.departamentos.departamentos_model import Departamento
from app.utils.auth_decorators import requer_gerencia_usuarios, requer_nivel_acesso
from datetime import datetime

# Blueprint do módulo de usuário
usuario_bp = Blueprint("usuario", __name__, template_folder="templates")

# ---------- ROTA DE TESTE DE IMAGEM (TEMPORÁRIA) ----------
@usuario_bp.route("/teste-imagem")
def teste_imagem():
    return render_template("teste_imagem.html")

# ---------- ROTA RAIZ ----------
@usuario_bp.route("/")
def index():
    return redirect(url_for("usuario.login"))

# ---------- ROTA DE LOGIN ----------
@usuario_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email")
        senha = request.form.get("senha")
        lembrar = request.form.get("lembrar")  # Checkbox "lembrar de mim"

        usuario = Usuario.query.filter_by(email=email).first()

        if usuario and usuario.check_senha(senha):
            if usuario.ativo:
                # Atualizar último login
                usuario.ultimo_login = datetime.now()
                db.session.commit()
                
                # Login com sessão persistente se marcou "lembrar"
                login_user(usuario, remember=bool(lembrar))
                flash(f"Bem-vindo, {usuario.nome}! ({usuario.get_nome_nivel()})", "success")
                
                # Verificar se há uma URL de destino (next)
                next_page = request.args.get('next')
                if next_page:
                    return redirect(next_page)
                
                # Redirecionar baseado no nível de acesso
                return redirect(url_for(usuario.get_menu_principal()))
            else:
                flash("Usuário desativado. Contate o administrador.", "danger")
        else:
            flash("E-mail ou senha incorretos!", "danger")

    return render_template("usuario/login.html")


# ---------- ROTA DE LOGOUT ----------
@usuario_bp.route("/logout")
@login_required
def logout():
    logout_user()
    flash("Você saiu do sistema.", "info")
    return redirect(url_for("usuario.login"))


# ---------- ROTA DE CADASTRO DE NOVO USUÁRIO ----------
@usuario_bp.route("/cadastro", methods=["GET", "POST"])
def cadastro():
    if request.method == "POST":
        nome = request.form.get("nome")
        email = request.form.get("email")
        senha = request.form.get("senha")
        perfil = request.form.get("perfil")

        # Verifica se já existe usuário com esse email
        existente = Usuario.query.filter_by(email=email).first()
        if existente:
            flash("Já existe um usuário com este e-mail!", "warning")
            return redirect(url_for("usuario.cadastro"))

        # Cria novo usuário
        novo_usuario = Usuario(nome=nome, email=email, perfil=perfil)
        novo_usuario.set_senha(senha)

        db.session.add(novo_usuario)
        db.session.commit()

        flash("Usuário cadastrado!", "info")
        return redirect(url_for("usuario.login"))

    return render_template("usuario/cadastro.html")


# ---------- ROTA DO PAINEL PRINCIPAL ----------
@usuario_bp.route("/painel")
@login_required
def painel():
    # Buscar dados para o painel
    try:
        from app.eventos.eventos_model import Evento
        proximos_eventos = Evento.eventos_proximos(3)
        total_eventos_proximos = len(proximos_eventos)
    except Exception as e:
        proximos_eventos = []
        total_eventos_proximos = 0
    
    # Buscar atividades de TODOS os departamentos para exibir no painel
    atividades_departamento = []
    try:
        from app.departamentos.departamentos_model import CronogramaDepartamento
        from app.eventos.eventos_model import Evento
        from datetime import date, timedelta
        
        hoje = date.today()
        hoje_datetime = datetime.now()
        
        # ATUALIZAR AUTOMATICAMENTE atividades antigas do cronograma
        atividades_antigas = CronogramaDepartamento.query.filter(
            CronogramaDepartamento.data_evento < hoje
        ).all()
        
        if atividades_antigas:
            for atividade in atividades_antigas:
                atividade.data_evento = hoje + timedelta(days=7)
                atividade.exibir_no_painel = True
                atividade.ativo = True
            db.session.commit()
            current_app.logger.info(f"Painel: {len(atividades_antigas)} cronogramas antigos atualizados")
        
        # ATUALIZAR AUTOMATICAMENTE eventos antigos dos departamentos
        eventos_antigos = Evento.query.filter(
            Evento.departamento_id.isnot(None),
            Evento.data_inicio < hoje_datetime
        ).all()
        
        if eventos_antigos:
            for evento in eventos_antigos:
                # Manter a hora original, apenas atualizar a data
                hora_original = evento.data_inicio.time()
                nova_data_inicio = datetime.combine(hoje + timedelta(days=7), hora_original)
                
                # Calcular duração do evento
                if evento.data_fim:
                    duracao = evento.data_fim - evento.data_inicio
                    evento.data_fim = nova_data_inicio + duracao
                
                evento.data_inicio = nova_data_inicio
            
            db.session.commit()
            current_app.logger.info(f"Painel: {len(eventos_antigos)} eventos antigos atualizados")
        
        # BUSCAR CRONOGRAMAS DOS DEPARTAMENTOS
        cronogramas = CronogramaDepartamento.query.filter(
            CronogramaDepartamento.ativo == True,
            CronogramaDepartamento.exibir_no_painel == True,
            CronogramaDepartamento.data_evento >= hoje
        ).all()
        
        # BUSCAR EVENTOS DOS DEPARTAMENTOS (futuros)
        eventos_departamentos = Evento.query.filter(
            Evento.departamento_id.isnot(None),
            Evento.data_inicio >= hoje_datetime
        ).all()
        
        current_app.logger.info(f"Painel: {len(cronogramas)} cronogramas e {len(eventos_departamentos)} eventos encontrados")
        
        # COMBINAR cronogramas e eventos em uma única lista
        atividades_combinadas = []
        
        # Adicionar cronogramas
        for cronograma in cronogramas:
            atividades_combinadas.append({
                'tipo': 'cronograma',
                'titulo': cronograma.titulo,
                'descricao': cronograma.descricao,
                'data_evento': cronograma.data_evento,
                'data_formatada': cronograma.data_formatada,
                'horario': cronograma.horario,
                'local': cronograma.local,
                'responsavel': cronograma.responsavel,
                'departamento': cronograma.departamento
            })
        
        # Adicionar eventos de departamentos
        for evento in eventos_departamentos:
            if evento.departamento:
                atividades_combinadas.append({
                    'tipo': 'evento',
                    'titulo': evento.titulo,
                    'descricao': evento.descricao,
                    'data_evento': evento.data_inicio.date() if evento.data_inicio else None,
                    'data_formatada': evento.data_inicio.strftime('%d %b') if evento.data_inicio else '',
                    'horario': evento.data_inicio.strftime('%H:%M') if evento.data_inicio else '',
                    'local': evento.local,
                    'responsavel': evento.responsavel,
                    'departamento': evento.departamento
                })
        
        # Ordenar por data
        atividades_departamento = sorted(atividades_combinadas, key=lambda x: x['data_evento'])[:10]
        
        total_atividades = len(atividades_departamento)
        current_app.logger.info(f"Painel: {total_atividades} atividades carregadas ({len(cronogramas)} cronogramas + {len(eventos_departamentos)} eventos)")
    except Exception as e:
        current_app.logger.error(f"Erro ao buscar atividades: {e}")
        import traceback
        traceback.print_exc()
        atividades_departamento = []
        total_atividades = 0
    
    # Buscar aulas que devem aparecer no painel
    aulas_painel = []
    try:
        from app.departamentos.departamentos_model import AulaDepartamento, Departamento
        
        aulas = db.session.query(AulaDepartamento).\
            join(Departamento).\
            filter(
                AulaDepartamento.exibir_no_painel == True,
                AulaDepartamento.ativo == True,
                Departamento.status == 'Ativo'
            ).\
            order_by(AulaDepartamento.criado_em.desc()).\
            limit(10).all()
        
        aulas_painel = aulas
        current_app.logger.info(f"Painel: {len(aulas_painel)} aulas encontradas para exibição")
    except Exception as e:
        current_app.logger.error(f"Erro ao buscar aulas: {e}")
        import traceback
        traceback.print_exc()
        aulas_painel = []
    
    return render_template("painel.html", 
                         proximos_eventos=proximos_eventos,
                         total_eventos_proximos=total_eventos_proximos,
                         atividades_departamento=atividades_departamento,
                         total_atividades=total_atividades,
                         aulas_painel=aulas_painel)

# ---------- GERENCIAMENTO DE USUÁRIOS ----------
@usuario_bp.route("/usuarios")
@requer_gerencia_usuarios
def lista_usuarios():
    """Lista todos os usuários para administração"""
    usuarios = Usuario.query.order_by(Usuario.nome).all()
    return render_template("usuario/lista_usuarios.html", usuarios=usuarios)

@usuario_bp.route("/usuarios/novo", methods=["GET", "POST"])
@requer_gerencia_usuarios
def novo_usuario():
    """Criar novo usuário"""
    if request.method == "POST":
        nome = request.form.get("nome")
        email = request.form.get("email")
        senha = request.form.get("senha")
        nivel_acesso = request.form.get("nivel_acesso")
        departamento_id = request.form.get("departamento_id")

        # Validações
        if not all([nome, email, senha, nivel_acesso]):
            flash("Todos os campos são obrigatórios!", "danger")
            departamentos = Departamento.query.order_by(Departamento.nome).all()
            return render_template("usuario/novo_usuario.html", niveis=NivelAcesso, departamentos=departamentos)

        # Verificar se já existe usuário com esse email
        existente = Usuario.query.filter_by(email=email).first()
        if existente:
            flash("Já existe um usuário com este e-mail!", "warning")
            departamentos = Departamento.query.order_by(Departamento.nome).all()
            return render_template("usuario/novo_usuario.html", niveis=NivelAcesso, departamentos=departamentos)

        # Verificar se pode criar usuário com esse nível
        if not pode_criar_nivel(current_user.nivel_acesso, nivel_acesso):
            flash("Você não pode criar usuários com este nível de acesso!", "danger")
            departamentos = Departamento.query.order_by(Departamento.nome).all()
            return render_template("usuario/novo_usuario.html", niveis=NivelAcesso, departamentos=departamentos)

        # Validar departamento para líder
        if nivel_acesso == 'lider_departamento':
            if not departamento_id:
                flash("Líder de departamento precisa ter um departamento associado!", "danger")
                departamentos = Departamento.query.order_by(Departamento.nome).all()
                return render_template("usuario/novo_usuario.html", niveis=NivelAcesso, departamentos=departamentos)

        # Criar novo usuário
        novo_usuario = Usuario(
            nome=nome,
            email=email,
            nivel_acesso=nivel_acesso,
            criado_por=current_user.id,
            perfil=nivel_acesso.title()  # Manter compatibilidade
        )
        novo_usuario.set_senha(senha)
        
        # Atribuir departamento se for líder
        if nivel_acesso == 'lider_departamento':
            novo_usuario.departamento_id = int(departamento_id)

        db.session.add(novo_usuario)
        db.session.commit()

        flash(f"Usuário {nome} criado com sucesso!", "success")
        return redirect(url_for("usuario.lista_usuarios"))

    departamentos = Departamento.query.order_by(Departamento.nome).all()
    return render_template("usuario/novo_usuario.html", niveis=NivelAcesso, departamentos=departamentos)

@usuario_bp.route("/usuarios/<int:user_id>/editar", methods=["GET", "POST"])
@requer_gerencia_usuarios
def editar_usuario(user_id):
    """Editar usuário existente"""
    usuario = Usuario.query.get_or_404(user_id)
    
    # Master não pode ser editado por outros
    if usuario.nivel_acesso == 'master' and current_user.nivel_acesso != 'master':
        flash("Apenas usuários master podem editar outros masters!", "danger")
        return redirect(url_for("usuario.lista_usuarios"))
    
    if request.method == "POST":
        nome = request.form.get("nome")
        email = request.form.get("email")
        nivel_acesso = request.form.get("nivel_acesso")
        departamento_id = request.form.get("departamento_id")
        ativo = request.form.get("ativo") == "on"
        nova_senha = request.form.get("nova_senha")

        # Validações
        if not all([nome, email, nivel_acesso]):
            flash("Nome, email e nível são obrigatórios!", "danger")
            departamentos = Departamento.query.order_by(Departamento.nome).all()
            return render_template("usuario/editar_usuario.html", usuario=usuario, niveis=NivelAcesso, departamentos=departamentos)

        # Verificar email único (exceto o próprio usuário)
        existente = Usuario.query.filter_by(email=email).first()
        if existente and existente.id != usuario.id:
            flash("Já existe outro usuário com este e-mail!", "warning")
            departamentos = Departamento.query.order_by(Departamento.nome).all()
            return render_template("usuario/editar_usuario.html", usuario=usuario, niveis=NivelAcesso, departamentos=departamentos)

        # Verificar se pode alterar para esse nível
        if not pode_criar_nivel(current_user.nivel_acesso, nivel_acesso):
            flash("Você não pode definir este nível de acesso!", "danger")
            departamentos = Departamento.query.order_by(Departamento.nome).all()
            return render_template("usuario/editar_usuario.html", usuario=usuario, niveis=NivelAcesso, departamentos=departamentos)

        # Atualizar dados
        usuario.nome = nome
        usuario.email = email
        usuario.nivel_acesso = nivel_acesso
        usuario.ativo = ativo
        usuario.perfil = nivel_acesso.title()  # Manter compatibilidade
        
        # Atualizar departamento se for líder
        if nivel_acesso == 'lider_departamento':
            if not departamento_id:
                flash("Líder de departamento precisa ter um departamento associado!", "danger")
                departamentos = Departamento.query.order_by(Departamento.nome).all()
                return render_template("usuario/editar_usuario.html", usuario=usuario, niveis=NivelAcesso, departamentos=departamentos)
            usuario.departamento_id = int(departamento_id)
        else:
            usuario.departamento_id = None

        # Alterar senha se informada
        if nova_senha:
            usuario.set_senha(nova_senha)

        db.session.commit()
        flash(f"Usuário {nome} atualizado com sucesso!", "success")
        return redirect(url_for("usuario.lista_usuarios"))

    departamentos = Departamento.query.order_by(Departamento.nome).all()
    return render_template("usuario/editar_usuario.html", usuario=usuario, niveis=NivelAcesso, departamentos=departamentos)

@usuario_bp.route("/usuarios/<int:user_id>/toggle-status", methods=["POST"])
@requer_gerencia_usuarios
def toggle_status_usuario(user_id):
    """Ativar/desativar usuário"""
    usuario = Usuario.query.get_or_404(user_id)
    
    # Master não pode ser desativado
    if usuario.nivel_acesso == 'master':
        return jsonify({"success": False, "message": "Usuários master não podem ser desativados!"})
    
    # Não pode desativar a si mesmo
    if usuario.id == current_user.id:
        return jsonify({"success": False, "message": "Você não pode desativar sua própria conta!"})
    
    usuario.ativo = not usuario.ativo
    db.session.commit()
    
    status = "ativado" if usuario.ativo else "desativado"
    return jsonify({"success": True, "message": f"Usuário {status} com sucesso!", "ativo": usuario.ativo})

@usuario_bp.route("/usuarios/<int:user_id>/excluir", methods=["POST"])
@requer_nivel_acesso('master')
def excluir_usuario(user_id):
    """Excluir usuário (apenas master)"""
    usuario = Usuario.query.get_or_404(user_id)
    
    # Master não pode ser excluído
    if usuario.nivel_acesso == 'master':
        return jsonify({"success": False, "message": "Usuários master não podem ser excluídos!"})
    
    # Não pode excluir a si mesmo
    if usuario.id == current_user.id:
        return jsonify({"success": False, "message": "Você não pode excluir sua própria conta!"})
    
    nome = usuario.nome
    db.session.delete(usuario)
    db.session.commit()
    
    return jsonify({"success": True, "message": f"Usuário {nome} excluído com sucesso!"})

def pode_criar_nivel(nivel_criador, nivel_novo):
    """Verifica se um nível pode criar outro nível"""
    hierarquia = {
        'master': ['master', 'administrador', 'lider_departamento', 'tesoureiro', 'secretario', 'midia', 'membro'],
        'administrador': ['administrador', 'lider_departamento', 'tesoureiro', 'secretario', 'midia', 'membro'],
        'tesoureiro': [],
        'secretario': [],
        'midia': [],
        'membro': []
    }
    return nivel_novo in hierarquia.get(nivel_criador, [])

# ---------- ROTA DE PERFIL DO USUÁRIO ----------
@usuario_bp.route("/perfil", methods=["GET", "POST"])
@login_required
def perfil():
    """Perfil do usuário logado"""
    if request.method == "POST":
        nome = request.form.get("nome")
        email = request.form.get("email")
        senha_atual = request.form.get("senha_atual")
        nova_senha = request.form.get("nova_senha")
        confirmar_senha = request.form.get("confirmar_senha")

        # Validações básicas
        if not all([nome, email]):
            flash("Nome e email são obrigatórios!", "danger")
            return render_template("usuario/perfil.html")

        # Verificar email único (exceto o próprio usuário)
        existente = Usuario.query.filter_by(email=email).first()
        if existente and existente.id != current_user.id:
            flash("Já existe outro usuário com este e-mail!", "warning")
            return render_template("usuario/perfil.html")

        # Atualizar dados básicos
        current_user.nome = nome
        current_user.email = email

        # Alterar senha se informada
        if nova_senha:
            if not senha_atual:
                flash("Informe a senha atual para alterar a senha!", "danger")
                return render_template("usuario/perfil.html")
            
            if not current_user.check_senha(senha_atual):
                flash("Senha atual incorreta!", "danger")
                return render_template("usuario/perfil.html")
            
            if nova_senha != confirmar_senha:
                flash("A confirmação da nova senha não confere!", "danger")
                return render_template("usuario/perfil.html")
            
            if len(nova_senha) < 6:
                flash("A nova senha deve ter pelo menos 6 caracteres!", "danger")
                return render_template("usuario/perfil.html")
            
            current_user.set_senha(nova_senha)

        db.session.commit()
        flash("Perfil atualizado com sucesso!", "success")
        return redirect(url_for("usuario.perfil"))

    return render_template("usuario/perfil.html")


# ---------- ROTA ADMINISTRATIVA: ATUALIZAR ATIVIDADES ----------
@usuario_bp.route("/admin/atualizar-atividades-painel")
@login_required
@requer_nivel_acesso(NivelAcesso.ADMINISTRADOR)
def atualizar_atividades_painel():
    """Atualiza atividades existentes para aparecerem no painel"""
    from app.departamentos.departamentos_model import CronogramaDepartamento
    from datetime import date, timedelta
    
    try:
        hoje = date.today()
        todas_atividades = CronogramaDepartamento.query.all()
        
        atualizadas = 0
        datas_atualizadas = 0
        
        for atividade in todas_atividades:
            modificado = False
            
            # Garantir que exibir_no_painel seja True
            if not atividade.exibir_no_painel:
                atividade.exibir_no_painel = True
                modificado = True
                atualizadas += 1
            
            # Se a data já passou, atualizar para uma data futura
            if atividade.data_evento < hoje:
                atividade.data_evento = hoje + timedelta(days=7)
                modificado = True
                datas_atualizadas += 1
            
            # Garantir que está ativo
            if not atividade.ativo:
                atividade.ativo = True
                modificado = True
        
        db.session.commit()
        
        # Contar atividades que aparecerão no painel
        total_painel = CronogramaDepartamento.query.filter(
            CronogramaDepartamento.ativo == True,
            CronogramaDepartamento.exibir_no_painel == True,
            CronogramaDepartamento.data_evento >= hoje
        ).count()
        
        flash(f"Atividades atualizadas! {atualizadas} marcadas para painel, {datas_atualizadas} datas atualizadas. Total no painel: {total_painel}", "success")
        
    except Exception as e:
        current_app.logger.error(f"Erro ao atualizar atividades: {e}")
        flash(f"Erro ao atualizar atividades: {str(e)}", "danger")
    
    return redirect(url_for("usuario.painel"))
