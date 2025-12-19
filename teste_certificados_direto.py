#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
import sqlite3
from datetime import datetime

# Adicionar o diretório raiz ao path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def criar_certificado_teste_direto():
    """Cria um certificado de teste diretamente no banco"""
    try:
        conn = sqlite3.connect('igreja.db')
        cursor = conn.cursor()
        
        # Inserir certificado de teste
        cursor.execute("""
            INSERT INTO certificados 
            (nome_pessoa, tipo_certificado, genero, data_evento, local_evento, pastor_responsavel, padrinhos, observacoes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            'Ana Sofia Mendes',
            'Apresentação',
            'Feminino',
            '2024-11-05',
            'Igreja OBPC Tietê',
            'Pastor Marcos Silva',
            'João Mendes e Maria Mendes',
            'Apresentação da pequena Ana com muito amor'
        ))
        
        apresentacao_id = cursor.lastrowid
        
        # Inserir certificado de batismo
        cursor.execute("""
            INSERT INTO certificados 
            (nome_pessoa, tipo_certificado, genero, data_evento, local_evento, pastor_responsavel, observacoes)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            'Carlos Roberto Santos',
            'Batismo',
            'Masculino',
            '2024-11-05',
            'Igreja OBPC Tietê',
            'Pastor Marcos Silva',
            'Batismo realizado com alegria'
        ))
        
        batismo_id = cursor.lastrowid
        
        conn.commit()
        conn.close()
        
        print(f"✅ Certificados de teste criados!")
        print(f"   - Apresentação (Feminino) ID: {apresentacao_id}")
        print(f"   - Batismo (Masculino) ID: {batismo_id}")
        
        # Verificar se foram salvos
        conn = sqlite3.connect('igreja.db')
        cursor = conn.cursor()
        cursor.execute("SELECT id, nome_pessoa, tipo_certificado, genero FROM certificados")
        certificados = cursor.fetchall()
        
        print(f"\n📋 Certificados no banco:")
        for cert in certificados:
            print(f"   - ID {cert[0]}: {cert[1]} ({cert[2]}) - {cert[3]}")
        
        conn.close()
        
        return apresentacao_id, batismo_id
        
    except Exception as e:
        print(f"❌ Erro ao criar certificados: {e}")
        return None, None

if __name__ == "__main__":
    print("=== CRIANDO CERTIFICADOS DE TESTE ===\n")
    criar_certificado_teste_direto()
    
    print(f"\n=== TESTE NO NAVEGADOR ===")
    print(f"Acesse: http://127.0.0.1:5000/midia/certificados")
    print(f"Os certificados devem aparecer na lista agora!")