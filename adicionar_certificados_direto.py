#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para adicionar certificados diretamente ao banco do Flask
"""

import sqlite3
import os
from datetime import datetime

def main():
    print("🚀 ADICIONANDO CERTIFICADOS DIRETAMENTE AO BANCO")
    print("=" * 55)
    
    # Primeiro, vamos verificar onde está o banco do Flask
    bancos_possiveis = [
        "igreja.db",
        "instance/igreja.db",
        "app/igreja.db"
    ]
    
    banco_encontrado = None
    for banco in bancos_possiveis:
        if os.path.exists(banco):
            print(f"📁 Encontrado: {banco}")
            banco_encontrado = banco
            break
    
    if not banco_encontrado:
        print("❌ Nenhum banco encontrado!")
        return
    
    print(f"🎯 Usando banco: {banco_encontrado}")
    
    try:
        conn = sqlite3.connect(banco_encontrado)
        cursor = conn.cursor()
        
        # Verificar se a tabela existe
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='certificados'")
        if not cursor.fetchone():
            print("❌ Tabela certificados não encontrada!")
            return
        
        # Verificar quantos registros existem
        cursor.execute("SELECT COUNT(*) FROM certificados")
        total_atual = cursor.fetchone()[0]
        print(f"📊 Certificados atuais: {total_atual}")
        
        # Limpar tabela se necessário
        if total_atual > 0:
            print("🧹 Limpando registros antigos...")
            cursor.execute("DELETE FROM certificados")
        
        # Inserir novos certificados
        print("📝 Inserindo certificados de exemplo...")
        
        certificados = [
            ("Ana Sofia Mendes", "Apresentação", "Feminino", "2025-10-15", "Pastor João Carlos", 
             "Igreja OBPC - Tietê/SP", "Apresentação especial", "APRES-F-001", 
             "Roberto Mendes e Sofia Cristina Mendes", "Paulo Santos e Maria Santos",
             datetime.now(), datetime.now()),
            
            ("Pedro Henrique Costa", "Apresentação", "Masculino", "2025-10-20", "Pastor João Carlos",
             "Igreja OBPC - Tietê/SP", "Apresentação especial", "APRES-M-001",
             "Carlos Costa e Helena Silva Costa", "José Roberto e Ana Carolina", 
             datetime.now(), datetime.now()),
            
            ("Isabella Santos", "Apresentação", "Feminino", "2025-11-01", "Pastor João Carlos",
             "Igreja OBPC - Tietê/SP", "Apresentação especial", "APRES-F-002",
             "Fernando Santos e Isabela Oliveira", "Marcos Silva e Fernanda Silva",
             datetime.now(), datetime.now()),
            
            ("Carlos Roberto Silva", "Batismo", "Masculino", "2025-09-15", "Pastor João Carlos",
             "Igreja OBPC - Tietê/SP", "Batismo por imersão", "BAT-M-001",
             "Roberto Carlos Silva e Maria Silva", "",
             datetime.now(), datetime.now()),
            
            ("Mariana Oliveira", "Batismo", "Feminino", "2025-09-20", "Pastor João Carlos",
             "Igreja OBPC - Tietê/SP", "Batismo por imersão", "BAT-F-001",
             "João Oliveira e Mariana Costa", "",
             datetime.now(), datetime.now()),
            
            ("João Paulo Santos", "Batismo", "Masculino", "2025-10-05", "Pastor João Carlos",
             "Igreja OBPC - Tietê/SP", "Batismo por imersão", "BAT-M-002",
             "Paulo Roberto Santos e Joana Santos", "",
             datetime.now(), datetime.now())
        ]
        
        # SQL de inserção
        sql = """
        INSERT INTO certificados (
            nome_pessoa, tipo_certificado, genero, data_evento, pastor_responsavel,
            local_evento, observacoes, numero_certificado, filiacao, padrinhos,
            data_criacao, data_atualizacao
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        
        cursor.executemany(sql, certificados)
        conn.commit()
        
        # Verificar resultado
        cursor.execute("SELECT COUNT(*) FROM certificados")
        total_final = cursor.fetchone()[0]
        
        print(f"✅ {len(certificados)} certificados inseridos!")
        print(f"📊 Total final: {total_final}")
        
        # Listar certificados inseridos
        cursor.execute("""
            SELECT nome_pessoa, tipo_certificado, genero, data_evento, filiacao, padrinhos
            FROM certificados 
            ORDER BY id
        """)
        
        registros = cursor.fetchall()
        
        print("\n📋 CERTIFICADOS CRIADOS:")
        for i, (nome, tipo, genero, data, filiacao, padrinhos) in enumerate(registros, 1):
            cor = "🔵" if genero == "Masculino" else ("🌸" if genero == "Feminino" else "💜")
            print(f"{i}. {cor} {nome} ({tipo})")
            print(f"   📅 {data} | Gênero: {genero}")
            if filiacao:
                print(f"   👨‍👩‍👧‍👦 {filiacao}")
            if padrinhos:
                print(f"   🤝 {padrinhos}")
            print()
        
        conn.close()
        
        print("🎉 CERTIFICADOS ADICIONADOS COM SUCESSO!")
        print("🔄 Agora atualize a página no navegador!")
        print("🌐 URL: http://127.0.0.1:5000/midia/certificados")
        
    except Exception as e:
        print(f"❌ Erro: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()