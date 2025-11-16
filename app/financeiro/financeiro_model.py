from app.extensoes import db
from datetime import datetime
from sqlalchemy import func, and_, or_
import hashlib

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
    comprovante = db.Column(db.String(300), nullable=True)  # Caminho do arquivo de comprovante
    criado_em = db.Column(db.DateTime, default=datetime.utcnow)
    origem = db.Column(db.String(50), default="manual")  # "manual" ou "importado"
    conciliado = db.Column(db.Boolean, default=False)
    
    # Novos campos para conciliação aprimorada
    hash_duplicata = db.Column(db.String(64), nullable=True, index=True)  # Hash para detectar duplicatas
    banco_origem = db.Column(db.String(100), nullable=True)  # Banco de origem (quando importado)
    documento_ref = db.Column(db.String(50), nullable=True)  # Número documento/referência bancária
    conciliado_em = db.Column(db.DateTime, nullable=True)  # Data da conciliação
    conciliado_por = db.Column(db.String(100), nullable=True)  # Usuário que conciliou
    par_conciliacao_id = db.Column(db.Integer, db.ForeignKey('conciliacao_pares.id'), nullable=True)
    
    def __repr__(self):
        return f'<Lancamento {self.tipo}: R$ {self.valor:.2f} - {self.descricao}>'
    
    def gerar_hash_duplicata(self):
        """Gera hash único baseado em data, valor e descrição para detectar duplicatas"""
        if self.data and self.valor and self.descricao:
            string_hash = f"{self.data.strftime('%Y-%m-%d')}|{self.valor:.2f}|{self.descricao.strip().lower()}"
            return hashlib.sha256(string_hash.encode()).hexdigest()
        return None
    
    def save(self):
        """Salva o lançamento gerando hash para duplicatas"""
        if not self.hash_duplicata:
            self.hash_duplicata = self.gerar_hash_duplicata()
        db.session.add(self)
        db.session.commit()
    
    @classmethod
    def verificar_duplicata(cls, data, valor, descricao):
        """Verifica se já existe lançamento similar (possível duplicata)"""
        temp_hash = hashlib.sha256(f"{data.strftime('%Y-%m-%d')}|{valor:.2f}|{descricao.strip().lower()}".encode()).hexdigest()
        return cls.query.filter_by(hash_duplicata=temp_hash).first()
    
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
            'comprovante': self.comprovante,
            'criado_em': self.criado_em.strftime('%Y-%m-%d %H:%M:%S') if self.criado_em else None,
            'origem': self.origem,
            'conciliado': self.conciliado,
            'banco_origem': self.banco_origem,
            'documento_ref': self.documento_ref,
            'conciliado_em': self.conciliado_em.strftime('%Y-%m-%d %H:%M:%S') if self.conciliado_em else None,
            'conciliado_por': self.conciliado_por
        }
    
    def tem_comprovante(self):
        """Verifica se o lançamento possui comprovante anexado"""
        return self.comprovante is not None and self.comprovante.strip() != ''
    
    def nome_arquivo_comprovante(self):
        """Retorna apenas o nome do arquivo do comprovante"""
        if self.tem_comprovante():
            return self.comprovante.split('/')[-1]
        return None
    
    def extensao_comprovante(self):
        """Retorna a extensão do arquivo de comprovante"""
        if self.tem_comprovante():
            return self.comprovante.split('.')[-1].lower()
        return None
    
    def is_comprovante_imagem(self):
        """Verifica se o comprovante é uma imagem"""
        if not self.tem_comprovante():
            return False
        extensoes_imagem = ['jpg', 'jpeg', 'png', 'gif', 'bmp']
        return self.extensao_comprovante() in extensoes_imagem
    
    def is_comprovante_pdf(self):
        """Verifica se o comprovante é um PDF"""
        return self.extensao_comprovante() == 'pdf'

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
        entradas = db.session.query(func.sum(Lancamento.valor))\
                    .filter(Lancamento.tipo == 'Entrada').scalar() or 0
        
        saidas = db.session.query(func.sum(Lancamento.valor))\
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
        from sqlalchemy import extract
        
        # Se for janeiro, pegar saldo de dezembro do ano anterior
        if mes == 1:
            mes_anterior = 12
            ano_anterior = ano - 1
        else:
            mes_anterior = mes - 1
            ano_anterior = ano
        
        # Calcular entradas até o mês anterior (inclusive)
        entradas = db.session.query(func.sum(Lancamento.valor))\
                    .filter(
                        and_(
                            Lancamento.tipo == 'Entrada',
                            func.date(Lancamento.data) < f'{ano}-{mes:02d}-01'
                        )
                    ).scalar() or 0
        
        # Calcular saídas até o mês anterior (inclusive)
        saidas = db.session.query(func.sum(Lancamento.valor))\
                  .filter(
                      and_(
                          Lancamento.tipo == 'Saída',
                          func.date(Lancamento.data) < f'{ano}-{mes:02d}-01'
                      )
                  ).scalar() or 0
        
        return entradas - saidas
    
    @staticmethod
    def formatar_valor(valor):
        """Formata valor para Real brasileiro"""
        return f"R$ {valor:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
    
    @staticmethod
    def obter_estatisticas_conciliacao():
        """Retorna estatísticas de conciliação"""
        total = Lancamento.query.filter_by(origem='importado').count()
        conciliados = Lancamento.query.filter_by(origem='importado', conciliado=True).count()
        pendentes = total - conciliados
        
        return {
            'total_importados': total,
            'conciliados': conciliados,
            'pendentes': pendentes,
            'percentual_conciliado': (conciliados / total * 100) if total > 0 else 0
        }


