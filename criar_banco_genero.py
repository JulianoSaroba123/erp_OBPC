#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
import sqlite3
from datetime import datetime

# Adicionar o diretório raiz ao path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def criar_banco_e_dados():
    """Cria banco e dados usando SQL direto"""
    try:
        conn = sqlite3.connect('igreja.db')
        cursor = conn.cursor()
        
        print("🔄 Verificando estrutura da tabela certificados...")
        cursor.execute("PRAGMA table_info(certificados)")
        colunas = cursor.fetchall()
        
        print("📋 Colunas existentes:")
        for coluna in colunas:
            print(f"   - {coluna[1]} ({coluna[2]})")
        
        # Verificar se a coluna gênero existe
        colunas_nomes = [coluna[1] for coluna in colunas]
        
        if 'genero' not in colunas_nomes:
            print("\n📝 Adicionando coluna 'genero'...")
            cursor.execute("ALTER TABLE certificados ADD COLUMN genero VARCHAR(10) DEFAULT 'masculino'")
            conn.commit()
            print("✅ Coluna 'genero' adicionada!")
        else:
            print("\n✅ Coluna 'genero' já existe!")
        
        # Limpar dados existentes
        cursor.execute("DELETE FROM certificados")
        print("\n🧹 Dados antigos removidos")
        
        # Inserir certificados de exemplo
        certificados = [
            ('Ana Sofia Mendes', 'Apresentação', 'feminino', '2024-11-05', 'Igreja OBPC Tietê', 'Pastor Marcos Silva', 'João Mendes e Maria Mendes', 'Apresentação da pequena Ana'),
            ('Pedro Henrique Costa', 'Apresentação', 'masculino', '2024-10-20', 'Igreja OBPC Tietê', 'Pastor Marcos Silva', 'Carlos Costa e Ana Costa', 'Apresentação do pequeno Pedro'),
            ('Isabella Santos', 'Apresentação', 'feminino', '2024-09-15', 'Igreja OBPC Tietê', 'Pastor Marcos Silva', 'Roberto Santos e Lucia Santos', 'Apresentação da pequena Isabella'),
            ('Carlos Roberto Silva', 'Batismo', 'masculino', '2024-11-03', 'Igreja OBPC Tietê', 'Pastor Marcos Silva', None, 'Batismo realizado com alegria'),
            ('Mariana Oliveira', 'Batismo', 'feminino', '2024-10-27', 'Igreja OBPC Tietê', 'Pastor Marcos Silva', None, 'Nova vida em Cristo'),
            ('João Paulo Santos', 'Batismo', 'masculino', '2024-10-13', 'Igreja OBPC Tietê', 'Pastor Marcos Silva', None, 'Testemunho público de fé'),
        ]
        
        print("\n📝 Inserindo certificados de exemplo...")
        for cert in certificados:
            cursor.execute("""
                INSERT INTO certificados 
                (nome_pessoa, tipo_certificado, genero, data_evento, local_evento, pastor_responsavel, padrinhos, observacoes, data_criacao)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (*cert, datetime.now()))
        
        conn.commit()
        
        # Verificar resultado
        cursor.execute("SELECT COUNT(*) FROM certificados")
        total = cursor.fetchone()[0]
        
        cursor.execute("SELECT nome_pessoa, tipo_certificado, genero FROM certificados ORDER BY id")
        certificados_resultado = cursor.fetchall()
        
        print(f"\n✅ {total} certificados criados com sucesso!")
        print("\n📋 Lista de certificados:")
        for nome, tipo, genero in certificados_resultado:
            icone = "👧" if genero == 'feminino' else "👦"
            print(f"   {icone} {nome} - {tipo} ({genero})")
        
        conn.close()
        
        print(f"\n🌐 TESTE NO NAVEGADOR:")
        print(f"Lista: http://127.0.0.1:5000/midia/certificados")
        print(f"Novo: http://127.0.0.1:5000/midia/certificados/novo")
        
        print(f"\n✨ PRÓXIMOS PASSOS:")
        print(f"1. Adicionar campo gênero no formulário")
        print(f"2. Atualizar templates para usar cores por gênero")
        print(f"3. Atualizar rotas para salvar gênero")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro: {e}")
        return False

if __name__ == "__main__":
    print("=== CRIANDO BANCO DE CERTIFICADOS COM GÊNERO ===\n")
    if criar_banco_e_dados():
        print("\n🎉 BANCO CONFIGURADO COM SUCESSO!")
    else:
        print("\n❌ ERRO NA CONFIGURAÇÃO!")