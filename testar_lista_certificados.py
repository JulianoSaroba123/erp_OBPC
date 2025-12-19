#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import requests

def testar_rota_lista():
    """Testa a rota de listagem de certificados"""
    try:
        response = requests.get("http://127.0.0.1:5000/midia/certificados")
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            print("✅ Rota funcionando!")
            
            # Verificar se há erro na página
            if "erro" in response.text.lower() or "error" in response.text.lower():
                print("⚠️ Pode haver erro na página")
            
            # Verificar se há indicação de certificados
            if "Ana Sofia" in response.text or "Carlos Roberto" in response.text:
                print("✅ Certificados encontrados na página!")
            elif "Nenhum certificado" in response.text:
                print("⚠️ Página indica que não há certificados")
            else:
                print("❓ Não foi possível determinar se há certificados")
                
        else:
            print(f"❌ Erro na rota: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Erro ao testar rota: {e}")

if __name__ == "__main__":
    print("=== TESTANDO ROTA DE LISTAGEM ===")
    testar_rota_lista()