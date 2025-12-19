#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
import sqlite3
from datetime import datetime

# Adicionar o diretório raiz ao path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def criar_certificados_teste():
    """Cria certificados de teste para demonstrar os templates"""
    try:
        conn = sqlite3.connect('app_obpc.db')
        cursor = conn.cursor()
        
        # Criar certificado de apresentação com o novo template
        cursor.execute("""
            INSERT INTO certificados 
            (nome_pessoa, tipo_certificado, data_evento, local_evento, pastor_responsavel, padrinhos, observacoes)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            'Ana Sofia Mendes',
            'Apresentação',
            '2024-11-05',
            'Igreja OBPC Tietê',
            'Pastor Marcos Silva',
            'João Mendes e Maria Mendes',
            'Apresentação da pequena Ana com muito amor'
        ))
        
        apresentacao_id = cursor.lastrowid
        
        # Criar certificado de batismo para comparação
        cursor.execute("""
            INSERT INTO certificados 
            (nome_pessoa, tipo_certificado, data_evento, local_evento, pastor_responsavel, observacoes)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            'Carlos Roberto Santos',
            'Batismo',
            '2024-11-05',
            'Igreja OBPC Tietê',
            'Pastor Marcos Silva',
            'Batismo realizado com alegria'
        ))
        
        batismo_id = cursor.lastrowid
        
        conn.commit()
        conn.close()
        
        print(f"✅ Certificados de teste criados!")
        print(f"   - Apresentação (Minimalista) ID: {apresentacao_id}")
        print(f"   - Batismo (Azul) ID: {batismo_id}")
        
        return apresentacao_id, batismo_id
        
    except Exception as e:
        print(f"Erro ao criar certificados de teste: {e}")
        return None, None

def testar_templates():
    """Testa os diferentes templates"""
    print("=== TESTE DOS TEMPLATES DE CERTIFICADOS ===\n")
    
    # Criar certificados de teste
    apresentacao_id, batismo_id = criar_certificados_teste()
    
    if apresentacao_id and batismo_id:
        print(f"\n=== URLS PARA TESTE ===")
        print(f"\n🌸 APRESENTAÇÃO (Minimalista Azul/Rosa):")
        print(f"   Visualizar: http://127.0.0.1:5000/midia/certificados/visualizar/{apresentacao_id}")
        print(f"   PDF: http://127.0.0.1:5000/midia/certificados/pdf/{apresentacao_id}")
        
        print(f"\n💙 BATISMO (Modelo Azul):")
        print(f"   Visualizar: http://127.0.0.1:5000/midia/certificados/visualizar/{batismo_id}")
        print(f"   PDF: http://127.0.0.1:5000/midia/certificados/pdf/{batismo_id}")
        
        print(f"\n=== CARACTERÍSTICAS DO NOVO TEMPLATE ===")
        print(f"✨ Design minimalista com cores azul e rosa")
        print(f"📏 Logo MUITO maior no topo (120px altura)")
        print(f"🎨 Gradiente no nome da criança")
        print(f"👨‍👩‍👧‍👦 Campo de padrinhos em destaque")
        print(f"📖 Versículo bíblico apropriado")
        print(f"🎯 Layout limpo e moderno")
        
        print(f"\n=== COMPARAÇÃO ===")
        print(f"• Apresentação: Template minimalista (azul/rosa)")
        print(f"• Batismo: Template azul tradicional")
        print(f"• Ambos: Logo grande sem nome da igreja no cabeçalho")
    
    print("\n=== TESTE CONCLUÍDO ===")

if __name__ == "__main__":
    testar_templates()