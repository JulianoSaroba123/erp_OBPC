#!/usr/bin/env python3
"""
Script para atualizar a tabela certificados no banco do Flask
"""

from app import create_app, db
import sqlite3
import os

def atualizar_tabela_flask():
    """Atualiza a tabela certificados no banco do Flask"""
    app = create_app()
    
    with app.app_context():
        # Pegar o caminho do banco do Flask
        database_url = app.config.get('SQLALCHEMY_DATABASE_URI')
        banco_path = database_url.replace('sqlite:///', '')
        
        print(f"🔧 Atualizando banco do Flask: {banco_path}")
        
        # Conectar diretamente ao banco do Flask
        conn = sqlite3.connect(banco_path)
        cursor = conn.cursor()
        
        try:
            # Verificar se as colunas existem
            cursor.execute("PRAGMA table_info(certificados)")
            colunas = [col[1] for col in cursor.fetchall()]
            print(f"📋 Colunas existentes: {colunas}")
            
            # Adicionar coluna genero se não existir
            if 'genero' not in colunas:
                print("➕ Adicionando coluna 'genero'...")
                cursor.execute("ALTER TABLE certificados ADD COLUMN genero VARCHAR(10)")
                
            # Adicionar coluna filiacao se não existir
            if 'filiacao' not in colunas:
                print("➕ Adicionando coluna 'filiacao'...")
                cursor.execute("ALTER TABLE certificados ADD COLUMN filiacao TEXT")
                
            # Adicionar coluna padrinhos se não existir
            if 'padrinhos' not in colunas:
                print("➕ Adicionando coluna 'padrinhos'...")
                cursor.execute("ALTER TABLE certificados ADD COLUMN padrinhos TEXT")
            
            conn.commit()
            
            # Verificar novamente
            cursor.execute("PRAGMA table_info(certificados)")
            colunas_final = [col[1] for col in cursor.fetchall()]
            print(f"✅ Colunas finais: {colunas_final}")
            
            # Adicionar certificados de exemplo
            print("\n🚀 Inserindo certificados de exemplo...")
            
            # Verificar se já há certificados
            cursor.execute("SELECT COUNT(*) FROM certificados")
            total = cursor.fetchone()[0]
            
            if total == 0:
                certificados = [
                    ("Ana Sofia Mendes", "Apresentação", "Feminino", "2025-10-15", "Pastor João Carlos", 
                     "Igreja OBPC - Tietê/SP", "Roberto Mendes e Sofia Cristina Mendes", "Paulo Santos e Maria Santos", 
                     "APRES-F-001", "Apresentação especial"),
                    
                    ("Pedro Henrique Costa", "Apresentação", "Masculino", "2025-10-20", "Pastor João Carlos",
                     "Igreja OBPC - Tietê/SP", "Carlos Costa e Helena Silva Costa", "José Roberto e Ana Carolina",
                     "APRES-M-001", "Apresentação especial"),
                    
                    ("Isabella Santos", "Apresentação", "Feminino", "2025-11-01", "Pastor João Carlos",
                     "Igreja OBPC - Tietê/SP", "Fernando Santos e Isabela Oliveira", "Marcos Silva e Fernanda Silva",
                     "APRES-F-002", "Apresentação especial"),
                    
                    ("Carlos Roberto Silva", "Batismo", "Masculino", "2025-09-15", "Pastor João Carlos",
                     "Igreja OBPC - Tietê/SP", "Roberto Carlos Silva e Maria Silva", "",
                     "BAT-M-001", "Batismo por imersão"),
                    
                    ("Mariana Oliveira", "Batismo", "Feminino", "2025-09-20", "Pastor João Carlos",
                     "Igreja OBPC - Tietê/SP", "João Oliveira e Mariana Costa", "",
                     "BAT-F-001", "Batismo por imersão"),
                    
                    ("João Paulo Santos", "Batismo", "Masculino", "2025-10-05", "Pastor João Carlos",
                     "Igreja OBPC - Tietê/SP", "Paulo Roberto Santos e Joana Santos", "",
                     "BAT-M-002", "Batismo por imersão")
                ]
                
                sql = """
                INSERT INTO certificados 
                (nome_pessoa, tipo_certificado, genero, data_evento, pastor_responsavel, 
                 local_evento, filiacao, padrinhos, numero_certificado, observacoes,
                 data_criacao, data_atualizacao)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'), datetime('now'))
                """
                
                for i, cert in enumerate(certificados, 1):
                    cursor.execute(sql, cert)
                    print(f"  ✅ {i}. {cert[0]} ({cert[1]} - {cert[2]})")
                
                conn.commit()
                
                # Verificar final
                cursor.execute("SELECT COUNT(*) FROM certificados")
                total_final = cursor.fetchone()[0]
                print(f"\n🎉 Total de certificados criados: {total_final}")
            else:
                print(f"ℹ️ Já existem {total} certificados no banco")
            
        except Exception as e:
            conn.rollback()
            print(f"❌ Erro: {e}")
            raise
        finally:
            conn.close()

if __name__ == "__main__":
    atualizar_tabela_flask()