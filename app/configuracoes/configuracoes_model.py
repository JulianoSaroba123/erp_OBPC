#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Modelo de Configurações - Sistema OBPC
Igreja O Brasil para Cristo - Tietê/SP

Modelo para gerenciar todas as configurações do sistema
"""

from app.extensoes import db
from datetime import datetime

class Configuracao(db.Model):
    """Modelo para configurações gerais do sistema"""
    __tablename__ = 'configuracoes'
    
    # Campo ID
    id = db.Column(db.Integer, primary_key=True)
    
    # Dados Institucionais
    nome_igreja = db.Column(db.String(200), nullable=False, default='Igreja O Brasil para Cristo')
    cnpj = db.Column(db.String(18), nullable=True)
    dirigente = db.Column(db.String(100), nullable=True)
    tesoureiro = db.Column(db.String(100), nullable=True)
    cidade = db.Column(db.String(100), nullable=False, default='Tietê')
    bairro = db.Column(db.String(100), nullable=True)
    endereco = db.Column(db.String(200), nullable=True)
    cep = db.Column(db.String(9), nullable=True)  # Formato: 12345-678
    telefone = db.Column(db.String(20), nullable=True)
    email = db.Column(db.String(100), nullable=True)
    logo = db.Column(db.String(255), nullable=True, default='static/logo_obpc_novo.jpg')
    
    # Diretoria da Igreja
    presidente = db.Column(db.String(100), nullable=True)  # Pastor Dirigente
    vice_presidente = db.Column(db.String(100), nullable=True)  # Pastora
    primeiro_secretario = db.Column(db.String(100), nullable=True)  # 1º Secretário
    segundo_secretario = db.Column(db.String(100), nullable=True)  # 2º Secretário
    primeiro_tesoureiro = db.Column(db.String(100), nullable=True)  # 1º Tesoureiro
    segundo_tesoureiro = db.Column(db.String(100), nullable=True)  # 2º Tesoureiro
    
    # Configurações Financeiras
    banco_padrao = db.Column(db.String(100), nullable=True, default='Caixa Econômica Federal')
    percentual_conselho = db.Column(db.Float, nullable=False, default=10.0)
    saldo_inicial = db.Column(db.Float, nullable=False, default=0.0)
    
    # Configurações de Relatórios
    rodape_relatorio = db.Column(db.String(255), nullable=False, default='Sistema Administrativo OBPC')
    exibir_logo_relatorio = db.Column(db.Boolean, nullable=False, default=True)
    campo_assinatura_1 = db.Column(db.String(100), nullable=True, default='Pastor Responsável')
    campo_assinatura_2 = db.Column(db.String(100), nullable=True, default='Tesoureiro(a)')
    fonte_relatorio = db.Column(db.String(50), nullable=False, default='Helvetica')
    
    # Configurações de Aparência
    tema = db.Column(db.String(20), nullable=False, default='escuro')
    cor_principal = db.Column(db.String(7), nullable=False, default='#0b1b3a')
    cor_secundaria = db.Column(db.String(7), nullable=False, default='#228B22')
    cor_destaque = db.Column(db.String(7), nullable=False, default="#3553FF")
    mensagem_painel = db.Column(db.Text, nullable=True, default='Bem-vindo ao Sistema Administrativo da Igreja O Brasil para Cristo')
    
    # Configurações Adicionais
    backup_automatico = db.Column(db.Boolean, nullable=False, default=True)
    notificacoes_email = db.Column(db.Boolean, nullable=False, default=False)
    idioma = db.Column(db.String(5), nullable=False, default='pt-BR')
    fuso_horario = db.Column(db.String(50), nullable=False, default='America/Sao_Paulo')
    
    # Metadados
    criado_em = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    atualizado_em = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<Configuracao {self.nome_igreja}>'
    
    @staticmethod
    def obter_configuracao():
        """Retorna a configuração única do sistema (ID=1) ou cria uma padrão"""
        config = Configuracao.query.filter_by(id=1).first()
        
        if not config:
            # Criar configuração padrão
            config = Configuracao(
                id=1,
                nome_igreja='Igreja O Brasil para Cristo',
                cidade='Tietê',
                bairro='Centro',
                endereco='Rua da Igreja, 123',
                telefone='(15) 1234-5678',
                email='contato@obpc.org.br',
                cnpj='12.345.678/0001-90',
                dirigente='Pastor João Silva',
                tesoureiro='Maria Santos',
                # Diretoria
                presidente='Pastor João Silva',
                vice_presidente='Pastora Ana Silva',
                primeiro_secretario='José dos Santos',
                segundo_secretario='Maria da Silva',
                primeiro_tesoureiro='Carlos Oliveira',
                segundo_tesoureiro='Ana Santos',
                banco_padrao='Caixa Econômica Federal',
                percentual_conselho=10.0,
                saldo_inicial=0.0,
                rodape_relatorio='Igreja O Brasil para Cristo - Tietê/SP',
                exibir_logo_relatorio=True,
                campo_assinatura_1='Pastor Responsável',
                campo_assinatura_2='Tesoureiro(a)',
                fonte_relatorio='Helvetica',
                tema='escuro',
                cor_principal='#0b1b3a',
                cor_secundaria='#228B22',
                cor_destaque='#FFD700',
                mensagem_painel='Bem-vindo ao Sistema Administrativo da Igreja O Brasil para Cristo - Tietê/SP',
                backup_automatico=True,
                notificacoes_email=False,
                idioma='pt-BR',
                fuso_horario='America/Sao_Paulo'
            )
            
            try:
                db.session.add(config)
                db.session.commit()
            except Exception as e:
                db.session.rollback()
                print(f"Erro ao criar configuração padrão: {str(e)}")
        
        return config
    
    def salvar(self):
        """Salva as alterações da configuração no banco"""
        try:
            self.atualizado_em = datetime.utcnow()
            db.session.commit()
            return True
        except Exception as e:
            db.session.rollback()
            print(f"Erro ao salvar configuração: {str(e)}")
            return False
    
    def nome_igreja_completo(self):
        """Retorna o nome completo da igreja com cidade"""
        if self.cidade:
            return f"{self.nome_igreja} - {self.cidade}/SP"
        return self.nome_igreja
    
    def endereco_completo(self):
        """Retorna o endereço completo formatado"""
        endereco_parts = []
        
        if self.endereco:
            endereco_parts.append(self.endereco)
        if self.bairro:
            endereco_parts.append(f"Bairro {self.bairro}")
        if self.cidade:
            endereco_parts.append(f"{self.cidade}/SP")
            
        return ", ".join(endereco_parts) if endereco_parts else ""
    
    def telefone_formatado(self):
        """Retorna o telefone formatado"""
        if self.telefone:
            # Remove caracteres não numéricos
            numeros = ''.join(filter(str.isdigit, self.telefone))
            
            if len(numeros) == 11:  # Celular
                return f"({numeros[:2]}) {numeros[2:7]}-{numeros[7:]}"
            elif len(numeros) == 10:  # Telefone fixo
                return f"({numeros[:2]}) {numeros[2:6]}-{numeros[6:]}"
        
        return self.telefone
    
    def cnpj_formatado(self):
        """Retorna o CNPJ formatado"""
        if self.cnpj:
            # Remove caracteres não numéricos
            numeros = ''.join(filter(str.isdigit, self.cnpj))
            
            if len(numeros) == 14:
                return f"{numeros[:2]}.{numeros[2:5]}.{numeros[5:8]}/{numeros[8:12]}-{numeros[12:]}"
        
        return self.cnpj
    
    def get_cores_tema(self):
        """Retorna as cores do tema atual"""
        return {
            'principal': self.cor_principal,
            'secundaria': self.cor_secundaria,
            'destaque': self.cor_destaque
        }
    
    def is_tema_escuro(self):
        """Verifica se o tema atual é escuro"""
        return self.tema == 'escuro'
    
    @staticmethod
    def get_temas_disponiveis():
        """Retorna os temas disponíveis"""
        return [
            ('escuro', 'Tema Escuro'),
            ('claro', 'Tema Claro'),
            ('azul', 'Tema Azul'),
            ('verde', 'Tema Verde')
        ]
    
    @staticmethod
    def get_fontes_disponiveis():
        """Retorna as fontes disponíveis para relatórios"""
        return [
            ('Helvetica', 'Helvetica'),
            ('Times-Roman', 'Times New Roman'),
            ('Courier', 'Courier'),
            ('Arial', 'Arial')
        ]
    
    @staticmethod
    def get_bancos_disponiveis():
        """Retorna a lista de bancos disponíveis"""
        return [
            'Caixa Econômica Federal',
            'Banco do Brasil',
            'Banco Santander',
            'Banco Itaú',
            'Banco Bradesco',
            'Nubank',
            'Banco Inter',
            'Banco Original',
            'PagBank',
            'Outros'
        ]