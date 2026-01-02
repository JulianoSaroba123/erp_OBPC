"""
Script para atualizar atividades existentes no Render.

COMO USAR NO RENDER:
1. Acesse o Dashboard do Render
2. Vá em Shell (console)
3. Execute: python atualizar_atividades_render.py

Este script vai:
- Buscar todas as atividades existentes
- Marcar exibir_no_painel = True
- Atualizar datas antigas para datas futuras
"""

from app import create_app, db
from app.departamentos.departamentos_model import CronogramaDepartamento
from datetime import date, timedelta

app = create_app()

with app.app_context():
    print("=" * 70)
    print("ATUALIZANDO ATIVIDADES PARA O PAINEL - RENDER")
    print("=" * 70)
    
    # Buscar todas as atividades
    todas_atividades = CronogramaDepartamento.query.all()
    print(f"\nTotal de atividades encontradas: {len(todas_atividades)}")
    
    if not todas_atividades:
        print("\nNenhuma atividade encontrada no banco.")
        exit(0)
    
    hoje = date.today()
    atualizadas = 0
    datas_atualizadas = 0
    
    for atividade in todas_atividades:
        modificado = False
        
        # 1. Garantir que exibir_no_painel seja True
        if not atividade.exibir_no_painel:
            atividade.exibir_no_painel = True
            modificado = True
            atualizadas += 1
        
        # 2. Se a data já passou, atualizar para uma data futura
        if atividade.data_evento < hoje:
            dias_passados = (hoje - atividade.data_evento).days
            # Adicionar os dias que passaram + 7 dias no futuro
            atividade.data_evento = hoje + timedelta(days=7)
            modificado = True
            datas_atualizadas += 1
            print(f"  - Data atualizada: {atividade.titulo} -> {atividade.data_evento.strftime('%d/%m/%Y')}")
        
        # 3. Garantir que está ativo
        if not atividade.ativo:
            atividade.ativo = True
            modificado = True
        
        if modificado:
            print(f"  - Atualizada: {atividade.titulo}")
    
    # Salvar alterações
    db.session.commit()
    
    print("\n" + "=" * 70)
    print("RESULTADO:")
    print("=" * 70)
    print(f"Total de atividades processadas: {len(todas_atividades)}")
    print(f"Atividades marcadas para exibir no painel: {atualizadas}")
    print(f"Datas atualizadas para futuro: {datas_atualizadas}")
    
    # Mostrar atividades que aparecerão no painel
    atividades_painel = CronogramaDepartamento.query.filter(
        CronogramaDepartamento.ativo == True,
        CronogramaDepartamento.exibir_no_painel == True,
        CronogramaDepartamento.data_evento >= hoje
    ).order_by(CronogramaDepartamento.data_evento.asc()).all()
    
    print(f"\nAtividades que aparecerao no painel: {len(atividades_painel)}")
    for i, ativ in enumerate(atividades_painel, 1):
        print(f"{i}. {ativ.titulo} - {ativ.data_evento.strftime('%d/%m/%Y')} as {ativ.horario}")
    
    print("\n" + "=" * 70)
    print("CONCLUIDO! Atualize a pagina do painel para ver as mudancas.")
    print("=" * 70)
