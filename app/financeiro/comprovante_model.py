"""
Modelo de Comprovantes - Sistema OBPC
Múltiplos comprovantes por lançamento financeiro
"""

from app.extensoes import db
from datetime import datetime

class Comprovante(db.Model):
    """Modelo para armazenar múltiplos comprovantes por lançamento"""
    __tablename__ = 'comprovantes'
    
    id = db.Column(db.Integer, primary_key=True)
    lancamento_id = db.Column(db.Integer, db.ForeignKey('lancamentos.id'), nullable=False)
    arquivo = db.Column(db.String(300), nullable=False)  # Caminho do arquivo
    nome_original = db.Column(db.String(255), nullable=True)  # Nome original do arquivo
    tamanho = db.Column(db.Integer, nullable=True)  # Tamanho em bytes
    tipo_mime = db.Column(db.String(100), nullable=True)  # Tipo MIME do arquivo
    criado_em = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relacionamento com Lancamento
    lancamento = db.relationship('Lancamento', back_populates='comprovantes')
    
    def __repr__(self):
        return f'<Comprovante {self.nome_original}>'
    
    def nome_arquivo(self):
        """Retorna apenas o nome do arquivo"""
        if self.arquivo:
            return self.arquivo.split('/')[-1]
        return None
    
    def extensao(self):
        """Retorna a extensão do arquivo"""
        if self.arquivo:
            return self.arquivo.split('.')[-1].lower()
        return None
    
    def is_imagem(self):
        """Verifica se o arquivo é uma imagem"""
        extensoes_imagem = ['jpg', 'jpeg', 'png', 'gif', 'bmp']
        return self.extensao() in extensoes_imagem
    
    def is_pdf(self):
        """Verifica se o arquivo é PDF"""
        return self.extensao() == 'pdf'
    
    def tamanho_formatado(self):
        """Retorna o tamanho do arquivo formatado"""
        if not self.tamanho:
            return "N/A"
        
        if self.tamanho < 1024:
            return f"{self.tamanho} B"
        elif self.tamanho < 1024 * 1024:
            return f"{self.tamanho / 1024:.1f} KB"
        else:
            return f"{self.tamanho / (1024 * 1024):.1f} MB"
