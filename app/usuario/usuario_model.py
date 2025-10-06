from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from app.extensoes import db, login_manager

class Usuario(UserMixin, db.Model):
    __tablename__ = "usuarios"

    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    senha_hash = db.Column(db.String(200), nullable=False)
    perfil = db.Column(db.String(50), default="Membro")  # Pastor, Tesoureiro, Secretário, etc.
    ativo = db.Column(db.Boolean, default=True)

    # -------- Métodos de senha --------
    def set_senha(self, senha):
        """Gera o hash da senha"""
        self.senha_hash = generate_password_hash(senha)

    def check_senha(self, senha):
        """Valida a senha"""
        return check_password_hash(self.senha_hash, senha)

    # -------- Métodos do Flask-Login --------
    @property
    def is_active(self):
        """Permite desativar usuários sem deletar"""
        return self.ativo

    def __repr__(self):
        return f"<Usuario {self.nome} ({self.email})>"

# Callback do Flask-Login para carregar usuário
@login_manager.user_loader
def load_user(user_id):
    return Usuario.query.get(int(user_id))
