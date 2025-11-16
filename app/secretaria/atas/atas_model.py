from app.extensoes import db
from datetime import datetime

class Ata(db.Model):
    """Modelo para Atas de Reunião"""
    __tablename__ = 'atas'
    
    id = db.Column(db.Integer, primary_key=True)
    titulo = db.Column(db.String(200), nullable=False, 
                       info={'label': 'Título da Reunião'})
    data = db.Column(db.Date, nullable=False,
                     info={'label': 'Data da Reunião'})
    local = db.Column(db.String(200), 
                      info={'label': 'Local da Reunião'})
    responsavel = db.Column(db.String(100), 
                            info={'label': 'Responsável pela Reunião'})
    descricao = db.Column(db.Text, 
                          info={'label': 'Descrição/Conteúdo da Ata'})
    arquivo = db.Column(db.String(300), 
                        info={'label': 'Caminho do arquivo PDF'})
    criado_em = db.Column(db.DateTime, default=datetime.utcnow,
                          info={'label': 'Data de Criação'})
    
    def __repr__(self):
        return f'<Ata {self.titulo} - {self.data}>'
    
    def to_dict(self):
        """Converte o objeto para dicionário"""
        return {
            'id': self.id,
            'titulo': self.titulo,
            'data': self.data.strftime('%d/%m/%Y') if self.data else None,
            'local': self.local,
            'responsavel': self.responsavel,
            'descricao': self.descricao,
            'arquivo': self.arquivo,
            'criado_em': self.criado_em.strftime('%d/%m/%Y %H:%M') if self.criado_em else None
        }