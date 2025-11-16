#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Modelo de Despesas Fixas do Conselho - Sistema OBPC
Igreja O Brasil para Cristo - Tietê/SP

Modelo para gerenciar despesas fixas mensais do conselho administrativo
"""

from app.extensoes import db
from datetime import datetime

class DespesaFixaConselho(db.Model):
    """Modelo para despesas fixas do conselho administrativo"""
    __tablename__ = 'despesas_fixas_conselho'
    
    # Campos principais
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)  # Ex: "Oferta Voluntária Conchas"
    descricao = db.Column(db.Text, nullable=True)  # Descrição detalhada
    valor_padrao = db.Column(db.Float, nullable=False, default=0.0)  # Valor padrão mensal
    
    # Configurações
    ativo = db.Column(db.Boolean, nullable=False, default=True)  # Se está ativo
    tipo = db.Column(db.String(50), nullable=False, default='despesa_fixa')  # Tipo da despesa
    categoria = db.Column(db.String(100), nullable=True)  # Categoria se necessário
    
    # Campos de auditoria
    data_criacao = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    data_atualizacao = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<DespesaFixaConselho {self.nome}: R$ {self.valor_padrao:.2f}>'
    
    @classmethod
    def obter_despesas_ativas(cls):
        """Obtém todas as despesas fixas ativas"""
        return cls.query.filter_by(ativo=True).order_by(cls.nome).all()
    
    @classmethod
    def obter_total_despesas_fixas(cls):
        """Calcula o total das despesas fixas ativas"""
        despesas = cls.obter_despesas_ativas()
        return sum(despesa.valor_padrao for despesa in despesas)
    
    @classmethod
    def obter_despesas_como_dict(cls):
        """Retorna as despesas como dicionário para uso nos relatórios"""
        despesas = cls.obter_despesas_ativas()
        return {
            despesa.nome.lower().replace(' ', '_').replace('ã', 'a').replace('ç', 'c'): despesa.valor_padrao 
            for despesa in despesas
        }
    
    @classmethod
    def obter_despesas_para_relatorio(cls):
        """Retorna as despesas formatadas para o relatório da sede"""
        despesas = cls.obter_despesas_ativas()
        resultado = {}
        
        for despesa in despesas:
            # Criar chaves padronizadas para o relatório
            if 'conchas' in despesa.nome.lower():
                resultado['oferta_voluntaria_conchas'] = despesa.valor_padrao
            elif 'site' in despesa.nome.lower():
                resultado['site'] = despesa.valor_padrao
            elif 'filipe' in despesa.nome.lower():
                resultado['projeto_filipe'] = despesa.valor_padrao
            elif 'força' in despesa.nome.lower() or 'forca' in despesa.nome.lower():
                resultado['forca_para_viver'] = despesa.valor_padrao
            elif 'contador' in despesa.nome.lower():
                resultado['contador_sede'] = despesa.valor_padrao
            else:
                # Para despesas não padronizadas, usar o nome limpo
                chave = despesa.nome.lower().replace(' ', '_').replace('ã', 'a').replace('ç', 'c')
                resultado[chave] = despesa.valor_padrao
        
        return resultado