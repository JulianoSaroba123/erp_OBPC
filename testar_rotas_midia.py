"""
Teste de Rotas do Módulo Mídia - Sistema OBPC
Verifica se as rotas estão sendo registradas corretamente
"""

from app import create_app

def testar_rotas_midia():
    """Testa se as rotas do módulo mídia estão registradas"""
    print("🔍 TESTE DE ROTAS - MÓDULO MÍDIA")
    print("="*50)
    
    try:
        app = create_app()
        
        # Listar todas as rotas registradas
        print("📋 ROTAS REGISTRADAS NO SISTEMA:")
        print("-" * 30)
        
        rotas_midia = []
        outras_rotas = []
        
        with app.app_context():
            for rule in app.url_map.iter_rules():
                rota = str(rule)
                if '/midia/' in rota:
                    rotas_midia.append(rota)
                else:
                    outras_rotas.append(rota)
        
        # Mostrar rotas do módulo mídia
        if rotas_midia:
            print("✅ ROTAS DO MÓDULO MÍDIA ENCONTRADAS:")
            for rota in sorted(rotas_midia):
                print(f"   🎯 {rota}")
        else:
            print("❌ NENHUMA ROTA DO MÓDULO MÍDIA ENCONTRADA!")
        
        print(f"\n📊 RESUMO:")
        print(f"   🎯 Rotas Mídia: {len(rotas_midia)}")
        print(f"   🔧 Outras Rotas: {len(outras_rotas)}")
        
        # Mostrar algumas outras rotas para comparação
        print(f"\n🔧 ALGUMAS OUTRAS ROTAS (para comparação):")
        for rota in sorted(outras_rotas)[:5]:
            print(f"   ⚙️ {rota}")
        
        if rotas_midia:
            print(f"\n✅ TESTE: As rotas estão registradas corretamente!")
        else:
            print(f"\n❌ PROBLEMA: Rotas do módulo mídia não foram registradas!")
            print(f"💡 POSSÍVEIS CAUSAS:")
            print(f"   - Erro na importação dos blueprints")
            print(f"   - Erro de sintaxe nos arquivos de rotas")
            print(f"   - Blueprints não registrados no app principal")
        
    except Exception as e:
        print(f"❌ ERRO ao testar rotas: {str(e)}")
        import traceback
        print(f"📋 TRACEBACK:")
        traceback.print_exc()

if __name__ == '__main__':
    testar_rotas_midia()