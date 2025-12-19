from app.extensoes import db
from datetime import datetime

class Obreiro(db.Model):
    __tablename__ = 'obreiros'
    
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    telefone = db.Column(db.String(20))
    email = db.Column(db.String(120))
    funcao = db.Column(db.String(50))  # Diácono, Presbítero, Evangelista, Pastor, etc.
    data_consagracao = db.Column(db.Date)
    status = db.Column(db.String(20), default='Ativo')
    observacoes = db.Column(db.Text)
    data_cadastro = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<Obreiro {self.nome} - {self.funcao}>'
    
    def to_dict(self):
        """Converte o objeto Obreiro para dicionário"""
        return {
            'id': self.id,
            'nome': self.nome,
            'telefone': self.telefone,
            'email': self.email,
            'funcao': self.funcao,
            'data_consagracao': self.data_consagracao.strftime('%Y-%m-%d') if self.data_consagracao else None,
            'status': self.status,
            'observacoes': self.observacoes,
            'data_cadastro': self.data_cadastro.strftime('%Y-%m-%d %H:%M:%S') if self.data_cadastro else None
        }
    
    @property
    def tempo_ministerio(self):
        """Calcula tempo de ministério desde a consagração"""
        if self.data_consagracao:
            hoje = datetime.now().date()
            delta = hoje - self.data_consagracao
            anos = delta.days // 365
            if anos > 0:
                return f"{anos} ano{'s' if anos > 1 else ''}"
            else:
                meses = delta.days // 30
                return f"{meses} mês{'es' if meses != 1 else ''}"
        return "Não informado"