"""
Modelos do Módulo Mídia - Sistema OBPC
Unifica todos os models: Agenda, Certificados e Carteiras
"""

from app import db
from datetime import datetime


class AgendaSemanal(db.Model):
    """Modelo para agenda semanal da igreja"""
    __tablename__ = 'agenda_semanal'
    
    id = db.Column(db.Integer, primary_key=True)
    titulo = db.Column(db.String(200), nullable=False)
    data_evento = db.Column(db.Date, nullable=False)
    hora_inicio = db.Column(db.Time, nullable=True)
    hora_fim = db.Column(db.Time, nullable=True)
    local = db.Column(db.String(200), nullable=True)
    descricao = db.Column(db.Text, nullable=True)
    tipo_evento = db.Column(db.String(50), nullable=False)  # Culto, Reunião, Evento, Anúncio
    responsavel = db.Column(db.String(200), nullable=True)
    observacoes = db.Column(db.Text, nullable=True)
    ativo = db.Column(db.Boolean, default=True)
    data_criacao = db.Column(db.DateTime, default=datetime.utcnow)
    data_atualizacao = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f'<AgendaSemanal {self.titulo} - {self.data_evento}>'

    def to_dict(self):
        """Converte o objeto para dicionário"""
        return {
            'id': self.id,
            'titulo': self.titulo,
            'data_evento': self.data_evento.strftime('%Y-%m-%d') if self.data_evento else None,
            'hora_inicio': self.hora_inicio.strftime('%H:%M') if self.hora_inicio else None,
            'hora_fim': self.hora_fim.strftime('%H:%M') if self.hora_fim else None,
            'local': self.local,
            'descricao': self.descricao,
            'tipo_evento': self.tipo_evento,
            'responsavel': self.responsavel,
            'observacoes': self.observacoes,
            'ativo': self.ativo
        }


class Certificado(db.Model):
    """Modelo para certificados de batismo e apresentação"""
    __tablename__ = 'certificados'
    
    id = db.Column(db.Integer, primary_key=True)
    nome_pessoa = db.Column(db.String(200), nullable=False)
    tipo_certificado = db.Column(db.String(50), nullable=False)  # Batismo, Apresentação
    genero = db.Column(db.String(10), nullable=True)  # Masculino, Feminino - Reativado para cores
    data_evento = db.Column(db.Date, nullable=False)
    pastor_responsavel = db.Column(db.String(200), nullable=False)
    local_evento = db.Column(db.String(200), nullable=True)
    observacoes = db.Column(db.Text, nullable=True)
    numero_certificado = db.Column(db.String(50), nullable=True)
    # Campo para padrinhos (específico para apresentação)
    padrinhos = db.Column(db.Text, nullable=True)
    # Campo filiacao reativado
    filiacao = db.Column(db.Text, nullable=True)
    data_criacao = db.Column(db.DateTime, default=datetime.utcnow)
    data_atualizacao = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f'<Certificado {self.nome_pessoa} - {self.tipo_certificado}>'

    def to_dict(self):
        """Converte o objeto para dicionário"""
        return {
            'id': self.id,
            'nome_pessoa': self.nome_pessoa,
            'tipo_certificado': self.tipo_certificado,
            'genero': self.genero,  # Reativado para cores azul/rosa
            'data_evento': self.data_evento.strftime('%Y-%m-%d') if self.data_evento else None,
            'pastor_responsavel': self.pastor_responsavel,
            'local_evento': self.local_evento,
            'observacoes': self.observacoes,
            'numero_certificado': self.numero_certificado,
            'padrinhos': self.padrinhos,
            'filiacao': self.filiacao  # Campo reativado
        }


class CarteiraMembro(db.Model):
    """Modelo para carteiras de identificação dos membros"""
    __tablename__ = 'carteiras_membro'
    
    id = db.Column(db.Integer, primary_key=True)
    numero_carteira = db.Column(db.String(20), unique=True, nullable=False)
    nome_completo = db.Column(db.String(200), nullable=False)
    data_nascimento = db.Column(db.Date, nullable=False)
    telefone = db.Column(db.String(20), nullable=True)
    endereco = db.Column(db.String(300), nullable=True)
    data_batismo = db.Column(db.Date, nullable=True)
    cargo_funcao = db.Column(db.String(100), nullable=True)
    foto_caminho = db.Column(db.String(500), nullable=True)
    observacoes = db.Column(db.Text, nullable=True)
    ativo = db.Column(db.Boolean, default=True)
    data_criacao = db.Column(db.DateTime, default=datetime.utcnow)
    data_atualizacao = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f'<CarteiraMembro {self.numero_carteira} - {self.nome_completo}>'

    def to_dict(self):
        """Converte o objeto para dicionário"""
        return {
            'id': self.id,
            'numero_carteira': self.numero_carteira,
            'nome_completo': self.nome_completo,
            'data_nascimento': self.data_nascimento.strftime('%Y-%m-%d') if self.data_nascimento else None,
            'telefone': self.telefone,
            'endereco': self.endereco,
            'data_batismo': self.data_batismo.strftime('%Y-%m-%d') if self.data_batismo else None,
            'cargo_funcao': self.cargo_funcao,
            'foto_caminho': self.foto_caminho,
            'observacoes': self.observacoes,
            'ativo': self.ativo
        }

    @staticmethod
    def gerar_proximo_numero():
        """Gera o próximo número sequencial para carteira"""
        ultima_carteira = CarteiraMembro.query.order_by(CarteiraMembro.id.desc()).first()
        if ultima_carteira:
            try:
                ultimo_numero = int(ultima_carteira.numero_carteira.split('-')[-1])
                proximo_numero = ultimo_numero + 1
            except:
                proximo_numero = 1
        else:
            proximo_numero = 1
        
        return f"OBPC-{proximo_numero:04d}"