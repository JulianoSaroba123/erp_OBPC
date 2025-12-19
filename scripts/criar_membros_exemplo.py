"""
Script para criar membros de exemplo
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from app.extensoes import db
from app.membros.membros_model import Membro
from datetime import datetime, date

app = create_app()

def criar_membros_exemplo():
    """Cria membros de exemplo para teste"""
    with app.app_context():
        print("👥 CRIANDO MEMBROS DE EXEMPLO...")
        
        # Limpar membros existentes
        Membro.query.delete()
        
        membros_exemplo = [
            {
                'nome': 'Pastor João Silva',
                'telefone': '(11) 99999-1111',
                'email': 'pastor.joao@obpc.com',
                'endereco': 'Rua da Igreja, 123',
                'cidade': 'São Paulo',
                'estado': 'SP',
                'cep': '01234-567',
                'data_nascimento': date(1970, 5, 15),
                'data_batismo': date(1990, 8, 20),
                'tipo': 'Lider',
                'status': 'Ativo',
                'observacoes': 'Pastor principal da igreja'
            },
            {
                'nome': 'Maria Santos',
                'telefone': '(11) 99999-2222',
                'email': 'maria.santos@email.com',
                'endereco': 'Av. Central, 456',
                'cidade': 'São Paulo',
                'estado': 'SP',
                'cep': '01234-890',
                'data_nascimento': date(1985, 3, 10),
                'data_batismo': date(2010, 12, 25),
                'tipo': 'Obreiro',
                'status': 'Ativo',
                'observacoes': 'Responsável pelo ministério de louvor'
            },
            {
                'nome': 'Carlos Oliveira',
                'telefone': '(11) 99999-3333',
                'email': 'carlos.oliveira@email.com',
                'endereco': 'Rua das Flores, 789',
                'cidade': 'São Paulo',
                'estado': 'SP',
                'cep': '01234-321',
                'data_nascimento': date(1992, 7, 22),
                'data_batismo': date(2015, 4, 12),
                'tipo': 'Membro',
                'status': 'Ativo',
                'observacoes': 'Participa do grupo de jovens'
            },
            {
                'nome': 'Ana Paula Costa',
                'telefone': '(11) 99999-4444', 
                'email': 'ana.costa@email.com',
                'endereco': 'Praça da Paz, 321',
                'cidade': 'São Paulo',
                'estado': 'SP',
                'cep': '01234-654',
                'data_nascimento': date(1988, 11, 5),
                'data_batismo': date(2012, 6, 10),
                'tipo': 'Obreiro',
                'status': 'Ativo',
                'observacoes': 'Coordenadora do ministério infantil'
            },
            {
                'nome': 'Roberto Ferreira',
                'telefone': '(11) 99999-5555',
                'email': 'roberto.ferreira@email.com',
                'endereco': 'Rua da Esperança, 654',
                'cidade': 'São Paulo',
                'estado': 'SP',
                'cep': '01234-987',
                'data_nascimento': date(1975, 9, 18),
                'data_batismo': date(2000, 10, 31),
                'tipo': 'Lider',
                'status': 'Ativo',
                'observacoes': 'Líder do ministério de evangelismo'
            }
        ]
        
        for dados in membros_exemplo:
            membro = Membro(**dados)
            db.session.add(membro)
            print(f"✅ {dados['nome']} ({dados['tipo']})")
        
        db.session.commit()
        
        # Verificar criação
        total = Membro.query.count()
        print(f"\n✅ {total} MEMBROS CRIADOS COM SUCESSO!")
        
        print("\n📊 ESTATÍSTICAS:")
        print(f"👑 Líderes: {Membro.query.filter_by(tipo='Lider').count()}")
        print(f"⚒️  Obreiros: {Membro.query.filter_by(tipo='Obreiro').count()}")
        print(f"👥 Membros: {Membro.query.filter_by(tipo='Membro').count()}")

if __name__ == "__main__":
    criar_membros_exemplo()