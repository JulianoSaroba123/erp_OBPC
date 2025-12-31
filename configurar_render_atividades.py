"""
Script para configurar usuário admin no Render com departamento
Execute este script no console do Render ou via SSH
"""

from app.extensoes import db
from app import create_app

app = create_app()

with app.app_context():
    from app.usuario.usuario_model import Usuario
    from app.departamentos.departamentos_model import Departamento
    
    print("=" * 70)
    print("CONFIGURANDO ADMIN PARA VER ATIVIDADES NO RENDER")
    print("=" * 70)
    
    # 1. Buscar usuário admin
    admin = Usuario.query.filter_by(email='admin@obpc.com').first()
    
    if not admin:
        print("\n❌ Usuário admin não encontrado!")
        print("   Crie o usuário primeiro")
        exit(1)
    
    print(f"\n✓ Usuário encontrado: {admin.nome}")
    print(f"  Email: {admin.email}")
    print(f"  Departamento atual: {admin.departamento_id}")
    
    # 2. Verificar se há departamentos
    departamentos = Departamento.query.all()
    
    if not departamentos:
        print("\n⚠️ Nenhum departamento cadastrado!")
        print("   Criando departamento padrão...")
        
        # Criar departamento padrão
        dept = Departamento(
            nome="Administração",
            lider="Administrador",
            status="Ativo",
            descricao="Departamento administrativo da igreja"
        )
        db.session.add(dept)
        db.session.commit()
        
        print(f"✓ Departamento '{dept.nome}' criado (ID: {dept.id})")
        departamento_id = dept.id
    else:
        # Usar primeiro departamento
        dept = departamentos[0]
        departamento_id = dept.id
        print(f"\n✓ Departamento encontrado: {dept.nome} (ID: {dept.id})")
    
    # 3. Vincular admin ao departamento
    if admin.departamento_id != departamento_id:
        admin.departamento_id = departamento_id
        db.session.commit()
        print(f"\n✅ Admin vinculado ao departamento ID {departamento_id}")
    else:
        print(f"\n✓ Admin já está vinculado ao departamento ID {departamento_id}")
    
    # 4. Verificar atividades
    from app.departamentos.departamentos_model import CronogramaDepartamento
    atividades = CronogramaDepartamento.query.filter_by(departamento_id=departamento_id).all()
    
    print(f"\n📊 Atividades cadastradas neste departamento: {len(atividades)}")
    
    if atividades:
        for a in atividades:
            print(f"  - {a.titulo} ({a.data_evento}) | Painel: {a.exibir_no_painel}")
    else:
        print("\n⚠️ Nenhuma atividade cadastrada ainda!")
        print("   Cadastre atividades em: Departamentos > Editar departamento")
    
    print("\n" + "=" * 70)
    print("CONFIGURAÇÃO CONCLUÍDA!")
    print("=" * 70)
    print("\n📝 Próximos passos:")
    print("   1. Faça logout no Render")
    print("   2. Faça login novamente")
    print("   3. Vá em Departamentos e cadastre atividades")
    print("   4. Marque o checkbox 'Exibir no Painel'")
    print("   5. As atividades devem aparecer no painel principal")
