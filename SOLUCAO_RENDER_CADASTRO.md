# 🔧 SOLUÇÃO: Configurar Banco de Dados no Render

## Problema
O cadastro de membros não está funcionando no Render porque o banco PostgreSQL precisa ser configurado.

## Solução - Execute no Shell do Render

### Passo 1: Acessar o Shell do Render

1. Acesse https://dashboard.render.com
2. Clique no seu Web Service (erp_OBPC)
3. Clique na aba **"Shell"** no menu superior
4. Aguarde o shell abrir

### Passo 2: Executar Script de Configuração

No shell do Render, execute o seguinte comando:

```bash
python configurar_banco_render_completo.py
```

Este script irá:
- ✅ Criar todas as 26+ tabelas necessárias
- ✅ Adicionar as colunas extras na tabela membros (CPF, número, bairro, etc.)
- ✅ Criar o usuário admin (se não existir)

**Se aparecer aviso sobre agenda_pastoral, execute também:**
```bash
python criar_agenda_pastoral_render.py
```

### Passo 3: Aguardar Conclusão

Você verá uma mensagem assim ao final:

```
==============================================================
CONFIGURACAO CONCLUIDA COM SUCESSO!
==============================================================

Tabelas criadas: 26
Colunas extras adicionadas: X

Voce pode agora:
1. Acessar o sistema no Render
2. Fazer login com admin@obpc.com / admin123
3. Cadastrar membros com todos os campos
==============================================================
```

### Passo 4: Testar o Sistema

1. Acesse sua URL do Render (ex: https://erp-obpc.onrender.com)
2. Faça login com:
   - Email: `admin@obpc.com`
   - Senha: `admin123`
3. Vá em **Membros > Novo Membro**
4. Cadastre um membro de teste

## Alternativa: Executar Scripts Separados

Se o script completo não funcionar, execute na ordem:

```bash
# 1. Criar tabelas
python criar_tabelas_render.py

# 2. Adicionar colunas extras
python atualizar_membros_render.py
```

## Verificar se Funcionou

No shell do Render, execute para verificar:

```bash
python -c "from app import create_app; from app.extensoes import db; from sqlalchemy import inspect; app = create_app(); inspector = inspect(db.engine); print('Tabelas:', inspector.get_table_names())"
```

## Problemas Comuns

### Erro: "No module named 'app'"
- Certifique-se de estar no diretório raiz do projeto
- Execute: `cd /opt/render/project/src`

### Erro: "DATABASE_URL not found"
- Verifique se o banco PostgreSQL está conectado ao Web Service
- Vá em Dashboard > Seu Web Service > Environment
- Confirme que a variável `DATABASE_URL` existe

### Timeout no Shell
- Tente novamente - às vezes o Render demora para inicializar
- Se persistir, use o script mais simples: `criar_tabelas_render.py`

## 🎯 Resultado Esperado

Após executar com sucesso:
- ✅ Tabela `membros` criada com 23 colunas
- ✅ Cadastro de membros funcionando
- ✅ Todos os campos disponíveis (CPF, endereço completo, teologia, etc.)
- ✅ Login funcionando com admin@obpc.com

## Contato

Se continuar com problemas, verifique:
1. Logs do Render (aba "Logs")
2. Se o deploy foi concluído com sucesso
3. Se a aplicação está rodando (status "Live")
