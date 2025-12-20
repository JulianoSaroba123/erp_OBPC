# Sistema de Líder de Departamento

## O que foi implementado?

Agora o sistema permite criar usuários com nível de acesso **"Líder de Departamento"** que terão acesso apenas ao departamento específico que lideram.

## Alterações realizadas

### 1. Modelo de Usuário (`app/usuario/usuario_model.py`)
- ✅ Adicionado nível de acesso `LIDER_DEPARTAMENTO`
- ✅ Adicionado campo `departamento_id` (referência ao departamento que lidera)
- ✅ Adicionado método `eh_lider_departamento()` para verificação
- ✅ Líder de departamento tem acesso ao módulo de departamentos

### 2. Listagem de Departamentos (`app/departamentos/departamentos_routes.py`)
- ✅ Modificada para filtrar apenas o departamento do líder
- ✅ Admin/Master continuam vendo todos os departamentos

### 3. Scripts auxiliares criados
- ✅ `adicionar_coluna_departamento_usuario.py` - Atualiza o banco de dados
- ✅ `criar_usuario_lider_jubrac.py` - Exemplo de criação de líder

## Como usar?

### Passo 1: Atualizar o banco de dados

Execute o script para adicionar a nova coluna:

```powershell
python adicionar_coluna_departamento_usuario.py
```

### Passo 2: Criar um líder de departamento

**Opção A - Usar o script de exemplo:**

```powershell
python criar_usuario_lider_jubrac.py
```

**Opção B - Criar manualmente:**

Você pode criar um líder para qualquer departamento. Exemplo para Jubrac:

```python
from app import create_app
from app.extensoes import db
from app.usuario.usuario_model import Usuario
from app.departamentos.departamentos_model import Departamento

app = create_app()
with app.app_context():
    # Buscar o departamento (exemplo: Jubrac)
    jubrac = Departamento.query.filter_by(nome='Jubrac').first()
    
    # Criar o usuário líder
    lider = Usuario(
        nome='Nome do Líder',
        email='lider@obpc.com',
        nivel_acesso='lider_departamento',
        departamento_id=jubrac.id,
        ativo=True
    )
    lider.set_senha('senha_segura')
    
    db.session.add(lider)
    db.session.commit()
```

### Passo 3: Login e acesso

Quando o líder fizer login:

1. ✅ Será redirecionado automaticamente para a página de Departamentos
2. ✅ Verá **apenas o departamento que lidera** (não os outros)
3. ✅ Poderá visualizar e editar as informações do seu departamento
4. ✅ Não terá acesso a outros módulos administrativos

## Regras de acesso

| Nível de Acesso | Departamentos Visíveis |
|-----------------|------------------------|
| Master | Todos |
| Administrador | Todos |
| Líder de Departamento | Apenas o seu |
| Outros níveis | Sem acesso |

## Exemplo prático

**Cenário:** João é líder do Jubrac

1. Criar departamento Jubrac (se ainda não existir)
2. Executar `python adicionar_coluna_departamento_usuario.py`
3. Criar usuário:
   - Nome: João Silva
   - Email: joao.jubrac@obpc.com
   - Nível: `lider_departamento`
   - Departamento: Jubrac (ID do departamento)
   - Senha: definir senha segura

4. João faz login → Vai direto para Departamentos → Vê apenas o Jubrac

## Validações importantes

- ✅ Usuário com `nivel_acesso='lider_departamento'` DEVE ter `departamento_id` preenchido
- ✅ O sistema valida com `eh_lider_departamento()` antes de filtrar
- ✅ Se não tiver departamento associado, funciona como usuário sem acesso especial

## Próximos passos sugeridos

1. Adicionar no formulário de usuários a opção de selecionar departamento
2. Criar validação para não permitir múltiplos líderes no mesmo departamento (opcional)
3. Adicionar relatório de departamentos por líder

## Observações

- Esta implementação mantém compatibilidade total com o sistema existente
- Administradores e Master continuam com acesso total
- A coluna `departamento_id` aceita NULL para usuários que não são líderes
- O sistema está pronto para deploy no Render após os testes locais
