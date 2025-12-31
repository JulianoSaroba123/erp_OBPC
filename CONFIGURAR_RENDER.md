# Como configurar atividades no Render

## Problema
As atividades não aparecem no painel do Render porque:
1. O banco de dados do Render é separado do banco local
2. O usuário admin pode não estar vinculado a um departamento
3. Pode não haver atividades cadastradas

## Solução

### Opção 1: Executar script via Render Shell

1. Acesse o dashboard do Render
2. Vá no seu serviço (Web Service)
3. Clique em **Shell** no menu lateral
4. Execute o comando:
```bash
python configurar_render_atividades.py
```

### Opção 2: Executar via Python Console

Se o Render tiver console Python:
```bash
python
```

Depois dentro do Python:
```python
exec(open('configurar_render_atividades.py').read())
```

### Opção 3: Configurar manualmente

1. **Acesse o sistema no Render**
2. **Faça login** como admin@obpc.com
3. Vá em **Gerenciar Usuários**
4. **Edite o usuário admin** e vincule a um departamento
5. Vá em **Departamentos** > Editar departamento
6. **Adicione uma atividade**
7. **Marque o checkbox "Exibir no Painel"**
8. Salve
9. Volte ao painel principal - a atividade deve aparecer

## Verificação

Após configurar:
- Faça **logout**
- Faça **login** novamente
- Acesse o **Painel**
- As atividades devem aparecer na seção "Atividades do Departamento"

## Checklist

- [ ] Usuário admin está vinculado a um departamento
- [ ] Existe pelo menos 1 departamento cadastrado
- [ ] Existe pelo menos 1 atividade cadastrada
- [ ] A atividade tem "Exibir no Painel" marcado
- [ ] A data da atividade é futura (ou hoje)
- [ ] A atividade está marcada como "Ativa"
