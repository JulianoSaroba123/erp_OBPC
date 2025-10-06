from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_user, logout_user, login_required
from app.extensoes import db
from app.usuario.usuario_model import Usuario

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

        usuario = Usuario.query.filter_by(email=email).first()

        if usuario and usuario.check_senha(senha):
            if usuario.ativo:
                login_user(usuario)
                flash("Login realizado com sucesso!", "success")
                return redirect(url_for("usuario.painel"))  # painel principal
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
    return render_template("painel.html")
