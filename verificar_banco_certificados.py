#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sqlite3
import os

def verificar_banco():
    """Verifica o estado do banco de dados"""
    
    bancos = ['igreja.db', 'app_obpc.db']
    
    for banco in bancos:
        print(f"\n=== VERIFICANDO {banco} ===")
        
        if not os.path.exists(banco):
            print(f"❌ Banco {banco} não existe")
            continue
            
        tamanho = os.path.getsize(banco)
        print(f"📊 Tamanho: {tamanho} bytes")
        
        if tamanho == 0:
            print(f"⚠️ Banco {banco} está vazio")
            continue
            
        try:
            conn = sqlite3.connect(banco)
            cursor = conn.cursor()
            
            # Listar tabelas
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tabelas = cursor.fetchall()
            print(f"📋 Tabelas: {[t[0] for t in tabelas]}")
            
            # Verificar certificados se existir
            if any('certificados' in str(t) for t in tabelas):
                cursor.execute("SELECT COUNT(*) FROM certificados")
                total = cursor.fetchone()[0]
                print(f"📜 Total de certificados: {total}")
                
                if total > 0:
                    cursor.execute("SELECT id, nome_pessoa, tipo_certificado, genero FROM certificados LIMIT 3")
                    amostras = cursor.fetchall()
                    print(f"📋 Amostras:")
                    for amostra in amostras:
                        print(f"   - ID {amostra[0]}: {amostra[1]} ({amostra[2]}) - Gênero: {amostra[3] or 'Não definido'}")
            
            conn.close()
            
        except Exception as e:
            print(f"❌ Erro ao ler {banco}: {e}")
    
    print(f"\n=== CONCLUSÃO ===")
    print("Se não há certificados, precisa:")
    print("1. Criar/recriar as tabelas")
    print("2. Verificar se o Flask está usando o banco correto")
    print("3. Testar criação via interface web")

if __name__ == "__main__":
    verificar_banco()