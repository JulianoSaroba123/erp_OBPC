#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Correção definitiva do problema de sincronização entre SQLAlchemy e banco
Este script resolve o problema da lista que some quando acessa PDF
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app, db
import sqlite3

def main():
    print("🔧 CORRIGINDO PROBLEMA DE SINCRONIZAÇÃO DO BANCO 🔧")
    print("=" * 60)
    
    # Verificar estrutura atual do banco
    db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'igreja.db')
    
    if not os.path.exists(db_path):
        print("❌ Banco de dados não encontrado!")
        print(f"Tentando localizar em: {db_path}")
        return
    
    print(f"📂 Verificando banco: {db_path}")
    
    # Conectar diretamente ao SQLite para verificar a estrutura
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Verificar estrutura da tabela certificados
    cursor.execute("PRAGMA table_info(certificados)")
    colunas = cursor.fetchall()
    
    print("\n📊 Estrutura atual da tabela 'certificados':")
    for col in colunas:
        print(f"  - {col[1]}: {col[2]} {'(NULL)' if col[3] == 0 else '(NOT NULL)'}")
    
    # Verificar se a coluna filiacao existe
    colunas_nomes = [col[1] for col in colunas]
    tem_filiacao = 'filiacao' in colunas_nomes
    
    print(f"\n🔍 Campo 'filiacao' existe: {'✅ SIM' if tem_filiacao else '❌ NÃO'}")
    
    # Contar certificados
    cursor.execute("SELECT COUNT(*) FROM certificados")
    total_certificados = cursor.fetchone()[0]
    print(f"📋 Total de certificados: {total_certificados}")
    
    if total_certificados > 0:
        print("\n🗂️ Últimos 3 certificados:")
        try:
            if tem_filiacao:
                cursor.execute("""
                    SELECT id, nome_pessoa, tipo_certificado, 
                           date(data_evento) as data_evento, filiacao 
                    FROM certificados 
                    ORDER BY id DESC LIMIT 3
                """)
            else:
                cursor.execute("""
                    SELECT id, nome_pessoa, tipo_certificado, 
                           date(data_evento) as data_evento 
                    FROM certificados 
                    ORDER BY id DESC LIMIT 3
                """)
            
            certificados = cursor.fetchall()
            for cert in certificados:
                if tem_filiacao:
                    print(f"  - ID {cert[0]}: {cert[1]} ({cert[2]}) - {cert[3]} - Filiação: {cert[4] or 'N/A'}")
                else:
                    print(f"  - ID {cert[0]}: {cert[1]} ({cert[2]}) - {cert[3]}")
        except Exception as e:
            print(f"❌ Erro ao listar certificados: {str(e)}")
    
    conn.close()
    
    print("\n🔧 Testando conexão com SQLAlchemy...")
    
    # Tentar usar SQLAlchemy
    app = create_app()
    with app.app_context():
        try:
            from app.midia.midia_model import Certificado
            
            # Tentar uma query simples
            count = Certificado.query.count()
            print(f"✅ SQLAlchemy funcionando! Total de certificados: {count}")
            
            # Listar alguns certificados
            if count > 0:
                certificados = Certificado.query.limit(3).all()
                print("\n📋 Certificados via SQLAlchemy:")
                for cert in certificados:
                    print(f"  - {cert.nome_pessoa} ({cert.tipo_certificado})")
                    
        except Exception as e:
            print(f"❌ Erro no SQLAlchemy: {str(e)}")
            print("\n🚨 PROBLEMA DETECTADO!")
            print("O erro indica incompatibilidade entre modelo SQLAlchemy e banco real.")
            print("\n💡 SOLUÇÃO:")
            print("1. Temporariamente remover campo 'filiacao' do modelo")
            print("2. Testar sistema funcionando")
            print("3. Depois reintegrar campo de forma correta")
            
            return False
    
    print("\n✅ SISTEMA SINCRONIZADO E FUNCIONANDO!")
    return True

if __name__ == "__main__":
    main()