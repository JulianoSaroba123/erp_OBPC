from app.extensoes import db
from datetime import datetime

class Recibo(db.Model):
    __tablename__ = 'recibos'
    
    id = db.Column(db.Integer, primary_key=True)
    numero_recibo = db.Column(db.String(50), unique=True, nullable=False, index=True)
    
    # Dados do Recebedor
    nome_recebedor = db.Column(db.String(200), nullable=False)
    cpf_cnpj_recebedor = db.Column(db.String(20))
    
    # Dados do Pagamento
    valor = db.Column(db.Float, nullable=False)
    data_pagamento = db.Column(db.Date, nullable=False)
    referente_a = db.Column(db.String(200), nullable=False)
    forma_pagamento = db.Column(db.String(50), nullable=False)
    observacoes = db.Column(db.Text)
    
    # Controle
    criado_em = db.Column(db.DateTime, default=datetime.utcnow)
    criado_por = db.Column(db.String(100))
    pdf_gerado = db.Column(db.Boolean, default=False)
    
    def __repr__(self):
        return f'<Recibo {self.numero_recibo} - {self.nome_recebedor}>'
    
    def to_dict(self):
        """Converte o recibo para dicionário"""
        return {
            'id': self.id,
            'numero_recibo': self.numero_recibo,
            'nome_recebedor': self.nome_recebedor,
            'cpf_cnpj_recebedor': self.cpf_cnpj_recebedor,
            'valor': self.valor,
            'data_pagamento': self.data_pagamento.strftime('%Y-%m-%d') if self.data_pagamento else None,
            'referente_a': self.referente_a,
            'forma_pagamento': self.forma_pagamento,
            'observacoes': self.observacoes,
            'criado_em': self.criado_em.strftime('%Y-%m-%d %H:%M:%S') if self.criado_em else None,
            'criado_por': self.criado_por,
            'pdf_gerado': self.pdf_gerado
        }
    
    @staticmethod
    def gerar_numero_recibo():
        """Gera número sequencial de recibo único"""
        ano_atual = datetime.now().year
        
        # Buscar último recibo do ano
        ultimo_recibo = Recibo.query.filter(
            Recibo.numero_recibo.like(f'REC-{ano_atual}-%')
        ).order_by(Recibo.id.desc()).first()
        
        if ultimo_recibo:
            # Extrair número sequencial
            try:
                partes = ultimo_recibo.numero_recibo.split('-')
                ultimo_num = int(partes[2])
                proximo_num = ultimo_num + 1
            except:
                proximo_num = 1
        else:
            proximo_num = 1
        
        return f"REC-{ano_atual}-{proximo_num:05d}"
