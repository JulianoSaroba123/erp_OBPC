"""
Modelo para gerenciar dados do painel (Favoritos, Filtros, Histórico)
"""
from app.extensoes import db
from datetime import datetime


class FavoritoPainel(db.Model):
    """Modelo para rastrear atividades/aulas favoritadas pelo usuário"""
    __tablename__ = 'favorito_painel'
    
    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
    
    # Tipo de item: 'atividade', 'aula', 'evento'
    tipo_item = db.Column(db.String(50), nullable=False)
    # ID do item no banco (id do cronograma, aula, evento, etc)
    item_id = db.Column(db.Integer, nullable=False)
    # Nome do item (para referência rápida)
    nome_item = db.Column(db.String(255), nullable=False)
    # Departamento (para filtro)
    departamento_id = db.Column(db.Integer, nullable=True)
    
    # Controle
    pinado = db.Column(db.Boolean, default=False)  # Se está pinado no topo
    criado_em = db.Column(db.DateTime, default=datetime.utcnow)
    atualizado_em = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<FavoritoPainel {self.usuario_id}-{self.tipo_item}-{self.item_id}>'


class ConfiguracaoPainel(db.Model):
    """Dmodel para armazenar configurações do painel por usuário"""
    __tablename__ = 'configuracao_painel'
    
    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), unique=True, nullable=False)
    
    # Filtros
    departamento_selecionado = db.Column(db.Integer, nullable=True)  # Filtrar por departamento
    mostrar_todos_departamentos = db.Column(db.Boolean, default=True)
    
    # Exibição
    mostrar_atividades = db.Column(db.Boolean, default=True)
    mostrar_aulas = db.Column(db.Boolean, default=True)
    mostrar_eventos = db.Column(db.Boolean, default=True)
    mostrar_aniversariantes = db.Column(db.Boolean, default=True)
    
    # Ordenação
    ordenar_por = db.Column(db.String(50), default='data')  # 'data', 'departamento', 'titulo'
    
    criado_em = db.Column(db.DateTime, default=datetime.utcnow)
    atualizado_em = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<ConfiguracaoPainel usuario_{self.usuario_id}>'
