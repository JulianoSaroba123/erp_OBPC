"""
Script para verificar se o blueprint de participação está funcionando
"""
from app import create_app

app = create_app()

with app.app_context():
    print("🔍 === VERIFICANDO BLUEPRINT DE PARTICIPAÇÃO ===")
    
    # Listar todas as rotas registradas
    print("\n📋 Rotas registradas no sistema:")
    for rule in app.url_map.iter_rules():
        if 'participacao' in rule.rule:
            print(f"   ✅ {rule.methods} {rule.rule} → {rule.endpoint}")
    
    # Verificar se as rotas específicas existem
    rotas_esperadas = [
        '/secretaria/participacao',
        '/secretaria/participacao/nova',
        '/secretaria/participacao/salvar',
        '/secretaria/participacao/pdf'
    ]
    
    print("\n🎯 Verificando rotas específicas:")
    for rota in rotas_esperadas:
        try:
            with app.test_client() as client:
                # Fazer uma requisição de teste (pode dar erro de login, mas rota existe)
                response = client.get(rota)
                if response.status_code in [200, 302, 401, 403]:  # Códigos que indicam que a rota existe
                    print(f"   ✅ {rota} - ROTA EXISTE (status: {response.status_code})")
                else:
                    print(f"   ❌ {rota} - ERRO (status: {response.status_code})")
        except Exception as e:
            print(f"   ❌ {rota} - ERRO: {e}")
    
    # Verificar blueprints registrados
    print("\n📦 Blueprints registrados:")
    for blueprint_name, blueprint in app.blueprints.items():
        if blueprint_name == 'participacao':
            print(f"   ✅ Blueprint 'participacao' encontrado!")
            print(f"      Prefixo URL: {getattr(blueprint, 'url_prefix', 'Nenhum')}")
        elif 'secretaria' in blueprint_name or blueprint_name in ['atas', 'inventario', 'oficios']:
            print(f"   📋 Blueprint '{blueprint_name}' registrado")
    
    print("\n🎯 === RESULTADO ===")
    if 'participacao' in app.blueprints:
        print("✅ Blueprint de participação está registrado corretamente!")
        print("💡 Se não aparece no menu, reinicie o servidor Flask")
    else:
        print("❌ Blueprint de participação NÃO está registrado!")
        print("💡 Verifique o arquivo app/__init__.py")