#!/usr/bin/env python3
"""
Script para capturar exceção específica na rota mídia
"""

import sys
import os

# Adicionar o diretório raiz ao path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from app.midia.midia_model import AgendaSemanal

def testar_midia_diretamente():
    """Testa a função da mídia diretamente"""
    
    app = create_app()
    
    with app.app_context():
        print("🔍 Teste direto da função mídia")
        print("=" * 40)
        
        try:
            # Verificar se existem dados na tabela AgendaSemanal
            agendas = AgendaSemanal.query.all()
            print(f"✅ Total de agendas: {len(agendas)}")
            
            # Simular a lógica da função listar_agenda
            from datetime import datetime, timedelta
            
            hoje = datetime.now().date()
            semana = hoje.isocalendar()[1]  # Semana atual
            ano = hoje.year
            
            print(f"✅ Data atual: {hoje}")
            print(f"✅ Semana: {semana}, Ano: {ano}")
            
            # Calcular datas da semana
            primeiro_dia_ano = datetime(ano, 1, 1).date()
            dias_para_semana = (semana - 1) * 7
            inicio_semana = primeiro_dia_ano + timedelta(days=dias_para_semana - primeiro_dia_ano.weekday())
            fim_semana = inicio_semana + timedelta(days=6)
            
            print(f"✅ Período: {inicio_semana} a {fim_semana}")
            
            # Query da agenda
            query = AgendaSemanal.query.filter(AgendaSemanal.ativo == True)
            agenda = query.order_by(AgendaSemanal.data_evento.asc()).all()
            
            print(f"✅ Query executada com sucesso: {len(agenda)} itens")
            
            # Testar render do template
            from flask import render_template
            tipos_evento = ['Culto', 'Reunião', 'Evento', 'Anúncio']
            semanas_ano = list(range(1, 53))
            
            # Tentar renderizar template
            resultado = render_template('midia/agenda/lista_agenda.html',
                                      agenda=agenda,
                                      tipos_evento=tipos_evento,
                                      semanas_ano=semanas_ano,
                                      semana_atual=semana,
                                      ano_atual=ano,
                                      tipo_evento_atual='',
                                      inicio_semana=inicio_semana,
                                      fim_semana=fim_semana)
            
            print("✅ Template renderizado com sucesso!")
            print(f"✅ Tamanho do HTML: {len(resultado)} caracteres")
            
            return True
            
        except Exception as e:
            print(f"❌ ERRO ENCONTRADO: {type(e).__name__}: {e}")
            import traceback
            traceback.print_exc()
            return False

if __name__ == "__main__":
    testar_midia_diretamente()