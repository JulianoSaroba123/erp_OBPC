#!/usr/bin/env python3
"""
Script de diagnóstico para resolver o problema da lista vazia
"""

import sqlite3
import os
from app import create_app, db
from app.midia.midia_model import Certificado

def diagnostico_completo():
    """Diagnóstico completo do problema"""
    print("🔍 DIAGNÓSTICO COMPLETO - LISTA VAZIA")
    print("=" * 50)
    
    # 1. Verificar arquivos de banco
    print("\n📁 VERIFICANDO ARQUIVOS DE BANCO:")
    for file in os.listdir('.'):
        if file.endswith('.db'):
            size = os.path.getsize(file)
            print(f"  - {file}: {size} bytes")
    
    # 2. Verificar banco direto (SQLite)
    print("\n🗄️ VERIFICANDO BANCO DIRETO (SQLite):")
    try:
        conn = sqlite3.connect('igreja.db')
        cursor = conn.cursor()
        
        # Verificar tabelas
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tabelas = [row[0] for row in cursor.fetchall()]
        print(f"  Tabelas: {tabelas}")
        
        if 'certificados' in tabelas:
            # Verificar estrutura
            cursor.execute("PRAGMA table_info(certificados)")
            colunas = [col[1] for col in cursor.fetchall()]
            print(f"  Colunas: {colunas}")
            
            # Verificar dados
            cursor.execute("SELECT COUNT(*) FROM certificados")
            total = cursor.fetchone()[0]
            print(f"  Total de certificados: {total}")
            
            if total > 0:
                cursor.execute("SELECT id, nome_pessoa, tipo_certificado, genero FROM certificados LIMIT 5")
                print("  Primeiros certificados:")
                for cert in cursor.fetchall():
                    print(f"    - ID: {cert[0]} | {cert[1]} | {cert[2]} | {cert[3]}")
        
        conn.close()
    except Exception as e:
        print(f"  ❌ Erro SQLite: {e}")
    
    # 3. Verificar Flask/SQLAlchemy
    print("\n🌐 VERIFICANDO FLASK/SQLALCHEMY:")
    try:
        app = create_app()
        with app.app_context():
            # Verificar configuração
            db_url = app.config.get('SQLALCHEMY_DATABASE_URI')
            print(f"  URL configurada: {db_url}")
            
            # Forçar criação de tabelas
            print("  Criando/atualizando tabelas...")
            db.create_all()
            
            # Tentar consultar
            try:
                total_flask = Certificado.query.count()
                print(f"  Certificados via Flask: {total_flask}")
                
                if total_flask == 0:
                    print("  🚨 PROBLEMA: Flask não vê certificados!")
                    print("  💡 Tentando inserir via Flask...")
                    
                    # Inserir via Flask
                    from datetime import date
                    cert_teste = Certificado(
                        nome_pessoa="TESTE VIA FLASK",
                        tipo_certificado="Apresentação",
                        genero="Masculino",
                        data_evento=date(2025, 11, 5),
                        pastor_responsavel="Pastor Teste",
                        local_evento="Igreja Teste",
                        filiacao="Pai Teste e Mãe Teste",
                        numero_certificado="TESTE-001"
                    )
                    
                    db.session.add(cert_teste)
                    db.session.commit()
                    
                    # Verificar novamente
                    total_apos = Certificado.query.count()
                    print(f"  ✅ Total após inserção: {total_apos}")
                    
                else:
                    print("  ✅ Flask encontrou certificados!")
                    # Listar alguns
                    certs = Certificado.query.limit(5).all()
                    for cert in certs:
                        print(f"    - {cert.nome_pessoa} ({cert.tipo_certificado})")
                        
            except Exception as e:
                print(f"  ❌ Erro consulta Flask: {e}")
                
                # Tentar recriar tabelas
                print("  🔧 Tentando recriar tabelas...")
                try:
                    db.drop_all()
                    db.create_all()
                    print("  ✅ Tabelas recriadas!")
                except Exception as e2:
                    print(f"  ❌ Erro ao recriar: {e2}")
    
    except Exception as e:
        print(f"  ❌ Erro Flask: {e}")
    
    print("\n📊 DIAGNÓSTICO CONCLUÍDO")

if __name__ == "__main__":
    diagnostico_completo()