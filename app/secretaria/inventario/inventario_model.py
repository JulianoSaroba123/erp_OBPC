from app.extensoes import db
from datetime import datetime

class ItemInventario(db.Model):
    """Modelo para Inventário Patrimonial"""
    __tablename__ = 'inventario'
    
    id = db.Column(db.Integer, primary_key=True)
    codigo = db.Column(db.String(50), unique=True, nullable=False,
                       info={'label': 'Código do Item'})
    nome = db.Column(db.String(200), nullable=False,
                     info={'label': 'Nome do Item'})
    categoria = db.Column(db.String(100), nullable=False,
                          info={'label': 'Categoria'})
    descricao = db.Column(db.Text,
                          info={'label': 'Descrição Detalhada'})
    valor_aquisicao = db.Column(db.Numeric(10, 2),
                                info={'label': 'Valor de Aquisição'})
    data_aquisicao = db.Column(db.Date,
                               info={'label': 'Data de Aquisição'})
    estado_conservacao = db.Column(db.String(50), default='Bom',
                                   info={'label': 'Estado de Conservação'})
    localizacao = db.Column(db.String(200),
                            info={'label': 'Localização Atual'})
    responsavel = db.Column(db.String(100),
                            info={'label': 'Responsável pelo Item'})
    observacoes = db.Column(db.Text,
                            info={'label': 'Observações Gerais'})
    ativo = db.Column(db.Boolean, default=True,
                      info={'label': 'Item Ativo'})
    criado_em = db.Column(db.DateTime, default=datetime.utcnow,
                          info={'label': 'Data de Cadastro'})
    atualizado_em = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow,
                              info={'label': 'Última Atualização'})
    
    def __repr__(self):
        return f'<ItemInventario {self.codigo} - {self.nome}>'
    
    def to_dict(self):
        """Converte o objeto para dicionário"""
        return {
            'id': self.id,
            'codigo': self.codigo,
            'nome': self.nome,
            'categoria': self.categoria,
            'descricao': self.descricao,
            'valor_aquisicao': float(self.valor_aquisicao) if self.valor_aquisicao else None,
            'data_aquisicao': self.data_aquisicao.strftime('%d/%m/%Y') if self.data_aquisicao else None,
            'estado_conservacao': self.estado_conservacao,
            'localizacao': self.localizacao,
            'responsavel': self.responsavel,
            'observacoes': self.observacoes,
            'ativo': self.ativo,
            'criado_em': self.criado_em.strftime('%d/%m/%Y %H:%M') if self.criado_em else None,
            'atualizado_em': self.atualizado_em.strftime('%d/%m/%Y %H:%M') if self.atualizado_em else None
        }
    
    @staticmethod
    def get_categorias():
        """Retorna lista de categorias disponíveis"""
        return [
            'Móveis e Utensílios',
            'Equipamentos de Som e Imagem',
            'Instrumentos Musicais',
            'Equipamentos de Informática',
            'Veículos',
            'Eletrodomésticos',
            'Livros e Materiais',
            'Decoração e Arte',
            'Ferramentas e Equipamentos',
            'Outros'
        ]
    
    @staticmethod
    def get_estados_conservacao():
        """Retorna lista de estados de conservação"""
        return [
            'Excelente',
            'Bom',
            'Regular',
            'Ruim',
            'Péssimo'
        ]