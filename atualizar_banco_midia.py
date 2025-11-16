#!/usr/bin/env python3
"""
Script para atualizar banco de dados do módulo Mídia
Corrige estrutura das tabelas conforme o modelo unificado
"""

import sys
import os
from datetime import datetime

# Adicionar o diretório raiz ao Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from run import app
from app import db

def atualizar_banco_midia():
    """Atualiza estrutura do banco de dados do módulo Mídia"""
    
    with app.app_context():
        print("=== ATUALIZANDO BANCO DO MÓDULO MÍDIA ===")
        print()
        
        # Conectar ao banco
        try:
            connection = db.engine.connect()
            print("✅ Conectado ao banco de dados")
        except Exception as e:
            print(f"❌ Erro ao conectar: {str(e)}")
            return
        
        try:
            # 1. Verificar se tabelas existem
            print("\n🔍 VERIFICANDO TABELAS EXISTENTES:")
            
            result = connection.execute(db.text("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE '%agenda%' OR name LIKE '%certificado%' OR name LIKE '%carteira%'"))
            tabelas_existentes = [row[0] for row in result.fetchall()]
            
            for tabela in tabelas_existentes:
                print(f"   📋 {tabela}")
            
            # 2. Fazer backup das tabelas existentes (se necessário)
            print("\n💾 FAZENDO BACKUP (se necessário):")
            
            if 'agenda_semanal' in tabelas_existentes:
                try:
                    connection.execute(db.text("CREATE TABLE IF NOT EXISTS agenda_semanal_backup AS SELECT * FROM agenda_semanal"))
                    print("   ✅ Backup da agenda_semanal criado")
                except:
                    print("   ⚠️ Agenda semanal vazia ou backup já existe")
            
            if 'certificados' in tabelas_existentes:
                try:
                    connection.execute(db.text("CREATE TABLE IF NOT EXISTS certificados_backup AS SELECT * FROM certificados"))
                    print("   ✅ Backup dos certificados criado")
                except:
                    print("   ⚠️ Certificados vazio ou backup já existe")
            
            if 'carteiras_membro' in tabelas_existentes:
                try:
                    connection.execute(db.text("CREATE TABLE IF NOT EXISTS carteiras_membro_backup AS SELECT * FROM carteiras_membro"))
                    print("   ✅ Backup das carteiras criado")
                except:
                    print("   ⚠️ Carteiras vazio ou backup já existe")
            
            # 3. Remover tabelas antigas
            print("\n🗑️ REMOVENDO TABELAS ANTIGAS:")
            
            tabelas_para_remover = ['agenda_semanal', 'certificados', 'carteiras_membro']
            for tabela in tabelas_para_remover:
                if tabela in tabelas_existentes:
                    connection.execute(db.text(f"DROP TABLE IF EXISTS {tabela}"))
                    print(f"   ✅ Tabela {tabela} removida")
            
            # 4. Commit das mudanças
            connection.commit()
            
            # 5. Recriar tabelas com nova estrutura
            print("\n🔨 CRIANDO NOVAS TABELAS:")
            
            db.create_all()
            print("   ✅ Tabelas criadas com nova estrutura")
            
            # 6. Testar inserção básica
            print("\n🧪 TESTANDO NOVA ESTRUTURA:")
            
            from app.midia.midia_model import AgendaSemanal, Certificado, CarteiraMembro
            
            # Teste AgendaSemanal
            teste_agenda = AgendaSemanal(
                titulo="Teste de Agenda",
                data_evento=datetime.now().date(),
                tipo_evento="Teste"
            )
            db.session.add(teste_agenda)
            
            # Teste Certificado
            teste_certificado = Certificado(
                tipo_certificado="Batismo",
                nome_pessoa="Teste da Silva",
                data_evento=datetime.now().date(),
                pastor_responsavel="Pastor Teste"
            )
            db.session.add(teste_certificado)
            
            # Teste CarteiraMembro
            teste_carteira = CarteiraMembro(
                numero_carteira=CarteiraMembro.gerar_proximo_numero(),
                nome_completo="Teste dos Santos",
                data_nascimento=datetime(1990, 1, 1).date()
            )
            db.session.add(teste_carteira)
            
            db.session.commit()
            print("   ✅ Teste de inserção bem-sucedido")
            
            # 7. Limpar dados de teste
            db.session.delete(teste_agenda)
            db.session.delete(teste_certificado)
            db.session.delete(teste_carteira)
            db.session.commit()
            print("   ✅ Dados de teste removidos")
            
            print("\n✅ ATUALIZAÇÃO CONCLUÍDA COM SUCESSO!")
            print()
            print("🎯 PRÓXIMOS PASSOS:")
            print("   1. Execute: python testar_modulo_midia.py")
            print("   2. Execute: python run.py")
            print("   3. Teste: http://127.0.0.1:5000/midia/agenda")
            print()
            
        except Exception as e:
            connection.rollback()
            print(f"\n❌ Erro durante atualização: {str(e)}")
            import traceback
            traceback.print_exc()
            
        finally:
            connection.close()

if __name__ == "__main__":
    atualizar_banco_midia()