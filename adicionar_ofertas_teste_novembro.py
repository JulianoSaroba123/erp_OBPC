#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Adicionar dados de teste para novembro 2025
"""

import sqlite3
from datetime import datetime

def adicionar_ofertas_novembro():
    """Adiciona ofertas alçadas de teste no mês de novembro"""
    
    banco_path = 'f:/Ano 2025/Ano 2025/ERP_OBPC/igreja.db'
    
    print("➕ ADICIONANDO OFERTAS DE TESTE - NOVEMBRO 2025")
    print("=" * 60)
    
    try:
        conn = sqlite3.connect(banco_path)
        cursor = conn.cursor()
        
        # Dados de teste para novembro
        ofertas_teste = [
            ('2025-11-10', 'Oferta Alçada', 'Oferta Alçada - Domingo', 300.00),
            ('2025-11-17', 'Oferta Alçada', 'Oferta Alçada - Domingo', 250.00),
            ('2025-11-24', 'Oferta', 'Oferta da Igreja', 180.00),
            ('2025-11-15', 'Oferta', 'Oferta Especial', 120.00)
        ]
        
        print("📝 Inserindo lançamentos de teste:")
        
        for data, categoria, descricao, valor in ofertas_teste:
            cursor.execute("""
                INSERT INTO lancamentos (data, tipo, categoria, descricao, valor, conta)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (data, 'Entrada', categoria, descricao, valor, 'Caixa'))
            
            print(f"   ✅ {data} - {categoria}: R$ {valor:,.2f}")
        
        conn.commit()
        
        # Verificar resultado
        cursor.execute("""
            SELECT categoria, descricao, valor, data
            FROM lancamentos
            WHERE tipo = 'Entrada'
            AND data LIKE '2025-11%'
            ORDER BY data DESC
        """)
        
        lancamentos_novembro = cursor.fetchall()
        
        print(f"\n📊 NOVEMBRO 2025 - APÓS INSERÇÃO:")
        print("-" * 50)
        
        totais = {'dizimos': 0, 'ofertas_alcadas': 0, 'outras_ofertas': 0}
        
        for i, (categoria, descricao, valor, data) in enumerate(lancamentos_novembro, 1):
            categoria_lower = (categoria or '').lower()
            valor_float = float(valor)
            
            print(f"{i:2d}. {categoria} - R$ {valor_float:,.2f} ({data})")
            
            if 'dízimo' in categoria_lower or 'dizimo' in categoria_lower:
                totais['dizimos'] += valor_float
            elif 'oferta' in categoria_lower:
                if 'alçada' in categoria_lower or 'alcada' in categoria_lower:
                    totais['ofertas_alcadas'] += valor_float
                elif categoria_lower == 'oferta':
                    totais['ofertas_alcadas'] += valor_float  # Oferta regular
                else:
                    totais['outras_ofertas'] += valor_float
            else:
                totais['outras_ofertas'] += valor_float
        
        print(f"\n✅ TOTAIS ATUALIZADOS:")
        print(f"   Dízimos: R$ {totais['dizimos']:,.2f}")
        print(f"   Ofertas Alçadas: R$ {totais['ofertas_alcadas']:,.2f}")
        print(f"   Outras Ofertas: R$ {totais['outras_ofertas']:,.2f}")
        
        if totais['ofertas_alcadas'] > 0:
            print(f"\n🎉 SUCESSO! Agora novembro tem R$ {totais['ofertas_alcadas']:,.2f} em ofertas alçadas!")
            print("📝 Gere o PDF novamente - deve mostrar o valor correto.")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Erro: {str(e)}")

if __name__ == "__main__":
    adicionar_ofertas_novembro()