class ConciliacaoHistorico(db.Model):
    """Histórico de conciliações realizadas"""
    __tablename__ = 'conciliacao_historico'
    
    id = db.Column(db.Integer, primary_key=True)
    data_conciliacao = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    usuario = db.Column(db.String(100), nullable=False)
    total_conciliados = db.Column(db.Integer, nullable=False, default=0)
    total_pendentes = db.Column(db.Integer, nullable=False, default=0)
    tipo_conciliacao = db.Column(db.String(20), default='manual')  # 'manual', 'automatica', 'mista'
    observacao = db.Column(db.Text)
    tempo_execucao = db.Column(db.Float, nullable=True)  # Tempo em segundos
    regras_aplicadas = db.Column(db.Text, nullable=True)  # JSON com regras aplicadas
    
    # Relacionamento com pares conciliados
    pares = db.relationship('ConciliacaoPar', backref='historico', lazy=True)
    
    def __repr__(self):
        return f'<ConciliacaoHistorico {self.id}: {self.data_conciliacao}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'data_conciliacao': self.data_conciliacao.strftime('%Y-%m-%d %H:%M:%S'),
            'usuario': self.usuario,
            'total_conciliados': self.total_conciliados,
            'total_pendentes': self.total_pendentes,
            'tipo_conciliacao': self.tipo_conciliacao,
            'observacao': self.observacao,
            'tempo_execucao': self.tempo_execucao,
            'quantidade_pares': len(self.pares)
        }


class ConciliacaoPar(db.Model):
    """Registra pares conciliados para auditoria e controle"""
    __tablename__ = 'conciliacao_pares'
    
    id = db.Column(db.Integer, primary_key=True)
    historico_id = db.Column(db.Integer, db.ForeignKey('conciliacao_historico.id'), nullable=True)
    lancamento_manual_id = db.Column(db.Integer, db.ForeignKey('lancamentos.id'), nullable=False)
    lancamento_importado_id = db.Column(db.Integer, db.ForeignKey('lancamentos.id'), nullable=False)
    score_similaridade = db.Column(db.Float, nullable=True)  # Score de 0-1 da similaridade
    regra_aplicada = db.Column(db.String(200), nullable=True)  # Regra que gerou a conciliação
    metodo_conciliacao = db.Column(db.String(50), default='manual')  # 'manual', 'automatico'
    usuario = db.Column(db.String(100), nullable=True)
    criado_em = db.Column(db.DateTime, default=datetime.utcnow)
    ativo = db.Column(db.Boolean, default=True)  # Para permitir desfazer conciliação
    
    # Relacionamentos
    lancamento_manual = db.relationship('Lancamento', foreign_keys=[lancamento_manual_id], backref='pares_como_manual')
    lancamento_importado = db.relationship('Lancamento', foreign_keys=[lancamento_importado_id], backref='pares_como_importado')

    def __repr__(self):
        return f'<ConciliacaoPar {self.id}: Manual({self.lancamento_manual_id}) <-> Importado({self.lancamento_importado_id})>'

    def to_dict(self):
        return {
            'id': self.id,
            'historico_id': self.historico_id,
            'lancamento_manual_id': self.lancamento_manual_id,
            'lancamento_importado_id': self.lancamento_importado_id,
            'score_similaridade': self.score_similaridade,
            'regra_aplicada': self.regra_aplicada,
            'metodo_conciliacao': self.metodo_conciliacao,
            'usuario': self.usuario,
            'criado_em': self.criado_em.strftime('%Y-%m-%d %H:%M:%S') if self.criado_em else None,
            'ativo': self.ativo
        }
    
    def desfazer(self):
        """Desfaz a conciliação deste par"""
        if self.lancamento_manual:
            self.lancamento_manual.conciliado = False
            self.lancamento_manual.conciliado_em = None
            self.lancamento_manual.conciliado_por = None
            
        if self.lancamento_importado:
            self.lancamento_importado.conciliado = False
            self.lancamento_importado.conciliado_em = None
            self.lancamento_importado.conciliado_por = None
            
        self.ativo = False
        db.session.commit()


class ImportacaoExtrato(db.Model):
    """Controle de importações de extratos bancários"""
    __tablename__ = 'importacao_extrato'
    
    id = db.Column(db.Integer, primary_key=True)
    nome_arquivo = db.Column(db.String(255), nullable=False)
    hash_arquivo = db.Column(db.String(64), nullable=False, unique=True)  # Hash do arquivo para evitar reimportação
    banco = db.Column(db.String(100), nullable=True)
    data_importacao = db.Column(db.DateTime, default=datetime.utcnow)
    usuario = db.Column(db.String(100), nullable=False)
    total_registros = db.Column(db.Integer, default=0)
    registros_processados = db.Column(db.Integer, default=0)
    registros_duplicados = db.Column(db.Integer, default=0)
    registros_erro = db.Column(db.Integer, default=0)
    status = db.Column(db.String(20), default='processando')  # 'processando', 'concluido', 'erro'
    log_detalhado = db.Column(db.Text, nullable=True)  # Log detalhado da importação
    
    def __repr__(self):
        return f'<ImportacaoExtrato {self.nome_arquivo}: {self.status}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'nome_arquivo': self.nome_arquivo,
            'banco': self.banco,
            'data_importacao': self.data_importacao.strftime('%Y-%m-%d %H:%M:%S'),
            'usuario': self.usuario,
            'total_registros': self.total_registros,
            'registros_processados': self.registros_processados,
            'registros_duplicados': self.registros_duplicados,
            'registros_erro': self.registros_erro,
            'status': self.status
        }