"""
TESTE DIRETO DA LÓGICA DO PAINEL
Execute no Render para ver exatamente o que está acontecendo
"""
from app.extensoes import db
from app import create_app
from datetime import date

app = create_app()

with app.app_context():
    from app.usuario.usuario_model import Usuario
    from app.departamentos.departamentos_model import CronogramaDepartamento
    
    print("=" * 80)
    print("TESTANDO LÓGICA DO PAINEL - EXATAMENTE COMO O CÓDIGO")
    print("=" * 80)
    
    # Buscar usuário admin
    admin = Usuario.query.filter_by(email='admin@obpc.com').first()
    
    if not admin:
        print("\n❌ Usuário admin não encontrado!")
        exit(1)
    
    print(f"\n✓ Usuário: {admin.nome}")
    print(f"  Email: {admin.email}")
    print(f"  Departamento ID: {admin.departamento_id}")
    print(f"  Nível: {admin.nivel_acesso}")
    
    # Testar método eh_lider_departamento
    print(f"\n🔍 Testando eh_lider_departamento():")
    resultado = admin.eh_lider_departamento()
    print(f"  Resultado: {resultado}")
    
    if admin.nivel_acesso in ['master', 'administrador', 'Admin']:
        print(f"  ✓ Nível é master/admin: {admin.nivel_acesso}")
        if admin.departamento_id is not None:
            print(f"  ✓ Tem departamento_id: {admin.departamento_id}")
            print(f"  ✅ DEVERIA retornar True!")
        else:
            print(f"  ❌ NÃO tem departamento_id!")
            print(f"  ❌ Por isso retorna False!")
    
    # Simular código do painel
    print(f"\n🔍 Simulando código do painel:")
    print(f"  if current_user.eh_lider_departamento():")
    
    atividades_departamento = []
    
    if resultado:  # Se eh_lider_departamento retornar True
        print(f"    ✓ Entrou no IF!")
        
        try:
            hoje = date.today()
            print(f"    Data hoje: {hoje}")
            
            # Query exata do código
            atividades_departamento = CronogramaDepartamento.query.filter(
                CronogramaDepartamento.departamento_id == admin.departamento_id,
                CronogramaDepartamento.ativo == True,
                CronogramaDepartamento.exibir_no_painel == True,
                CronogramaDepartamento.data_evento >= hoje
            ).order_by(CronogramaDepartamento.data_evento.asc()).limit(10).all()
            
            print(f"\n    📊 Query executada com sucesso!")
            print(f"    Critérios:")
            print(f"      - departamento_id == {admin.departamento_id}")
            print(f"      - ativo == True")
            print(f"      - exibir_no_painel == True")
            print(f"      - data_evento >= {hoje}")
            
            print(f"\n    🎯 Resultado: {len(atividades_departamento)} atividades")
            
            if atividades_departamento:
                print(f"\n    ✅ ATIVIDADES ENCONTRADAS:")
                for a in atividades_departamento:
                    print(f"\n      - {a.titulo}")
                    print(f"        Data: {a.data_evento}")
                    print(f"        Horário: {a.horario}")
                    print(f"        Local: {a.local}")
                    print(f"        Responsável: {a.responsavel}")
                    print(f"        data_formatada: {a.data_formatada}")
            else:
                print(f"\n    ❌ NENHUMA ATIVIDADE ENCONTRADA!")
                
                # Debug: verificar cada critério
                print(f"\n    🔍 Debug dos critérios:")
                
                todas = CronogramaDepartamento.query.filter(
                    CronogramaDepartamento.departamento_id == admin.departamento_id
                ).all()
                print(f"      Total do departamento: {len(todas)}")
                
                for a in todas:
                    print(f"\n      Atividade: {a.titulo}")
                    print(f"        departamento_id: {a.departamento_id} == {admin.departamento_id}? {a.departamento_id == admin.departamento_id}")
                    print(f"        ativo: {a.ativo}")
                    print(f"        exibir_no_painel: {a.exibir_no_painel}")
                    print(f"        data_evento: {a.data_evento} >= {hoje}? {a.data_evento >= hoje}")
                    
                    if not a.ativo:
                        print(f"        ❌ PROBLEMA: não está ativa!")
                    if not a.exibir_no_painel:
                        print(f"        ❌ PROBLEMA: exibir_no_painel é False!")
                    if a.data_evento < hoje:
                        print(f"        ❌ PROBLEMA: data é passada!")
                    
        except Exception as e:
            print(f"    ❌ ERRO: {e}")
            import traceback
            traceback.print_exc()
    else:
        print(f"    ❌ NÃO entrou no IF!")
        print(f"    O método eh_lider_departamento() retornou False")
        print(f"    Por isso as atividades não são buscadas!")
    
    print(f"\n" + "=" * 80)
    print(f"VARIÁVEL atividades_departamento = {len(atividades_departamento)} itens")
    print(f"=" * 80)
    
    if len(atividades_departamento) == 0:
        print(f"\n⚠️ PROBLEMA IDENTIFICADO:")
        print(f"   A variável está vazia, então o template vai mostrar:")
        print(f"   'Nenhuma atividade cadastrada no cronograma do departamento.'")
