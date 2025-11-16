#!/usr/bin/env python3
"""
Script para restaurar dados perdidos após recriação das tabelas
"""

import sqlite3
from datetime import datetime, date
import json

def restaurar_dados_sistema():
    """Restaura dados essenciais do sistema"""
    print("🔧 RESTAURANDO DADOS DO SISTEMA")
    print("=" * 40)
    
    conn = sqlite3.connect('igreja.db')
    cursor = conn.cursor()
    
    try:
        # 1. Verificar quais tabelas existem
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tabelas = [row[0] for row in cursor.fetchall()]
        print(f"📋 Tabelas existentes: {len(tabelas)}")
        
        # 2. Restaurar dados de eventos se a tabela estiver vazia
        if 'eventos' in tabelas:
            cursor.execute("SELECT COUNT(*) FROM eventos")
            total_eventos = cursor.fetchone()[0]
            print(f"📅 Eventos existentes: {total_eventos}")
            
            if total_eventos == 0:
                print("➕ Criando eventos de exemplo...")
                eventos_exemplo = [
                    ("Culto de Oração", "2025-11-06", "19:30", "21:00", "Igreja OBPC", "Culto", "Pastor João", "Culto semanal de oração"),
                    ("Culto de Domingo", "2025-11-10", "19:00", "21:30", "Igreja OBPC", "Culto", "Pastor João", "Culto dominical"),
                    ("Escola Bíblica", "2025-11-10", "09:00", "10:00", "Igreja OBPC", "Ensino", "Diácono Paulo", "Escola bíblica dominical"),
                    ("Reunião de Obreiros", "2025-11-12", "19:30", "21:00", "Igreja OBPC", "Reunião", "Pastor João", "Reunião mensal dos obreiros"),
                    ("Culto de Ação de Graças", "2025-11-28", "19:00", "21:30", "Igreja OBPC", "Culto Especial", "Pastor João", "Culto especial de ação de graças")
                ]
                
                for evento in eventos_exemplo:
                    cursor.execute("""
                        INSERT INTO eventos 
                        (titulo, data_evento, hora_inicio, hora_fim, local, tipo_evento, responsavel, descricao, ativo, data_criacao)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, 1, datetime('now'))
                    """, evento)
                print(f"  ✅ {len(eventos_exemplo)} eventos criados")
        
        # 3. Verificar e restaurar membros
        if 'membros' in tabelas:
            cursor.execute("SELECT COUNT(*) FROM membros")
            total_membros = cursor.fetchone()[0]
            print(f"👥 Membros existentes: {total_membros}")
        
        # 4. Verificar e restaurar obreiros  
        if 'obreiros' in tabelas:
            cursor.execute("SELECT COUNT(*) FROM obreiros")
            total_obreiros = cursor.fetchone()[0]
            print(f"⛪ Obreiros existentes: {total_obreiros}")
        
        # 5. Verificar configurações
        if 'configuracoes' in tabelas:
            cursor.execute("SELECT COUNT(*) FROM configuracoes")
            total_config = cursor.fetchone()[0]
            print(f"⚙️ Configurações existentes: {total_config}")
            
            if total_config == 0:
                print("➕ Criando configurações padrão...")
                configs = [
                    ("nome_igreja", "Igreja OBPC - Tietê/SP"),
                    ("endereco_igreja", "Rua Principal, 123 - Centro - Tietê/SP"),
                    ("telefone_igreja", "(15) 3285-0000"),
                    ("email_igreja", "contato@obpc.com.br"),
                    ("pastor_titular", "Pastor João Carlos"),
                    ("cnpj_igreja", "00.000.000/0001-00"),
                    ("cor_primaria", "#2E7D32"),
                    ("cor_secundaria", "#1565C0")
                ]
                
                for config in configs:
                    cursor.execute("INSERT INTO configuracoes (chave, valor) VALUES (?, ?)", config)
                print(f"  ✅ {len(configs)} configurações criadas")
        
        # 6. Verificar lancamentos financeiros
        if 'lancamentos' in tabelas:
            cursor.execute("SELECT COUNT(*) FROM lancamentos")
            total_lancamentos = cursor.fetchone()[0]
            print(f"💰 Lançamentos financeiros: {total_lancamentos}")
        
        # 7. Verificar agenda semanal
        if 'agenda_semanal' in tabelas:
            cursor.execute("SELECT COUNT(*) FROM agenda_semanal")
            total_agenda = cursor.fetchone()[0]
            print(f"📆 Agenda semanal: {total_agenda}")
            
            if total_agenda == 0:
                print("➕ Criando agenda semanal padrão...")
                agenda_exemplo = [
                    ("Culto de Oração", "2025-11-06", "19:30", "21:00", "Igreja OBPC", "Toda quarta-feira", "Culto", "Pastor João"),
                    ("Culto Dominical", "2025-11-10", "19:00", "21:30", "Igreja OBPC", "Todo domingo à noite", "Culto", "Pastor João"),
                    ("Escola Bíblica", "2025-11-10", "09:00", "10:00", "Igreja OBPC", "Todo domingo de manhã", "Ensino", "Professores")
                ]
                
                for item in agenda_exemplo:
                    cursor.execute("""
                        INSERT INTO agenda_semanal 
                        (titulo, data_evento, hora_inicio, hora_fim, local, descricao, tipo_evento, responsavel, ativo, data_criacao)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, 1, datetime('now'))
                    """, item)
                print(f"  ✅ {len(agenda_exemplo)} itens de agenda criados")
        
        # 8. Verificar departamentos
        if 'departamentos' in tabelas:
            cursor.execute("SELECT COUNT(*) FROM departamentos")
            total_dept = cursor.fetchone()[0]
            print(f"🏛️ Departamentos: {total_dept}")
            
            if total_dept == 0:
                print("➕ Criando departamentos padrão...")
                departamentos = [
                    ("Mídia e Comunicação", "Responsável pela comunicação e mídia da igreja", "Ativo"),
                    ("Louvor e Adoração", "Ministério de música e louvor", "Ativo"),
                    ("Escola Bíblica", "Ensino e educação cristã", "Ativo"),
                    ("Diaconia", "Assistência social e cuidado pastoral", "Ativo"),
                    ("Evangelismo", "Evangelização e missões", "Ativo"),
                    ("Jovens", "Ministério voltado aos jovens", "Ativo"),
                    ("Crianças", "Ministério infantil", "Ativo")
                ]
                
                for dept in departamentos:
                    cursor.execute("""
                        INSERT INTO departamentos (nome, descricao, status, data_criacao)
                        VALUES (?, ?, ?, datetime('now'))
                    """, dept)
                print(f"  ✅ {len(departamentos)} departamentos criados")
        
        conn.commit()
        print("\n🎉 RESTAURAÇÃO CONCLUÍDA!")
        print("✅ Dados básicos do sistema foram restaurados")
        print("✅ Você pode agora navegar pelas outras abas")
        
    except Exception as e:
        conn.rollback()
        print(f"❌ Erro durante restauração: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    restaurar_dados_sistema()