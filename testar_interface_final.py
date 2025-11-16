#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Teste final da interface web depois das correções
"""

import requests
import time

def testar_interface_final():
    """Teste final da interface web"""
    
    print("🌐 TESTE FINAL DA INTERFACE WEB")
    print("=" * 50)
    
    base_url = "http://127.0.0.1:5000"
    session = requests.Session()
    
    try:
        # 1. Login
        print("1. Fazendo login...")
        login_url = f"{base_url}/login"
        
        login_data = {
            'email': 'admin@obpc.com',
            'senha': '123456'
        }
        
        login_response = session.post(login_url, data=login_data, allow_redirects=True)
        print(f"   Login: {login_response.status_code}")
        
        # 2. Acessar inventário
        print("2. Acessando inventário...")
        inventario_url = f"{base_url}/secretaria/inventario"
        
        response = session.get(inventario_url)
        print(f"   Inventário: {response.status_code}")
        
        if response.status_code == 200:
            html = response.text
            
            # Verificações específicas
            checks = [
                ("Template renderizado", "<html" in html and "</html>" in html),
                ("Título inventário", "inventário" in html.lower()),
                ("Tabela presente", "<table" in html),
                ("Item TESTE001", "TESTE001" in html),
                ("Item código 05", "05" in html),
                ("Lista vazia (erro)", "Nenhum item no inventário" in html),
                ("Valor total", "Valor Total" in html),
                ("Contador de itens", "Total de Itens" in html or "Itens Ativos" in html),
                ("JavaScript funcionando", "<script" in html),
                ("Bootstrap carregado", "bootstrap" in html.lower())
            ]
            
            print("\n   📊 Análise da interface:")
            tem_problema = False
            for check_name, result in checks:
                status = "✅" if result else "❌"
                print(f"      {status} {check_name}")
                
                if check_name == "Lista vazia (erro)" and result:
                    tem_problema = True
                    print("         🚨 PROBLEMA: Ainda mostra lista vazia!")
            
            # Salvar HTML final
            with open("debug_interface_final.html", "w", encoding="utf-8") as f:
                f.write(html)
            print(f"\n   💾 HTML final salvo em: debug_interface_final.html")
            
            # Verificar contadores específicos
            if "Total de Itens" in html:
                # Extrair números dos contadores
                import re
                
                # Procurar por padrões de números nos cards
                numeros_encontrados = re.findall(r'<h5>(\d+)</h5>', html)
                if numeros_encontrados:
                    print(f"\n   📊 Contadores encontrados: {numeros_encontrados}")
                    
                    if any(int(num) > 0 for num in numeros_encontrados):
                        print(f"   ✅ CONTADORES MOSTRAM DADOS!")
                    else:
                        print(f"   ❌ TODOS OS CONTADORES ESTÃO EM ZERO!")
                else:
                    print(f"   ❓ Contadores não encontrados no padrão esperado")
            
            # Resultado final
            if tem_problema:
                print(f"\n   🔍 PROBLEMA IDENTIFICADO: Interface ainda mostra lista vazia")
                print(f"   💡 POSSÍVEIS CAUSAS:")
                print(f"      - Cache do navegador")
                print(f"      - JavaScript não está executando")
                print(f"      - Erro na passagem de dados do backend")
                print(f"      - Template ainda tem bugs")
                return False
            else:
                print(f"\n   🎉 INTERFACE PARECE ESTAR FUNCIONANDO!")
                return True
                
        else:
            print(f"   ❌ Erro ao acessar inventário: {response.status_code}")
            return False
        
    except Exception as e:
        print(f"❌ Erro: {str(e)}")
        return False

if __name__ == "__main__":
    print("⏳ Aguardando servidor inicializar...")
    time.sleep(3)
    
    resultado = testar_interface_final()
    
    if resultado:
        print("\n" + "=" * 50)
        print("🎉 TESTE PASSOU - INTERFACE FUNCIONANDO!")
        print("=" * 50)
    else:
        print("\n" + "=" * 50)
        print("❌ PROBLEMA AINDA EXISTE")
        print("📁 Verifique: debug_interface_final.html")
        print("=" * 50)