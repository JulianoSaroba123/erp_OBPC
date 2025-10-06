from app.extensoes import db
from datetime import datetime

class Lancamento(db.Model):
    __tablename__ = 'lancamentos'
    
    id = db.Column(db.Integer, primary_key=True)
    data = db.Column(db.Date, default=datetime.utcnow().date)
    tipo = db.Column(db.String(20), nullable=False)  # "Entrada" ou "Saída"
    categoria = db.Column(db.String(100))
    descricao = db.Column(db.String(200))
    valor = db.Column(db.Float, nullable=False)
    conta = db.Column(db.String(50))  # "Banco", "Dinheiro", "Pix"
    observacoes = db.Column(db.Text)
    criado_em = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<Lancamento {self.tipo}: R$ {self.valor:.2f} - {self.descricao}>'
    
    def to_dict(self):
        """Converte o objeto Lancamento para dicionário"""
        return {
            'id': self.id,
            'data': self.data.strftime('%Y-%m-%d') if self.data else None,
            'tipo': self.tipo,
            'categoria': self.categoria,
            'descricao': self.descricao,
            'valor': self.valor,
            'conta': self.conta,
            'observacoes': self.observacoes,
            'criado_em': self.criado_em.strftime('%Y-%m-%d %H:%M:%S') if self.criado_em else None
        }
    
    @property
    def valor_formatado(self):
        """Retorna o valor formatado em Real brasileiro"""
        return f"R$ {self.valor:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
    
    @property
    def tipo_icon(self):
        """Retorna o ícone baseado no tipo"""
        if self.tipo == 'Entrada':
            return 'fas fa-arrow-up text-success'
        else:
            return 'fas fa-arrow-down text-danger'
    
    @property
    def conta_icon(self):
        """Retorna o ícone baseado na conta"""
        icons = {
            'Banco': 'fas fa-university',
            'Dinheiro': 'fas fa-money-bill-wave',
            'Pix': 'fas fa-qrcode'
        }
        return icons.get(self.conta, 'fas fa-wallet')
    
    @property
    def data_formatada(self):
        """Retorna a data formatada em português"""
        if not self.data:
            return '-'
        return self.data.strftime('%d/%m/%Y')
    
    @property
    def dia_semana(self):
        """Retorna o dia da semana em português"""
        if not self.data:
            return '-'
        dias = {
            'Monday': 'Segunda',
            'Tuesday': 'Terça', 
            'Wednesday': 'Quarta',
            'Thursday': 'Quinta',
            'Friday': 'Sexta',
            'Saturday': 'Sábado',
            'Sunday': 'Domingo'
        }
        return dias.get(self.data.strftime('%A'), '')
    
    @property
    def hora_criacao(self):
        """Retorna a hora de criação formatada"""
        if not self.criado_em:
            return ''
        return self.criado_em.strftime('%H:%M')
    
    @staticmethod
    def calcular_totais():
        """Calcula totais de entradas, saídas e saldo"""
        entradas = db.session.query(db.func.sum(Lancamento.valor))\
                    .filter(Lancamento.tipo == 'Entrada').scalar() or 0
        
        saidas = db.session.query(db.func.sum(Lancamento.valor))\
                  .filter(Lancamento.tipo == 'Saída').scalar() or 0
        
        saldo = entradas - saidas
        
        return {
            'entradas': entradas,
            'saidas': saidas,
            'saldo': saldo
        }
    
    @staticmethod
    def calcular_saldo_ate_mes_anterior(mes, ano):
        """Calcula o saldo acumulado até o mês anterior ao especificado"""
        from sqlalchemy import and_, extract
        
        # Se for janeiro, pegar saldo de dezembro do ano anterior
        if mes == 1:
            mes_anterior = 12
            ano_anterior = ano - 1
        else:
            mes_anterior = mes - 1
            ano_anterior = ano
        
        # Calcular entradas até o mês anterior (inclusive)
        entradas = db.session.query(db.func.sum(Lancamento.valor))\
                    .filter(
                        and_(
                            Lancamento.tipo == 'Entrada',
                            db.func.date(Lancamento.data) < f'{ano}-{mes:02d}-01'
                        )
                    ).scalar() or 0
        
        # Calcular saídas até o mês anterior (inclusive)
        saidas = db.session.query(db.func.sum(Lancamento.valor))\
                  .filter(
                      and_(
                          Lancamento.tipo == 'Saída',
                          db.func.date(Lancamento.data) < f'{ano}-{mes:02d}-01'
                      )
                  ).scalar() or 0
        
        return entradas - saidas
    
    @staticmethod
    def formatar_valor(valor):
        """Formata valor para Real brasileiro"""
        return f"R$ {valor:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')