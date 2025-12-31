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
    cronograma_mensal = db.Column(db.Text)  # Mantido para compatibilidade, será migrado
    possui_aulas = db.Column(db.Boolean, default=False)  # Se o departamento oferece aulas
    planejamento_aulas = db.Column(db.Text)  # Mantido para compatibilidade, será migrado
    criado_em = db.Column(db.DateTime, default=datetime.utcnow)  # Renomeado de data_cadastro
    
    # Relacionamentos
    cronogramas = db.relationship('CronogramaDepartamento', backref='departamento', lazy=True, cascade='all, delete-orphan')
    aulas = db.relationship('AulaDepartamento', backref='departamento', lazy=True, cascade='all, delete-orphan')
    eventos = db.relationship('Evento', backref='departamento', lazy=True, foreign_keys='Evento.departamento_id')

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
            'cronograma_mensal': self.cronograma_mensal,
            'possui_aulas': self.possui_aulas,
            'planejamento_aulas': self.planejamento_aulas,
            'criado_em': self.criado_em.strftime('%Y-%m-%d %H:%M:%S') if self.criado_em else None
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
    
    @property
    def cronograma_resumido(self):
        """Retorna uma versão resumida do cronograma mensal"""
        if self.cronograma_mensal and len(self.cronograma_mensal) > 150:
            return self.cronograma_mensal[:150] + "..."
        return self.cronograma_mensal or "Cronograma não definido"
    
    @property
    def status_badge_class(self):
        """Retorna a classe CSS apropriada para o badge de status"""
        status_classes = {
            'Ativo': 'bg-success',
            'Inativo': 'bg-secondary',
            'Em Formação': 'bg-warning',
            'Suspenso': 'bg-danger'
        }
        return status_classes.get(self.status, 'bg-secondary')
    
    @property
    def possui_aulas_badge(self):
        """Retorna badge formatado para exibir se possui aulas"""
        if self.possui_aulas:
            return '<span class="badge bg-primary"><i class="fas fa-graduation-cap me-1"></i>Com Aulas</span>'
        return '<span class="badge bg-light text-dark"><i class="fas fa-times me-1"></i>Sem Aulas</span>'


class CronogramaDepartamento(db.Model):
    """Modelo para cronogramas detalhados de departamentos"""
    __tablename__ = 'cronogramas_departamento'
    
    id = db.Column(db.Integer, primary_key=True)
    departamento_id = db.Column(db.Integer, db.ForeignKey('departamentos.id'), nullable=False)
    data_evento = db.Column(db.Date, nullable=False)
    titulo = db.Column(db.String(200), nullable=False)
    descricao = db.Column(db.Text)
    horario = db.Column(db.String(50))  # Ex: "19h30"
    local = db.Column(db.String(200))  # Ex: "Sala de reuniões"
    responsavel = db.Column(db.String(100))  # Quem é responsável pelo evento
    exibir_no_painel = db.Column(db.Boolean, default=False)  # Se deve aparecer no dashboard
    ativo = db.Column(db.Boolean, default=True)
    criado_em = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<CronogramaDepartamento {self.titulo}>'
    
    @property
    def data_formatada(self):
        """Retorna a data formatada em português"""
        if self.data_evento:
            meses = ['Jan', 'Fev', 'Mar', 'Abr', 'Mai', 'Jun',
                    'Jul', 'Ago', 'Set', 'Out', 'Nov', 'Dez']
            return f"{self.data_evento.day} {meses[self.data_evento.month-1]}"
        return ""
    
    @property
    def status_painel_badge(self):
        """Badge para indicar se aparece no painel"""
        if self.exibir_no_painel:
            return '<span class="badge bg-success"><i class="fas fa-eye me-1"></i>No Painel</span>'
        return '<span class="badge bg-light text-dark"><i class="fas fa-eye-slash me-1"></i>Privado</span>'


class AulaDepartamento(db.Model):
    """Modelo para aulas oferecidas pelos departamentos"""
    __tablename__ = 'aulas_departamento'
    
    id = db.Column(db.Integer, primary_key=True)
    departamento_id = db.Column(db.Integer, db.ForeignKey('departamentos.id'), nullable=False)
    titulo = db.Column(db.String(200), nullable=False)
    descricao = db.Column(db.Text)
    professora = db.Column(db.String(100))  # Nome da professora/instrutor
    dia_semana = db.Column(db.String(20))  # Ex: "Quarta-feira"
    horario = db.Column(db.String(50))  # Ex: "19h30 às 21h"
    local = db.Column(db.String(200))  # Ex: "Sala de aulas"
    data_inicio = db.Column(db.Date)  # Quando a aula começou/começará
    data_fim = db.Column(db.Date)  # Quando a aula termina (opcional)
    max_alunos = db.Column(db.Integer)  # Limite de alunos (opcional)
    material_necessario = db.Column(db.Text)  # Material didático necessário
    arquivo_anexo = db.Column(db.String(255))  # Nome do arquivo anexado (PDF, DOC, etc)
    exibir_no_painel = db.Column(db.Boolean, default=False)  # Se deve aparecer no dashboard
    ativo = db.Column(db.Boolean, default=True)
    criado_em = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<AulaDepartamento {self.titulo}>'
    
    @property
    def duracao_formatada(self):
        """Retorna a duração do curso formatada"""
        if self.data_inicio and self.data_fim:
            delta = self.data_fim - self.data_inicio
            semanas = delta.days // 7
            if semanas > 0:
                return f"{semanas} semanas"
        return "Em andamento"
    
    @property
    def status_painel_badge(self):
        """Badge para indicar se aparece no painel"""
        if self.exibir_no_painel:
            return '<span class="badge bg-info"><i class="fas fa-chalkboard me-1"></i>No Painel</span>'
        return '<span class="badge bg-light text-dark"><i class="fas fa-lock me-1"></i>Privado</span>'