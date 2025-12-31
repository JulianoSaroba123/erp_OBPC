"""
DIAGNÓSTICO COMPLETO E CORREÇÃO PARA O RENDER
Execute: python diagnostico_completo_render.py
"""
from app.extensoes import db
from app import create_app
from datetime import date

app = create_app()

with app.app_context():
    from app.usuario.usuario_model import Usuario
    from app.departamentos.departamentos_model import Departamento, CronogramaDepartamento
    
    print("=" * 80)
    print("DIAGNÓSTICO COMPLETO - RENDER")
    print("=" * 80)
    
    # 1. VERIFICAR USUÁRIO ADMIN
    print("\n1️⃣ VERIFICANDO USUÁRIO ADMIN")
    print("-" * 80)
    
    admin = Usuario.query.filter_by(email='admin@obpc.com').first()
    if not admin:
        admin = Usuario.query.filter_by(nivel_acesso='master').first()
    
    if admin:
        print(f"✓ Usuário: {admin.nome}")
        print(f"  Email: {admin.email}")
        print(f"  ID: {admin.id}")
        print(f"  Departamento ID: {admin.departamento_id}")
        print(f"  Nível: {admin.nivel_acesso}")
        print(f"  eh_lider_departamento(): {admin.eh_lider_departamento()}")
    else:
        print("❌ ERRO: Usuário admin não encontrado!")
        exit(1)
    
    # 2. VERIFICAR DEPARTAMENTOS
    print("\n2️⃣ DEPARTAMENTOS CADASTRADOS")
    print("-" * 80)
    
    departamentos = Departamento.query.all()
    print(f"Total: {len(departamentos)}\n")
    
    for d in departamentos:
        print(f"ID {d.id}: {d.nome}")
        print(f"  Líder: {d.lider}")
        print(f"  Status: {d.status}")
    
    # 3. BUSCAR DEPARTAMENTO MENIBRAC
    print("\n3️⃣ DEPARTAMENTO MENIBRAC")
    print("-" * 80)
    
    menibrac = Departamento.query.filter_by(nome='Menibrac').first()
    if not menibrac:
        # Tentar buscar por ID 8 (da URL)
        menibrac = Departamento.query.get(8)
    
    if menibrac:
        print(f"✓ Encontrado: {menibrac.nome} (ID: {menibrac.id})")
        print(f"  Líder: {menibrac.lider}")
        departamento_id = menibrac.id
    else:
        print("❌ Departamento Menibrac não encontrado!")
        departamento_id = None
    
    # 4. VERIFICAR ATIVIDADES
    print("\n4️⃣ ATIVIDADES CADASTRADAS")
    print("-" * 80)
    
    todas_atividades = CronogramaDepartamento.query.all()
    print(f"Total de atividades: {len(todas_atividades)}\n")
    
    for a in todas_atividades:
        print(f"ID {a.id}: {a.titulo}")
        print(f"  Departamento ID: {a.departamento_id}")
        print(f"  Data: {a.data_evento}")
        print(f"  Ativo: {a.ativo}")
        print(f"  Exibir no Painel: {a.exibir_no_painel}")
        print()
    
    # 5. SIMULAR QUERY DO PAINEL
    print("5️⃣ SIMULANDO QUERY DO PAINEL")
    print("-" * 80)
    
    if admin.departamento_id:
        print(f"✓ Admin está vinculado ao departamento {admin.departamento_id}")
        
        hoje = date.today()
        print(f"  Data de hoje: {hoje}")
        
        # Query exata do painel
        atividades_painel = CronogramaDepartamento.query.filter(
            CronogramaDepartamento.departamento_id == admin.departamento_id,
            CronogramaDepartamento.ativo == True,
            CronogramaDepartamento.exibir_no_painel == True,
            CronogramaDepartamento.data_evento >= hoje
        ).order_by(CronogramaDepartamento.data_evento.asc()).all()
        
        print(f"\n  Resultado da query: {len(atividades_painel)} atividades")
        
        if atividades_painel:
            print("\n  ✅ ATIVIDADES QUE DEVERIAM APARECER:")
            for a in atividades_painel:
                print(f"    - {a.titulo} ({a.data_evento})")
        else:
            print("\n  ❌ NENHUMA ATIVIDADE ENCONTRADA!")
            print("\n  Verificando cada critério:")
            
            todas_dept = CronogramaDepartamento.query.filter_by(departamento_id=admin.departamento_id).all()
            print(f"    - Total do departamento: {len(todas_dept)}")
            
            ativas = CronogramaDepartamento.query.filter(
                CronogramaDepartamento.departamento_id == admin.departamento_id,
                CronogramaDepartamento.ativo == True
            ).all()
            print(f"    - Ativas: {len(ativas)}")
            
            painel = CronogramaDepartamento.query.filter(
                CronogramaDepartamento.departamento_id == admin.departamento_id,
                CronogramaDepartamento.exibir_no_painel == True
            ).all()
            print(f"    - Com 'exibir_no_painel': {len(painel)}")
            
            futuras = CronogramaDepartamento.query.filter(
                CronogramaDepartamento.departamento_id == admin.departamento_id,
                CronogramaDepartamento.data_evento >= hoje
            ).all()
            print(f"    - Com data futura: {len(futuras)}")
    else:
        print("❌ Admin NÃO está vinculado a nenhum departamento!")
        print("   ESTE É O PROBLEMA!")
    
    # 6. CORREÇÃO AUTOMÁTICA
    print("\n6️⃣ CORREÇÃO AUTOMÁTICA")
    print("-" * 80)
    
    correcoes = []
    
    # Correção 1: Vincular admin ao departamento Menibrac
    if admin and departamento_id and admin.departamento_id != departamento_id:
        print(f"Vinculando admin ao departamento {departamento_id}...")
        admin.departamento_id = departamento_id
        correcoes.append("Admin vinculado ao departamento")
    
    # Correção 2: Marcar todas atividades do departamento para exibir no painel
    if departamento_id:
        atividades_dept = CronogramaDepartamento.query.filter_by(departamento_id=departamento_id).all()
        for a in atividades_dept:
            if not a.exibir_no_painel:
                print(f"Marcando '{a.titulo}' para exibir no painel...")
                a.exibir_no_painel = True
                a.ativo = True
                correcoes.append(f"Atividade '{a.titulo}' corrigida")
    
    if correcoes:
        db.session.commit()
        print(f"\n✅ {len(correcoes)} correção(ões) aplicada(s):")
        for c in correcoes:
            print(f"   - {c}")
    else:
        print("✓ Nenhuma correção necessária")
    
    print("\n" + "=" * 80)
    print("DIAGNÓSTICO CONCLUÍDO!")
    print("=" * 80)
    print("\n📝 PRÓXIMOS PASSOS:")
    print("   1. Faça LOGOUT no navegador")
    print("   2. LIMPE o cache do navegador (Ctrl+Shift+Delete)")
    print("   3. Faça LOGIN novamente")
    print("   4. Acesse o PAINEL")
    print("   5. As atividades devem aparecer!")
