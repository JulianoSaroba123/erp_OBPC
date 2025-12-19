#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Análise precisa do HTML gerado pelo inventário
"""

import requests
import re

def analisar_html_inventario():
    """Analisa precisamente o HTML do inventário"""
    
    print("🔍 ANÁLISE PRECISA DO HTML DO INVENTÁRIO")
    print("=" * 60)
    
    base_url = "http://127.0.0.1:5000"
    session = requests.Session()
    
    try:
        # Login
        login_data = {'email': 'admin@obpc.com', 'senha': '123456'}
        session.post(f"{base_url}/login", data=login_data, allow_redirects=True)
        
        # Acessar inventário
        response = session.get(f"{base_url}/secretaria/inventario")
        html = response.text
        
        print("1. VERIFICAÇÃO DE TEMPLATE COMPILATION:")
        
        # Verificar se o template foi compilado corretamente
        template_errors = re.findall(r'{%.*?%}', html)
        if template_errors:
            print(f"   ❌ TEMPLATE NÃO COMPILADO! Erros encontrados:")
            for error in template_errors[:5]:  # Mostrar apenas os primeiros 5
                print(f"      - {error}")
        else:
            print("   ✅ Template compilado corretamente")
        
        print("\n2. VERIFICAÇÃO DOS CONTADORES:")
        
        # Procurar pelos contadores nos cards
        contador_total = re.search(r'Total de Itens.*?<h5[^>]*>(\d+)</h5>', html, re.DOTALL | re.IGNORECASE)
        if contador_total:
            total = contador_total.group(1)
            print(f"   📊 Total de Itens: {total}")
        else:
            print("   ❌ Contador 'Total de Itens' não encontrado")
        
        contador_ativos = re.search(r'Itens Ativos.*?<h5[^>]*>(\d+)</h5>', html, re.DOTALL | re.IGNORECASE)
        if contador_ativos:
            ativos = contador_ativos.group(1)
            print(f"   ✅ Itens Ativos: {ativos}")
        else:
            print("   ❌ Contador 'Itens Ativos' não encontrado")
        
        contador_resultados = re.search(r'Resultados.*?<h5[^>]*>(\d+)</h5>', html, re.DOTALL | re.IGNORECASE)
        if contador_resultados:
            resultados = contador_resultados.group(1)
            print(f"   🔍 Resultados: {resultados}")
        else:
            print("   ❌ Contador 'Resultados' não encontrado")
        
        print("\n3. VERIFICAÇÃO DA TABELA DE ITENS:")
        
        # Verificar se há tabela de itens
        tabela_itens = re.search(r'<table[^>]*class="table[^"]*"[^>]*>.*?</table>', html, re.DOTALL)
        if tabela_itens:
            print("   ✅ Tabela HTML encontrada")
            
            # Verificar linhas de dados na tabela
            linhas_dados = re.findall(r'<tr[^>]*>.*?</tr>', tabela_itens.group(0), re.DOTALL)
            linhas_dados = [l for l in linhas_dados if '<th' not in l]  # Remover cabeçalho
            
            print(f"   📋 Linhas de dados na tabela: {len(linhas_dados)}")
            
            if len(linhas_dados) > 0:
                print("   ✅ DADOS ENCONTRADOS NA TABELA!")
                
                # Extrair códigos dos itens
                codigos = re.findall(r'<span[^>]*class="badge[^"]*"[^>]*>([^<]+)</span>', tabela_itens.group(0))
                if codigos:
                    print(f"   📋 Códigos encontrados: {codigos}")
                else:
                    print("   ⚠️ Nenhum código extraído das linhas")
            else:
                print("   ❌ Nenhuma linha de dados na tabela")
        else:
            print("   ❌ Tabela HTML não encontrada")
        
        print("\n4. VERIFICAÇÃO DA MENSAGEM DE LISTA VAZIA:")
        
        # Verificar mensagem de lista vazia
        if "Nenhum item no inventário" in html:
            print("   ❌ MENSAGEM 'NENHUM ITEM' ENCONTRADA")
            
            # Verificar o contexto da mensagem
            contexto = re.search(r'.{100}Nenhum item no inventário.{100}', html, re.DOTALL)
            if contexto:
                print("   📄 Contexto da mensagem:")
                print(f"      {contexto.group(0).strip()}")
        else:
            print("   ✅ Mensagem 'Nenhum item' NÃO encontrada")
        
        print("\n5. VERIFICAÇÃO DE DADOS ESCONDIDOS:")
        
        # Procurar por qualquer referência a códigos de itens
        todos_codigos = re.findall(r'[A-Z]{2,4}\d{3}', html)
        if todos_codigos:
            print(f"   📋 Códigos encontrados em qualquer lugar do HTML: {set(todos_codigos)}")
        else:
            print("   ❌ Nenhum código de item encontrado no HTML")
        
        # Procurar por texto "05" especificamente
        ocorrencias_05 = html.count("05")
        if ocorrencias_05 > 0:
            print(f"   🔍 Texto '05' aparece {ocorrencias_05} vezes no HTML")
            
            # Encontrar contextos onde aparece "05"
            contextos = re.findall(r'.{20}05.{20}', html)
            print("   📄 Contextos onde aparece '05':")
            for i, ctx in enumerate(contextos[:3], 1):  # Mostrar apenas os primeiros 3
                print(f"      {i}. ...{ctx.strip()}...")
        else:
            print("   ❌ Texto '05' não encontrado no HTML")
        
        # Salvar análise
        with open("analise_html_detalhada.html", "w", encoding="utf-8") as f:
            f.write(html)
        
        print(f"\n6. HTML COMPLETO SALVO EM: analise_html_detalhada.html")
        print(f"   📏 Tamanho total: {len(html)} caracteres")
        
        return html
        
    except Exception as e:
        print(f"❌ Erro na análise: {str(e)}")
        return None

if __name__ == "__main__":
    resultado = analisar_html_inventario()
    
    print("\n" + "=" * 60)
    if resultado:
        print("✅ ANÁLISE CONCLUÍDA")
        print("📁 Verifique: analise_html_detalhada.html")
    else:
        print("❌ ANÁLISE FALHOU")
    print("=" * 60)