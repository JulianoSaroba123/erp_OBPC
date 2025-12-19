#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
import sqlite3
from datetime import datetime

# Adicionar o diretório raiz ao path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def adicionar_coluna_genero():
    """Adiciona a coluna de gênero na tabela certificados"""
    try:
        conn = sqlite3.connect('igreja.db')
        cursor = conn.cursor()
        
        # Verificar se a coluna já existe
        cursor.execute("PRAGMA table_info(certificados)")
        colunas = [coluna[1] for coluna in cursor.fetchall()]
        
        if 'genero' not in colunas:
            print("📝 Adicionando coluna 'genero' na tabela certificados...")
            cursor.execute("ALTER TABLE certificados ADD COLUMN genero VARCHAR(10) DEFAULT 'masculino'")
            conn.commit()
            print("✅ Coluna 'genero' adicionada com sucesso!")
        else:
            print("ℹ️ Coluna 'genero' já existe na tabela.")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Erro ao adicionar coluna gênero: {e}")

def criar_certificados_exemplo():
    """Cria certificados de exemplo com diferentes gêneros"""
    try:
        conn = sqlite3.connect('igreja.db')
        cursor = conn.cursor()
        
        # Limpar certificados existentes
        cursor.execute("DELETE FROM certificados")
        
        certificados_exemplo = [
            # Apresentações
            ('Ana Sofia Mendes', 'Apresentação', '2024-11-05', 'Igreja OBPC Tietê', 'Pastor Marcos Silva', 'João Mendes e Maria Mendes', 'Apresentação da pequena Ana', 'feminino'),
            ('Pedro Henrique Costa', 'Apresentação', '2024-10-20', 'Igreja OBPC Tietê', 'Pastor Marcos Silva', 'Carlos Costa e Ana Costa', 'Apresentação do pequeno Pedro', 'masculino'),
            ('Isabella Santos', 'Apresentação', '2024-09-15', 'Igreja OBPC Tietê', 'Pastor Marcos Silva', 'Roberto Santos e Lucia Santos', 'Apresentação da pequena Isabella', 'feminino'),
            
            # Batismos
            ('Carlos Roberto Silva', 'Batismo', '2024-11-03', 'Igreja OBPC Tietê', 'Pastor Marcos Silva', None, 'Batismo realizado com alegria', 'masculino'),
            ('Mariana Oliveira', 'Batismo', '2024-10-27', 'Igreja OBPC Tietê', 'Pastor Marcos Silva', None, 'Nova vida em Cristo', 'feminino'),
            ('João Paulo Santos', 'Batismo', '2024-10-13', 'Igreja OBPC Tietê', 'Pastor Marcos Silva', None, 'Testemunho público de fé', 'masculino'),
        ]
        
        for cert in certificados_exemplo:
            cursor.execute("""
                INSERT INTO certificados 
                (nome_pessoa, tipo_certificado, data_evento, local_evento, pastor_responsavel, padrinhos, observacoes, genero, data_criacao)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (*cert, datetime.now()))
        
        conn.commit()
        conn.close()
        
        print(f"✅ {len(certificados_exemplo)} certificados de exemplo criados!")
        print("   - 3 Apresentações (2 feminino, 1 masculino)")
        print("   - 3 Batismos (2 masculino, 1 feminino)")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro ao criar certificados de exemplo: {e}")
        return False

def verificar_certificados():
    """Verifica certificados no banco"""
    try:
        conn = sqlite3.connect('igreja.db')
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM certificados")
        total = cursor.fetchone()[0]
        
        cursor.execute("SELECT nome_pessoa, tipo_certificado, genero FROM certificados ORDER BY id DESC LIMIT 6")
        certificados = cursor.fetchall()
        
        print(f"\n📊 Total de certificados: {total}")
        if certificados:
            print("📋 Últimos certificados:")
            for nome, tipo, genero in certificados:
                icone = "👧" if genero == 'feminino' else "👦"
                print(f"   {icone} {nome} - {tipo} ({genero})")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Erro ao verificar certificados: {e}")

if __name__ == "__main__":
    print("=== CONFIGURANDO BANCO DE CERTIFICADOS ===\n")
    
    # Adicionar coluna de gênero
    adicionar_coluna_genero()
    
    # Criar certificados de exemplo
    print("\n📝 Criando certificados de exemplo...")
    if criar_certificados_exemplo():
        print("\n🔍 Verificando resultado...")
        verificar_certificados()
        
        print(f"\n🌐 TESTE NO NAVEGADOR:")
        print(f"Lista: http://127.0.0.1:5000/midia/certificados")
        print(f"Novo: http://127.0.0.1:5000/midia/certificados/novo")
        
        print(f"\n✨ RECURSOS IMPLEMENTADOS:")
        print(f"• Campo gênero adicionado (masculino/feminino)")
        print(f"• Templates diferenciados por gênero e tipo")
        print(f"• Apresentação: azul (masculino) / rosa (feminino)")
        print(f"• Batismo: template azul tradicional")
        
    print("\n🎉 CONFIGURAÇÃO CONCLUÍDA!")