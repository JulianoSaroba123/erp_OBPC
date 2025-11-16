#!/usr/bin/env python3
"""
Script para restaurar dados via Flask context
"""

from app import create_app, db

def restaurar_via_flask():
    """Restaura dados através do contexto Flask"""
    print("🔧 RESTAURANDO DADOS VIA FLASK")
    print("=" * 40)
    
    app = create_app()
    
    with app.app_context():
        try:
            # Forçar criação de todas as tabelas
            print("📋 Criando/verificando todas as tabelas...")
            db.create_all()
            
            # Importar modelos disponíveis
            from app.eventos.eventos_model import Evento
            # from app.secretaria.secretaria_model import Configuracao
            
            # Verificar eventos
            total_eventos = Evento.query.count()
            print(f"📅 Eventos existentes: {total_eventos}")
            
            if total_eventos == 0:
                print("➕ Criando eventos de exemplo...")
                from datetime import datetime, date, time
                
                eventos = [
                    Evento(
                        titulo="Culto de Oração",
                        data_inicio=datetime(2025, 11, 6, 19, 30),
                        data_fim=datetime(2025, 11, 6, 21, 0),
                        local="Igreja OBPC - Tietê/SP",
                        responsavel="Pastor João Carlos",
                        descricao="Culto semanal de oração - toda quarta-feira"
                    ),
                    Evento(
                        titulo="Culto Dominical",
                        data_inicio=datetime(2025, 11, 10, 19, 0),
                        data_fim=datetime(2025, 11, 10, 21, 30),
                        local="Igreja OBPC - Tietê/SP",
                        responsavel="Pastor João Carlos",
                        descricao="Culto principal de domingo à noite"
                    ),
                    Evento(
                        titulo="Escola Bíblica Dominical",
                        data_inicio=datetime(2025, 11, 10, 9, 0),
                        data_fim=datetime(2025, 11, 10, 10, 0),
                        local="Igreja OBPC - Tietê/SP",
                        responsavel="Diácono Paulo",
                        descricao="Escola bíblica para todas as idades"
                    ),
                    Evento(
                        titulo="Reunião de Obreiros",
                        data_inicio=datetime(2025, 11, 12, 19, 30),
                        data_fim=datetime(2025, 11, 12, 21, 0),
                        local="Igreja OBPC - Tietê/SP",
                        responsavel="Pastor João Carlos",
                        descricao="Reunião mensal dos obreiros e liderança"
                    ),
                    Evento(
                        titulo="Culto de Ação de Graças",
                        data_inicio=datetime(2025, 11, 28, 19, 0),
                        data_fim=datetime(2025, 11, 28, 21, 30),
                        local="Igreja OBPC - Tietê/SP",
                        responsavel="Pastor João Carlos",
                        descricao="Culto especial de ação de graças"
                    )
                ]
                
                for evento in eventos:
                    db.session.add(evento)
                
                db.session.commit()
                print(f"  ✅ {len(eventos)} eventos criados")
            
            # Verificar configurações (usando SQL direto)
            print("⚙️ Verificando configurações...")
            
            # Usar SQL direto para inserir configurações básicas
            import sqlite3
            conn = sqlite3.connect('igreja.db')
            cursor = conn.cursor()
            
            cursor.execute("SELECT COUNT(*) FROM configuracoes")
            result = cursor.fetchone()
            total_config = result[0] if result else 0
            print(f"⚙️ Configurações existentes: {total_config}")
            
            if total_config == 0:
                print("➕ Criando configurações padrão...")
                
                configs = [
                    ("nome_igreja", "Igreja OBPC - Tietê/SP"),
                    ("endereco_igreja", "Rua Principal, 123 - Centro - Tietê/SP"),
                    ("telefone_igreja", "(15) 3285-0000"),
                    ("email_igreja", "contato@obpc.com.br"),
                    ("pastor_titular", "Pastor João Carlos"),
                    ("cnpj_igreja", "00.000.000/0001-00")
                ]
                
                for config in configs:
                    cursor.execute("INSERT OR IGNORE INTO configuracoes (chave, valor) VALUES (?, ?)", config)
                
                conn.commit()
                print(f"  ✅ {len(configs)} configurações criadas")
            
            conn.close()
            
            print("\n🎉 RESTAURAÇÃO VIA FLASK CONCLUÍDA!")
            print("✅ Agora você pode navegar pelas outras abas")
            print("✅ Dados básicos foram restaurados")
            
        except Exception as e:
            db.session.rollback()
            print(f"❌ Erro: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    restaurar_via_flask()