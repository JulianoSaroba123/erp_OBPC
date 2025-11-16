from datetime import datetime
from app import db

class Oficio(db.Model):
    __tablename__ = 'oficios'
    
    id = db.Column(db.Integer, primary_key=True)
    numero = db.Column(db.String(20), unique=True, nullable=False)  # OF-2025-001
    data = db.Column(db.Date, nullable=False, default=datetime.utcnow().date)
    destinatario = db.Column(db.String(200), nullable=False)
    assunto = db.Column(db.String(300), nullable=False)
    descricao = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(50), nullable=False, default='Emitido')
    arquivo = db.Column(db.String(300))  # Caminho do PDF gerado
    criado_em = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<Oficio {self.numero}: {self.assunto}>'
    
    def to_dict(self):
        """Converte o objeto para dicionário"""
        return {
            'id': self.id,
            'numero': self.numero,
            'data': self.data.strftime('%d/%m/%Y') if self.data else '',
            'destinatario': self.destinatario,
            'assunto': self.assunto,
            'descricao': self.descricao,
            'status': self.status,
            'arquivo': self.arquivo,
            'criado_em': self.criado_em.strftime('%d/%m/%Y %H:%M') if self.criado_em else ''
        }
    
    @staticmethod
    def gerar_proximo_numero():
        """Gera o próximo número de ofício no formato OF-ANO-SEQ"""
        from datetime import datetime
        ano_atual = datetime.now().year
        
        # Busca o último ofício do ano atual
        ultimo_oficio = Oficio.query.filter(
            Oficio.numero.like(f'OF-{ano_atual}-%')
        ).order_by(Oficio.numero.desc()).first()
        
        if ultimo_oficio:
            # Extrai o número sequencial do último ofício
            try:
                numero_atual = int(ultimo_oficio.numero.split('-')[-1])
                proximo_numero = numero_atual + 1
            except (ValueError, IndexError):
                proximo_numero = 1
        else:
            proximo_numero = 1
        
        return f"OF-{ano_atual}-{proximo_numero:03d}"
    
    @staticmethod
    def get_status_options():
        """Retorna as opções de status disponíveis"""
        return [
            'Emitido',
            'Enviado',
            'Respondido',
            'Atendido',
            'Cancelado'
        ]