from app import create_app, db
from app.departamentos.departamentos_model import CronogramaDepartamento, Departamento
from datetime import date, timedelta

app = create_app()
ctx = app.app_context()
ctx.push()

print("=" * 70)
print("CRIANDO ATIVIDADES FUTURAS PARA O PAINEL")
print("=" * 70)

# Buscar departamentos
departamentos = Departamento.query.all()
print(f"\nDepartamentos encontrados: {len(departamentos)}")
for dep in departamentos:
    print(f" - {dep.nome}")

if not departamentos:
    print("\nNenhum departamento encontrado. Criando departamento exemplo...")
    dep = Departamento(nome="Departamento Infantil", descricao="Trabalho com crianças")
    db.session.add(dep)
    db.session.commit()
    departamentos = [dep]

# Remover atividades antigas (passadas)
atividades_antigas = CronogramaDepartamento.query.filter(
    CronogramaDepartamento.data_evento < date.today()
).all()

if atividades_antigas:
    print(f"\nRemovendo {len(atividades_antigas)} atividades passadas...")
    for ativ in atividades_antigas:
        db.session.delete(ativ)
    db.session.commit()

# Criar atividades futuras
hoje = date.today()
atividades_criadas = []

atividades_exemplo = [
    {
        'titulo': 'Culto Infantil Especial',
        'descricao': 'Culto especial para as crianças com atividades lúdicas',
        'dias_futuros': 7,
        'horario': '10h00',
        'local': 'Salão da Igreja',
        'responsavel': 'Equipe Menibrac'
    },
    {
        'titulo': 'Ensaio do Coral Infantil',
        'descricao': 'Ensaio das músicas para apresentação',
        'dias_futuros': 3,
        'horario': '15h00',
        'local': 'Sala de Música',
        'responsavel': 'Professora Maria'
    },
    {
        'titulo': 'Escola Bíblica Dominical',
        'descricao': 'Aula bíblica para crianças de 6 a 12 anos',
        'dias_futuros': 5,
        'horario': '09h00',
        'local': 'Sala 1',
        'responsavel': 'Professor João'
    },
    {
        'titulo': 'Recreação e Evangelismo',
        'descricao': 'Atividades recreativas com mensagem evangélica',
        'dias_futuros': 10,
        'horario': '14h00',
        'local': 'Quadra da Igreja',
        'responsavel': 'Equipe de Evangelismo'
    },
    {
        'titulo': 'Reunião de Planejamento',
        'descricao': 'Planejamento das atividades do mês',
        'dias_futuros': 14,
        'horario': '19h30',
        'local': 'Sala de Reuniões',
        'responsavel': 'Coordenação'
    }
]

for i, exemplo in enumerate(atividades_exemplo, 1):
    # Alternar entre os departamentos
    departamento = departamentos[i % len(departamentos)]
    
    data_evento = hoje + timedelta(days=exemplo['dias_futuros'])
    
    atividade = CronogramaDepartamento(
        departamento_id=departamento.id,
        data_evento=data_evento,
        titulo=exemplo['titulo'],
        descricao=exemplo['descricao'],
        horario=exemplo['horario'],
        local=exemplo['local'],
        responsavel=exemplo['responsavel'],
        exibir_no_painel=True,  # IMPORTANTE: marcar para exibir no painel
        ativo=True
    )
    
    db.session.add(atividade)
    atividades_criadas.append(atividade)
    
    print(f"\n[OK] Criada: {exemplo['titulo']}")
    print(f"   Data: {data_evento.strftime('%d/%m/%Y')}")
    print(f"   Horário: {exemplo['horario']}")
    print(f"   Departamento: {departamento.nome}")

# Salvar no banco
db.session.commit()

print("\n" + "=" * 70)
print(f"SUCESSO! {len(atividades_criadas)} atividades futuras criadas!")
print("=" * 70)

# Verificar o que vai aparecer no painel
atividades_painel = CronogramaDepartamento.query.filter(
    CronogramaDepartamento.ativo == True,
    CronogramaDepartamento.exibir_no_painel == True,
    CronogramaDepartamento.data_evento >= hoje
).order_by(CronogramaDepartamento.data_evento.asc()).all()

print(f"\nTotal de atividades que aparecerao no painel: {len(atividades_painel)}")
print("\nAtividades no painel (ordenadas por data):")
for i, ativ in enumerate(atividades_painel, 1):
    print(f"{i}. {ativ.titulo} - {ativ.data_evento.strftime('%d/%m/%Y')} às {ativ.horario}")

ctx.pop()
