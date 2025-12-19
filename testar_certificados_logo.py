#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
import sqlite3
from datetime import datetime

# Adicionar o diretório raiz ao path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def verificar_certificados():
    """Verifica certificados existentes no banco"""
    try:
        conn = sqlite3.connect('app_obpc.db')
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, nome_pessoa, tipo_certificado, data_evento, padrinhos 
            FROM certificados 
            ORDER BY id DESC 
            LIMIT 5
        """)
        
        certificados = cursor.fetchall()
        
        if certificados:
            print("=== CERTIFICADOS ENCONTRADOS ===")
            for cert in certificados:
                id_cert, nome, tipo, data_evento, padrinhos = cert
                print(f"ID: {id_cert}")
                print(f"Nome: {nome}")
                print(f"Tipo: {tipo}")
                print(f"Data: {data_evento}")
                if padrinhos:
                    print(f"Padrinhos: {padrinhos}")
                print("-" * 40)
                
                # URLs para testar
                print(f"URL Visualizar: http://127.0.0.1:5000/midia/certificados/visualizar/{id_cert}")
                print(f"URL PDF: http://127.0.0.1:5000/midia/certificados/pdf/{id_cert}")
                print("=" * 50)
        else:
            print("Nenhum certificado encontrado.")
            
        conn.close()
        
    except Exception as e:
        print(f"Erro ao verificar certificados: {e}")

def criar_certificado_teste():
    """Cria um certificado de teste se não existir"""
    try:
        conn = sqlite3.connect('app_obpc.db')
        cursor = conn.cursor()
        
        # Criar certificado de batismo
        cursor.execute("""
            INSERT INTO certificados 
            (nome_pessoa, tipo_certificado, data_evento, local_evento, pastor_responsavel, observacoes)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            'João da Silva',
            'Batismo',
            '2024-11-05',
            'Igreja OBPC Tietê',
            'Pastor Marcos',
            'Batismo realizado com alegria'
        ))
        
        batismo_id = cursor.lastrowid
        
        # Criar certificado de apresentação com padrinhos
        cursor.execute("""
            INSERT INTO certificados 
            (nome_pessoa, tipo_certificado, data_evento, local_evento, pastor_responsavel, padrinhos, observacoes)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            'Maria Eduarda Santos',
            'Apresentação',
            '2024-11-05',
            'Igreja OBPC Tietê',
            'Pastor Marcos',
            'João Santos e Ana Santos',
            'Apresentação da pequena Maria'
        ))
        
        apresentacao_id = cursor.lastrowid
        
        conn.commit()
        conn.close()
        
        print(f"✅ Certificados de teste criados!")
        print(f"   - Batismo ID: {batismo_id}")
        print(f"   - Apresentação ID: {apresentacao_id}")
        
        return batismo_id, apresentacao_id
        
    except Exception as e:
        print(f"Erro ao criar certificados de teste: {e}")
        return None, None

if __name__ == "__main__":
    print("=== TESTE DOS CERTIFICADOS COM LOGO MAIOR ===\n")
    
    # Verificar certificados existentes
    verificar_certificados()
    
    # Criar alguns certificados de teste
    print("\n=== CRIANDO CERTIFICADOS DE TESTE ===")
    batismo_id, apresentacao_id = criar_certificado_teste()
    
    if batismo_id and apresentacao_id:
        print(f"\n=== TESTE DAS URLS ===")
        print(f"Abra no navegador:")
        print(f"Batismo: http://127.0.0.1:5000/midia/certificados/visualizar/{batismo_id}")
        print(f"Apresentação: http://127.0.0.1:5000/midia/certificados/visualizar/{apresentacao_id}")
        print(f"\nPDFs diretos:")
        print(f"Batismo PDF: http://127.0.0.1:5000/midia/certificados/pdf/{batismo_id}")
        print(f"Apresentação PDF: http://127.0.0.1:5000/midia/certificados/pdf/{apresentacao_id}")
    
    print("\n=== TESTE CONCLUÍDO ===")