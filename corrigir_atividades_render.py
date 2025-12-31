"""
SCRIPT DE CORREÇÃO PARA O RENDER
Execute este script para marcar todas as atividades para exibir no painel
"""
from app.extensoes import db
from app import create_app

app = create_app()

with app.app_context():
    from app.departamentos.departamentos_model import CronogramaDepartamento
    
    print("=" * 70)
    print("CORRIGINDO ATIVIDADES - MARCAR TODAS PARA EXIBIR NO PAINEL")
    print("=" * 70)
    
    # Buscar todas as atividades
    atividades = CronogramaDepartamento.query.all()
    
    print(f"\n📊 Total de atividades encontradas: {len(atividades)}\n")
    
    if not atividades:
        print("⚠️ Nenhuma atividade cadastrada!")
        print("   Cadastre atividades primeiro em: Departamentos > Editar")
    else:
        corrigidas = 0
        
        for a in atividades:
            print(f"Atividade: {a.titulo}")
            print(f"  Data: {a.data_evento}")
            print(f"  Exibir no Painel: {a.exibir_no_painel}")
            
            if not a.exibir_no_painel:
                print(f"  ❌ Marcando para exibir no painel...")
                a.exibir_no_painel = True
                a.ativo = True  # Garantir que está ativa também
                corrigidas += 1
            else:
                print(f"  ✓ Já está marcada para exibir")
            
            print()
        
        if corrigidas > 0:
            db.session.commit()
            print(f"✅ {corrigidas} atividade(s) corrigida(s)!")
        else:
            print("✓ Todas as atividades já estão corretas!")
    
    print("\n" + "=" * 70)
    print("CORREÇÃO CONCLUÍDA!")
    print("=" * 70)
    print("\n📝 Próximos passos:")
    print("   1. Faça logout no Render")
    print("   2. Faça login novamente")
    print("   3. As atividades devem aparecer no painel!")
