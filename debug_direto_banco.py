import sqlite3
from datetime import datetime

# Conectar diretamente ao banco
conn = sqlite3.connect('instance/database.db')
cursor = conn.cursor()

print("=== DEBUG DIRETO NO BANCO - OUTUBRO 2025 ===")

# Buscar todas as entradas de outubro 2025
query = """
SELECT data, categoria, valor, tipo, conta, descricao 
FROM lancamento 
WHERE tipo = 'Entrada' 
AND date(data) >= '2025-10-01' 
AND date(data) < '2025-11-01'
ORDER BY data
"""

cursor.execute(query)
resultados = cursor.fetchall()

print(f"Total de entradas encontradas: {len(resultados)}")

# Processar cada entrada
total_dizimos = 0
total_ofertas_alcadas = 0
total_outras_ofertas = 0

for row in resultados:
    data, categoria, valor, tipo, conta, descricao = row
    
    print(f"\nData: {data}")
    print(f"Categoria: '{categoria}'")
    print(f"Valor: R$ {valor:.2f}")
    print(f"Tipo: {tipo}")
    print(f"Conta: {conta}")
    print(f"Descrição: {descricao}")
    
    # Aplicar a mesma lógica do código
    categoria_lower = categoria.lower() if categoria else ''
    
    if 'dízimo' in categoria_lower or 'dizimo' in categoria_lower:
        total_dizimos += valor
        print(f"→ CLASSIFICADO COMO: DÍZIMOS (R$ {valor:.2f})")
    elif 'oferta' in categoria_lower:
        if 'omn' in categoria_lower or 'especial' in categoria_lower:
            total_outras_ofertas += valor
            print(f"→ CLASSIFICADO COMO: OUTRAS OFERTAS (especial) (R$ {valor:.2f})")
        else:
            total_ofertas_alcadas += valor
            print(f"→ CLASSIFICADO COMO: OFERTAS ALÇADAS (regular) (R$ {valor:.2f})")
    else:
        total_outras_ofertas += valor
        print(f"→ CLASSIFICADO COMO: OUTRAS OFERTAS (não é dízimo nem oferta) (R$ {valor:.2f})")
    
    print("-" * 60)

print(f"\n=== TOTAIS CALCULADOS ===")
print(f"Dízimos: R$ {total_dizimos:.2f}")
print(f"Ofertas Alçadas: R$ {total_ofertas_alcadas:.2f}")
print(f"Outras Ofertas: R$ {total_outras_ofertas:.2f}")

# Verificar especificamente se existe o valor 236.52
print(f"\n=== VERIFICANDO VALOR R$ 236,52 ===")
for row in resultados:
    data, categoria, valor, tipo, conta, descricao = row
    if abs(valor - 236.52) < 0.01:
        print(f"ENCONTRADO! Data: {data}, Categoria: '{categoria}', Valor: R$ {valor:.2f}")

conn.close()