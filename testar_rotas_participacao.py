"""
Script para testar as rotas do módulo de Participação de Obreiros
"""
import requests
import time

def testar_rotas():
    base_url = "http://127.0.0.1:5000"
    
    print("🌐 === TESTANDO ROTAS DO MÓDULO DE PARTICIPAÇÃO ===")
    
    # Aguardar o servidor inicializar
    time.sleep(2)
    
    try:
        # 1. Testar rota principal
        print("\n📋 Testando rota principal...")
        response = requests.get(f"{base_url}/secretaria/participacao")
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            print("   ✅ Rota /secretaria/participacao funcionando!")
        else:
            print(f"   ❌ Erro na rota principal: {response.status_code}")
        
        # 2. Testar rota de novo cadastro
        print("\n➕ Testando rota de cadastro...")
        response = requests.get(f"{base_url}/secretaria/participacao/nova")
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            print("   ✅ Rota /secretaria/participacao/nova funcionando!")
        else:
            print(f"   ❌ Erro na rota de cadastro: {response.status_code}")
        
        # 3. Testar rota de PDF
        print("\n📄 Testando rota de PDF...")
        response = requests.get(f"{base_url}/secretaria/participacao/pdf")
        print(f"   Status: {response.status_code}")
        print(f"   Content-Type: {response.headers.get('Content-Type', 'N/A')}")
        if response.status_code == 200 and 'pdf' in response.headers.get('Content-Type', ''):
            print(f"   ✅ PDF gerado com sucesso! Tamanho: {len(response.content)} bytes")
        else:
            print(f"   ❌ Erro na rota de PDF: {response.status_code}")
        
        print("\n🎯 === TESTE DE ROTAS CONCLUÍDO ===")
        
    except requests.exceptions.ConnectionError:
        print("❌ Erro: Não foi possível conectar ao servidor.")
        print("   Certifique-se de que o servidor Flask está rodando.")
    except Exception as e:
        print(f"❌ Erro durante o teste: {e}")

if __name__ == "__main__":
    testar_rotas()