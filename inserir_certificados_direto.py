#!/usr/bin/env python3
"""
Script para inserir certificados diretamente via SQLite (sem Flask)
"""

import sqlite3
from datetime import date

def inserir_certificados_direto():
    """Insere certificados diretamente no SQLite"""
    
    # Conectar ao banco
    conn = sqlite3.connect('igreja.db')
    cursor = conn.cursor()
    
    try:
        # Verificar quantos certificados existem
        cursor.execute('SELECT COUNT(*) FROM certificados')
        total_atual = cursor.fetchone()[0]
        print(f"📊 Total atual de certificados: {total_atual}")
        
        if total_atual > 0:
            print(f"✅ Já existem {total_atual} certificados!")
            cursor.execute('SELECT id, nome_pessoa, tipo_certificado FROM certificados LIMIT 5')
            for cert in cursor.fetchall():
                print(f"  - ID: {cert[0]} | {cert[1]} | {cert[2]}")
            return
        
        print("🚀 Inserindo certificados de exemplo...")
        
        # Certificados para inserir
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
        
        # SQL para inserir
        sql = """
        INSERT INTO certificados 
        (nome_pessoa, tipo_certificado, genero, data_evento, pastor_responsavel, 
         local_evento, filiacao, padrinhos, numero_certificado, observacoes,
         data_criacao, data_atualizacao)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'), datetime('now'))
        """
        
        # Inserir todos
        for i, cert in enumerate(certificados, 1):
            cursor.execute(sql, cert)
            print(f"  ✅ {i}. {cert[0]} ({cert[1]} - {cert[2]})")
        
        # Confirmar no banco
        conn.commit()
        
        # Verificar se foram salvos
        cursor.execute('SELECT COUNT(*) FROM certificados')
        total_final = cursor.fetchone()[0]
        print(f"\n🎉 Sucesso! Total de certificados: {total_final}")
        
        # Listar todos para confirmar
        print("\n📋 Certificados criados:")
        cursor.execute('SELECT id, nome_pessoa, tipo_certificado, genero FROM certificados')
        for cert in cursor.fetchall():
            print(f"  - ID: {cert[0]} | {cert[1]} | {cert[2]} | {cert[3]}")
            
    except Exception as e:
        conn.rollback()
        print(f"❌ Erro: {e}")
        raise
    finally:
        conn.close()

if __name__ == "__main__":
    inserir_certificados_direto()