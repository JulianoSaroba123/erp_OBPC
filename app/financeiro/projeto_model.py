from app.extensoes import db
from datetime import datetime

class Projeto(db.Model):
    """Model para controle de projetos com destinação específica"""
    __tablename__ = 'projetos'
    
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False, unique=True)
    descricao = db.Column(db.Text)
    tipo = db.Column(db.String(50))  # Ex: "Doação", "Anistia", "Evento", "Reforma"
    status = db.Column(db.String(20), default='Ativo')  # Ativo, Concluído, Cancelado
    meta_valor = db.Column(db.Numeric(10, 2))  # Valor meta opcional
    data_inicio = db.Column(db.Date, default=datetime.now)
    data_fim = db.Column(db.Date)  # Opcional
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)
    
    # Relacionamento com lançamentos
    lancamentos = db.relationship('Lancamento', back_populates='projeto', lazy='dynamic')
    
    def __repr__(self):
        return f'<Projeto {self.nome}>'
    
    def calcular_totais(self):
        """Calcula entradas, saídas e saldo do projeto
        
        Lógica corrigida:
        - ENTRADA vinculada ao projeto = ENTRADA no projeto (doação direta)
        - SAÍDA com categoria DESTINAÇÃO = ENTRADA no projeto (transferência de recurso)
        - SAÍDA sem DESTINAÇÃO = SAÍDA do projeto (gasto real - materiais, despesas, etc)
        """
        from sqlalchemy import func
        
        # Entradas no projeto:
        # 1. Lançamentos tipo Entrada (doações diretas, OUTRAS OFERTAS)
        # 2. Lançamentos tipo Saída com categoria DESTINAÇÃO (transferências para o projeto)
        entradas = sum(
            l.valor for l in self.lancamentos.all()
            if l.tipo == 'Entrada' or 
            (l.tipo == 'Saída' and l.categoria and l.categoria.upper() == 'DESTINAÇÃO')
        )
        
        # Saídas do projeto: 
        # Qualquer SAÍDA que NÃO seja DESTINAÇÃO (compras, materiais, despesas do projeto)
        saidas = sum(
            l.valor for l in self.lancamentos.all()
            if l.tipo == 'Saída' and (not l.categoria or l.categoria.upper() != 'DESTINAÇÃO')
        )
        
        return {
            'entradas': entradas,
            'saidas': saidas,
            'saldo': entradas - saidas,
            'percentual': (float(entradas) / float(self.meta_valor) * 100) if self.meta_valor else None
        }
