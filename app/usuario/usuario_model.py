from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from app.extensoes import db, login_manager
from enum import Enum

class NivelAcesso(Enum):
    """Enum para níveis de acesso do sistema"""
    MASTER = "master"
    ADMINISTRADOR = "administrador"
    TESOUREIRO = "tesoureiro"
    SECRETARIO = "secretario"
    MIDIA = "midia"
    LIDER_DEPARTAMENTO = "lider_departamento"
    MEMBRO = "membro"

class Usuario(UserMixin, db.Model):
    __tablename__ = "usuarios"

    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    senha_hash = db.Column(db.String(200), nullable=False)
    perfil = db.Column(db.String(50), default="Membro")  # Campo legado
    nivel_acesso = db.Column(db.String(20), default=NivelAcesso.MEMBRO.value)
    departamento_id = db.Column(db.Integer, db.ForeignKey('departamentos.id'), nullable=True)  # ID do departamento que o usuário lidera
    ativo = db.Column(db.Boolean, default=True)
    criado_por = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=True)
    criado_em = db.Column(db.DateTime, default=db.func.current_timestamp())
    ultimo_login = db.Column(db.DateTime)

    # Relacionamento para usuários criados por este usuário
    usuarios_criados = db.relationship('Usuario', backref=db.backref('criador', remote_side=[id]))
    
    # Relacionamento com departamento
    departamento = db.relationship('Departamento', foreign_keys=[departamento_id], backref='lider_usuario')

    # -------- Métodos de senha --------
    def set_senha(self, senha):
        """Gera o hash da senha"""
        self.senha_hash = generate_password_hash(senha)

    def check_senha(self, senha):
        """Valida a senha"""
        return check_password_hash(self.senha_hash, senha)

    # -------- Métodos de permissão --------
    def tem_acesso_financeiro(self):
        """Verifica se tem acesso ao módulo financeiro"""
        return self.nivel_acesso in ['master', 'administrador', 'Admin', 'tesoureiro']
    
    def tem_acesso_secretaria(self):
        """Verifica se tem acesso ao módulo secretaria"""
        return self.nivel_acesso in ['master', 'administrador', 'Admin', 'secretario']
    
    def tem_acesso_midia(self):
        """Verifica se tem acesso ao módulo mídia"""
        return self.nivel_acesso in ['master', 'administrador', 'Admin', 'midia']
    
    def tem_acesso_membros(self):
        """Verifica se tem acesso ao módulo membros"""
        return self.nivel_acesso in ['master', 'administrador', 'Admin', 'secretario']
    
    def tem_acesso_obreiros(self):
        """Verifica se tem acesso ao módulo obreiros"""
        return self.nivel_acesso in ['master', 'administrador', 'Admin', 'secretario']
    
    def tem_acesso_departamentos(self):
        """Verifica se tem acesso ao módulo departamentos"""
        return self.nivel_acesso in ['master', 'administrador', 'Admin', 'lider_departamento']
    
    def eh_lider_departamento(self):
        """Verifica se é APENAS líder de departamento (não admin/master)"""
        # APENAS líder de departamento com vínculo
        return self.nivel_acesso == 'lider_departamento' and self.departamento_id is not None
    
    def tem_acesso_eventos(self):
        """Verifica se tem acesso ao módulo eventos"""
        return self.nivel_acesso in ['master', 'administrador', 'Admin', 'lider_departamento', 'midia', 'secretario', 'membro']
    
    def pode_gerenciar_eventos(self):
        """Verifica se pode criar/editar eventos"""
        return self.nivel_acesso in ['master', 'administrador', 'Admin', 'lider_departamento', 'midia']
    
    def tem_acesso_configuracoes(self):
        """Verifica se tem acesso às configurações"""
        return self.nivel_acesso in ['master', 'administrador', 'Admin']
    
    def pode_gerenciar_usuarios(self):
        """Verifica se pode gerenciar outros usuários"""
        return self.nivel_acesso in ['master', 'administrador', 'Admin']
    
    def pode_ver_relatorios_gerais(self):
        """Verifica se pode ver relatórios gerais"""
        return self.nivel_acesso in ['master', 'administrador']

    def get_menu_principal(self):
        """Retorna o URL do menu principal baseado no nível de acesso"""
        menu_map = {
            'master': 'usuario.painel',
            'administrador': 'usuario.painel',
            'tesoureiro': 'financeiro.lista_lancamentos',
            'secretario': 'atas.lista_atas',
            'midia': 'usuario.painel',
            'lider_departamento': 'departamentos.lista_departamentos',
            'membro': 'eventos.lista_eventos'
        }
        return menu_map.get(self.nivel_acesso, 'usuario.painel')

    def get_nome_nivel(self):
        """Retorna o nome amigável do nível de acesso"""
        nomes = {
            'master': 'Master',
            'administrador': 'Administrador',
            'tesoureiro': 'Tesoureiro',
            'secretario': 'Secretário',
            'midia': 'Mídia',
            'lider_departamento': 'Líder de Departamento',
            'membro': 'Membro'
        }
        return nomes.get(self.nivel_acesso, 'Desconhecido')

    # -------- Métodos do Flask-Login --------
    @property
    def is_active(self):
        """Permite desativar usuários sem deletar"""
        return self.ativo

    def __repr__(self):
        return f"<Usuario {self.nome} ({self.email}) - {self.get_nome_nivel()}>"

# Callback do Flask-Login para carregar usuário
@login_manager.user_loader
def load_user(user_id):
    return Usuario.query.get(int(user_id))
