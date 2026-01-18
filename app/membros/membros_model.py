from app.extensoes import db
from datetime import datetime

class Membro(db.Model):
    __tablename__ = 'membros'
    
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    cpf = db.Column(db.String(14))  # CPF com formatação XXX.XXX.XXX-XX
    telefone = db.Column(db.String(20))
    email = db.Column(db.String(120))
    endereco = db.Column(db.String(200))
    numero = db.Column(db.String(10))  # Número do endereço
    bairro = db.Column(db.String(100))  # Bairro
    cidade = db.Column(db.String(100))
    estado = db.Column(db.String(2))
    cep = db.Column(db.String(10))
    data_nascimento = db.Column(db.Date)
    data_batismo = db.Column(db.Date)
    status = db.Column(db.String(20), default='Ativo')
    tipo = db.Column(db.String(20), default='Membro')  # Membro, Obreiro, Lider
    observacoes = db.Column(db.Text)
    data_cadastro = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<Membro {self.nome}>'
    
    def to_dict(self):
        """Converte o objeto Membro para dicionário"""
        return {
            'id': self.id,
            'nome': self.nome,
            'cpf': self.cpf,
            'telefone': self.telefone,
            'email': self.email,
            'endereco': self.endereco,
            'numero': self.numero,
            'bairro': self.bairro,
            'cidade': self.cidade,
            'estado': self.estado,
            'cep': self.cep,
            'data_nascimento': self.data_nascimento.strftime('%Y-%m-%d') if self.data_nascimento else None,
            'data_batismo': self.data_batismo.strftime('%Y-%m-%d') if self.data_batismo else None,
            'status': self.status,
            'observacoes': self.observacoes,
            'data_cadastro': self.data_cadastro.strftime('%Y-%m-%d %H:%M:%S') if self.data_cadastro else None
        }