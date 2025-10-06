from app.extensoes import db
from datetime import datetime

class Departamento(db.Model):
    __tablename__ = 'departamentos'
    
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    lider = db.Column(db.String(100))
    vice_lider = db.Column(db.String(100))
    descricao = db.Column(db.Text)
    contato = db.Column(db.String(120))  # Telefone ou email do departamento
    status = db.Column(db.String(20), default='Ativo')
    data_cadastro = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<Departamento {self.nome}>'
    
    def to_dict(self):
        """Converte o objeto Departamento para dicionário"""
        return {
            'id': self.id,
            'nome': self.nome,
            'lider': self.lider,
            'vice_lider': self.vice_lider,
            'descricao': self.descricao,
            'contato': self.contato,
            'status': self.status,
            'data_cadastro': self.data_cadastro.strftime('%Y-%m-%d %H:%M:%S') if self.data_cadastro else None
        }
    
    @property
    def lideranca_completa(self):
        """Retorna a liderança completa do departamento"""
        lideres = []
        if self.lider:
            lideres.append(f"Líder: {self.lider}")
        if self.vice_lider:
            lideres.append(f"Vice-líder: {self.vice_lider}")
        return " | ".join(lideres) if lideres else "Sem liderança definida"
    
    @property
    def descricao_resumida(self):
        """Retorna uma versão resumida da descrição"""
        if self.descricao and len(self.descricao) > 100:
            return self.descricao[:100] + "..."
        return self.descricao or "Sem descrição"