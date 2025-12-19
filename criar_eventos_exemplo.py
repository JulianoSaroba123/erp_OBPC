#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Script para criar eventos de exemplo - Sistema OBPC
Igreja O Brasil para Cristo - Tietê/SP
"""

from datetime import datetime, timedelta
from app import create_app
from app.extensoes import db
from app.eventos.eventos_model import Evento

def criar_eventos_exemplo():
    """Cria eventos de exemplo para testar o sistema"""
    app = create_app()
    
    with app.app_context():
        print("🗓️ Criando eventos de exemplo...")
        
        # Data base para os eventos
        hoje = datetime.now()
        
        eventos_exemplo = [
            {
                'titulo': 'Culto de Domingo',
                'descricao': 'Culto dominical com pregação da Palavra e adoração',
                'data_inicio': hoje + timedelta(days=3, hours=19),
                'data_fim': hoje + timedelta(days=3, hours=21),
                'local': 'Templo Principal',
                'responsavel': 'Pastor João Silva',
                'status': 'Agendado'
            },
            {
                'titulo': 'Escola Bíblica Dominical',
                'descricao': 'Ensino bíblico para todas as idades',
                'data_inicio': hoje + timedelta(days=3, hours=9),
                'data_fim': hoje + timedelta(days=3, hours=10, minutes=30),
                'local': 'Salas de Aula',
                'responsavel': 'Professora Maria Santos',
                'status': 'Agendado'
            },
            {
                'titulo': 'Reunião de Oração',
                'descricao': 'Momento de oração e intercessão pela igreja e comunidade',
                'data_inicio': hoje + timedelta(days=2, hours=19, minutes=30),
                'data_fim': hoje + timedelta(days=2, hours=21),
                'local': 'Templo Principal',
                'responsavel': 'Diácono Pedro Costa',
                'status': 'Agendado'
            },
            {
                'titulo': 'Ensaio do Coral',
                'descricao': 'Ensaio semanal do ministério de louvor',
                'data_inicio': hoje + timedelta(days=5, hours=19),
                'data_fim': hoje + timedelta(days=5, hours=20, minutes=30),
                'local': 'Templo Principal',
                'responsavel': 'Ministro Carlos Oliveira',
                'status': 'Agendado'
            },
            {
                'titulo': 'Reunião de Jovens',
                'descricao': 'Encontro semanal do ministério jovem',
                'data_inicio': hoje + timedelta(days=6, hours=19),
                'data_fim': hoje + timedelta(days=6, hours=21),
                'local': 'Salão da Juventude',
                'responsavel': 'Pastor Auxiliar Lucas Lima',
                'status': 'Agendado'
            },
            {
                'titulo': 'Conferência Ministerial',
                'descricao': 'Conferência anual com palestrantes convidados',
                'data_inicio': hoje + timedelta(days=15, hours=19),
                'data_fim': hoje + timedelta(days=17, hours=21),
                'local': 'Templo Principal',
                'responsavel': 'Pastor João Silva',
                'status': 'Agendado'
            },
            {
                'titulo': 'Retiro Espiritual',
                'descricao': 'Retiro de fim de semana para crescimento espiritual',
                'data_inicio': hoje + timedelta(days=21, hours=18),
                'data_fim': hoje + timedelta(days=23, hours=16),
                'local': 'Chácara Monte Sião',
                'responsavel': 'Equipe Pastoral',
                'status': 'Agendado'
            },
            {
                'titulo': 'Culto de Ação de Graças (Concluído)',
                'descricao': 'Culto especial de gratidão pelas bênçãos recebidas',
                'data_inicio': hoje - timedelta(days=7, hours=-19),
                'data_fim': hoje - timedelta(days=7, hours=-21),
                'local': 'Templo Principal',
                'responsavel': 'Pastor João Silva',
                'status': 'Concluído'
            },
            {
                'titulo': 'Batismo nas Águas',
                'descricao': 'Cerimônia de batismo para novos convertidos',
                'data_inicio': hoje + timedelta(days=10, hours=10),
                'data_fim': hoje + timedelta(days=10, hours=12),
                'local': 'Batistério da Igreja',
                'responsavel': 'Pastor João Silva',
                'status': 'Agendado'
            },
            {
                'titulo': 'Reunião de Liderança',
                'descricao': 'Reunião mensal com líderes de ministérios',
                'data_inicio': hoje + timedelta(days=8, hours=19, minutes=30),
                'data_fim': hoje + timedelta(days=8, hours=21, minutes=30),
                'local': 'Sala de Reuniões',
                'responsavel': 'Pastor João Silva',
                'status': 'Agendado'
            }
        ]
        
        # Verificar se já existem eventos
        eventos_existentes = Evento.query.count()
        if eventos_existentes > 0:
            print(f"⚠️  Já existem {eventos_existentes} eventos cadastrados.")
            resposta = input("Deseja adicionar os eventos de exemplo mesmo assim? (s/N): ")
            if resposta.lower() not in ['s', 'sim', 'y', 'yes']:
                print("❌ Operação cancelada.")
                return
        
        # Criar eventos
        eventos_criados = 0
        for evento_data in eventos_exemplo:
            try:
                # Verificar se evento similar já existe
                evento_existente = Evento.query.filter_by(
                    titulo=evento_data['titulo']
                ).first()
                
                if not evento_existente:
                    evento = Evento(
                        titulo=evento_data['titulo'],
                        descricao=evento_data['descricao'],
                        data_inicio=evento_data['data_inicio'],
                        data_fim=evento_data['data_fim'],
                        local=evento_data['local'],
                        responsavel=evento_data['responsavel'],
                        status=evento_data['status']
                    )
                    
                    db.session.add(evento)
                    eventos_criados += 1
                    print(f"✅ Evento criado: {evento_data['titulo']}")
                else:
                    print(f"⏭️  Evento já existe: {evento_data['titulo']}")
                    
            except Exception as e:
                print(f"❌ Erro ao criar evento '{evento_data['titulo']}': {str(e)}")
        
        try:
            db.session.commit()
            print(f"\n🎉 {eventos_criados} eventos de exemplo criados com sucesso!")
            print("\n📋 Resumo dos eventos:")
            
            # Mostrar estatísticas
            total_eventos = Evento.query.count()
            agendados = Evento.query.filter_by(status='Agendado').count()
            concluidos = Evento.query.filter_by(status='Concluído').count()
            
            print(f"• Total de eventos: {total_eventos}")
            print(f"• Agendados: {agendados}")
            print(f"• Concluídos: {concluidos}")
            
            print("\n🌐 Acesse o sistema em: http://127.0.0.1:5000")
            print("📅 Vá em Eventos > Calendário para visualizar os eventos!")
            
        except Exception as e:
            db.session.rollback()
            print(f"❌ Erro ao salvar eventos: {str(e)}")

if __name__ == '__main__':
    criar_eventos_exemplo()