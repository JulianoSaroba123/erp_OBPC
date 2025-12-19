#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Modelo de Eventos - Sistema OBPC
Igreja O Brasil para Cristo - Tietê/SP

Modelo para gerenciamento de eventos da igreja
"""

from datetime import datetime
from app.extensoes import db


class Evento(db.Model):
    """Modelo para eventos da igreja"""
    
    __tablename__ = 'eventos'
    
    # Campos principais
    id = db.Column(db.Integer, primary_key=True)
    titulo = db.Column(db.String(200), nullable=False)
    descricao = db.Column(db.Text)
    data_inicio = db.Column(db.DateTime, nullable=False)
    data_fim = db.Column(db.DateTime, nullable=False)
    local = db.Column(db.String(200))
    responsavel = db.Column(db.String(100))
    status = db.Column(db.String(20), default='Agendado')
    criado_em = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<Evento {self.titulo}>'
    
    def to_dict(self):
        """Converte objeto para dicionário"""
        return {
            'id': self.id,
            'titulo': self.titulo,
            'descricao': self.descricao,
            'data_inicio': self.data_inicio.strftime('%Y-%m-%d %H:%M') if self.data_inicio else None,
            'data_fim': self.data_fim.strftime('%Y-%m-%d %H:%M') if self.data_fim else None,
            'local': self.local,
            'responsavel': self.responsavel,
            'status': self.status,
            'criado_em': self.criado_em.strftime('%Y-%m-%d %H:%M') if self.criado_em else None
        }
    
    def data_inicio_formatada(self):
        """Retorna data de início formatada para exibição"""
        if self.data_inicio:
            return self.data_inicio.strftime('%d/%m/%Y %H:%M')
        return '-'
    
    def data_fim_formatada(self):
        """Retorna data de fim formatada para exibição"""
        if self.data_fim:
            return self.data_fim.strftime('%d/%m/%Y %H:%M')
        return '-'
    
    def periodo_formatado(self):
        """Retorna período completo formatado"""
        if self.data_inicio and self.data_fim:
            inicio = self.data_inicio.strftime('%d/%m/%Y %H:%M')
            fim = self.data_fim.strftime('%d/%m/%Y %H:%M')
            return f"{inicio} - {fim}"
        return '-'
    
    def duracao_horas(self):
        """Calcula duração do evento em horas"""
        if self.data_inicio and self.data_fim:
            delta = self.data_fim - self.data_inicio
            horas = delta.total_seconds() / 3600
            return round(horas, 1)
        return 0
    
    def status_badge_class(self):
        """Retorna classe CSS do badge do status"""
        classes = {
            'Agendado': 'bg-primary',
            'Concluído': 'bg-success', 
            'Cancelado': 'bg-danger',
            'Em Andamento': 'bg-warning'
        }
        return classes.get(self.status, 'bg-secondary')
    
    def is_evento_passado(self):
        """Verifica se o evento já passou"""
        if self.data_fim:
            return self.data_fim < datetime.now()
        return False
    
    def is_evento_hoje(self):
        """Verifica se o evento é hoje"""
        if self.data_inicio:
            hoje = datetime.now().date()
            return self.data_inicio.date() == hoje
        return False
    
    @staticmethod
    def eventos_proximos(limite=5):
        """Retorna próximos eventos ordenados por data"""
        agora = datetime.now()
        return Evento.query.filter(
            Evento.data_inicio >= agora,
            Evento.status != 'Cancelado'
        ).order_by(Evento.data_inicio).limit(limite).all()
    
    @staticmethod
    def eventos_mes_atual():
        """Retorna eventos do mês atual"""
        agora = datetime.now()
        inicio_mes = agora.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        
        # Calcular primeiro dia do próximo mês
        if agora.month == 12:
            fim_mes = agora.replace(year=agora.year + 1, month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
        else:
            fim_mes = agora.replace(month=agora.month + 1, day=1, hour=0, minute=0, second=0, microsecond=0)
        
        return Evento.query.filter(
            Evento.data_inicio >= inicio_mes,
            Evento.data_inicio < fim_mes
        ).order_by(Evento.data_inicio).all()
    
    @staticmethod
    def contar_por_status():
        """Conta eventos por status"""
        from sqlalchemy import func
        resultado = db.session.query(
            Evento.status,
            func.count(Evento.id).label('total')
        ).group_by(Evento.status).all()
        
        contadores = {}
        for status, total in resultado:
            contadores[status] = total
        
        return contadores