# 📋 INSTRUÇÕES DE DEPLOY RENDER - SISTEMA DE RECIBOS

## ✅ Pré-requisitos Concluídos

### 1. Banco de Dados Local
- ✅ Tabela `recibo` criada com sucesso
- ✅ Modelo SQLAlchemy configurado em `app/financeiro/recibo_model.py`
- ✅ 12 colunas implementadas

### 2. CRUD Completo
- ✅ 5 rotas implementadas em `financeiro_routes.py`:
  - `lista_recibos` (GET) - Listagem com paginação e filtros
  - `novo_recibo` (GET/POST) - Criação de recibos
  - `visualizar_recibo` (GET) - Visualização detalhada
  - `gerar_pdf_recibo` (GET) - Regeneração de PDF
  - `excluir_recibo` (POST) - Exclusão com confirmação

### 3. Templates Criados
- ✅ `lista_recibos.html` - Tabela com métricas e filtros
- ✅ `visualizar_recibo.html` - Visualização detalhada
- ✅ `emitir_recibo.html` - Formulário de emissão (já existente)

### 4. Navegação
- ✅ Menu atualizado em `base.html`
- ✅ Links para "Emitir Recibo" e "Gerenciar Recibos"

### 5. Dependencies
- ✅ `reportlab==4.0.7` - Geração de PDF
- ✅ `pytz==2023.3` - Timezone Brasil (ADICIONADO)
- ✅ `psycopg2-binary==2.9.9` - PostgreSQL driver
- ✅ `gunicorn==21.2.0` - Servidor de produção

---

## 🚀 PASSOS PARA DEPLOY NO RENDER

### Passo 1: Fazer Push do Código
```bash
git add .
git commit -m "Sistema CRUD de Recibos completo - pronto para Render"
git push origin main
```

### Passo 2: Configurar Banco no Render
1. Acesse o Dashboard do Render
2. Vá em **PostgreSQL** (se já existe) ou crie um novo:
   - Clique em **New +** → **PostgreSQL**
   - Nome: `sistema-obpc-db` (ou similar)
   - Region: **Ohio (US East)** (recomendado para menor latência)
   - PostgreSQL Version: **15** ou superior
   - Plan: **Free** ou **Starter**
3. Após criação, copie a **Internal Database URL**

### Passo 3: Atualizar Web Service
1. Acesse seu Web Service no Render Dashboard
2. Vá em **Environment** → **Environment Variables**
3. Adicione/atualize:
   ```
   DATABASE_URL = [Cole a Internal Database URL do PostgreSQL]
   FLASK_ENV = production
   SECRET_KEY = [sua chave secreta]
   ```

### Passo 4: Executar Migration no Render
**IMPORTANTE:** A tabela `recibo` precisa ser criada no PostgreSQL do Render.

#### Opção A: Via Render Shell (Recomendado)
1. No Dashboard do Render, acesse seu Web Service
2. Clique em **Shell** (canto superior direito)
3. Execute:
   ```bash
   python configurar_banco_recibos.py
   ```

#### Opção B: Conectar via PostgreSQL Client
1. Instale psql localmente
2. Conecte usando a **External Database URL**:
   ```bash
   psql [External Database URL]
   ```
3. Execute o SQL manualmente:
   ```sql
   CREATE TABLE recibo (
       id SERIAL PRIMARY KEY,
       numero_recibo VARCHAR(50) UNIQUE NOT NULL,
       nome_recebedor VARCHAR(200) NOT NULL,
       cpf_cnpj_recebedor VARCHAR(20),
       valor NUMERIC(10, 2) NOT NULL,
       data_pagamento DATE NOT NULL,
       referente_a TEXT NOT NULL,
       forma_pagamento VARCHAR(50) NOT NULL,
       observacoes TEXT,
       criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
       criado_por VARCHAR(100),
       pdf_gerado BOOLEAN DEFAULT FALSE
   );
   ```

### Passo 5: Deploy
1. O Render detectará automaticamente o push e iniciará o deploy
2. Aguarde até STATUS = **Live** (verde)
3. Verifique os logs em **Logs**

### Passo 6: Verificar Funcionamento
1. Acesse seu domínio Render: `https://seu-app.onrender.com`
2. Faça login
3. Vá em **Financeiro** → **Emitir Recibo**
4. Teste criando um recibo
5. Acesse **Gerenciar Recibos** para ver a lista

---

## 🔍 Checklist de Verificação

- [ ] Código commitado e pushed para GitHub
- [ ] Variável `DATABASE_URL` configurada no Render
- [ ] Tabela `recibo` criada no PostgreSQL do Render
- [ ] Deploy concluído com sucesso (status Live)
- [ ] Menu "Gerenciar Recibos" aparece no sistema
- [ ] Possível criar novo recibo
- [ ] PDF é gerado corretamente
- [ ] Lista de recibos carrega com paginação
- [ ] Filtros de data e busca funcionam
- [ ] Visualização de recibo individual funciona
- [ ] Exclusão de recibo funciona

---

## 🐛 Troubleshooting

### Erro: "Table 'recibo' doesn't exist"
**Solução:** Executar Passo 4 (migration no Render)

### Erro: "ImportError: pytz"
**Solução:** Verificar se `pytz==2023.3` está no `requirements.txt` e fazer redeploy

### PDF não gera ou mostra horário errado
**Solução:** Verificar importação de pytz em `gerar_pdf_reportlab.py`

### Erro 500 ao acessar lista de recibos
**Solução:** 
1. Verificar logs no Render
2. Verificar se migration foi executada
3. Verificar se modelo está importado corretamente

### Render não detecta mudanças
**Solução:**
```bash
# Forçar deploy manual no Render Dashboard
# Ou fazer um commit vazio:
git commit --allow-empty -m "Trigger Render deploy"
git push origin main
```

---

## 📊 Estrutura do Sistema de Recibos

### Modelo (Database)
```
recibo
├── id (PK)
├── numero_recibo (UNIQUE, formato: REC-2025-00001)
├── nome_recebedor
├── cpf_cnpj_recebedor
├── valor
├── data_pagamento
├── referente_a
├── forma_pagamento
├── observacoes
├── criado_em
├── criado_por
└── pdf_gerado
```

### Fluxo de Emissão
1. Usuário acessa "Emitir Recibo"
2. Preenche formulário (nome, valor, data, etc.)
3. Sistema valida dados
4. Gera número sequencial automático
5. Salva no banco de dados
6. Gera PDF em tempo real
7. Retorna PDF para download
8. Marca `pdf_gerado = True`

### Funcionalidades CRUD
- **Create:** Formulário → Validação → Banco → PDF
- **Read:** Lista paginada + Visualização individual
- **Update:** Não implementado (recibos são documentos legais)
- **Delete:** Exclusão com confirmação (apenas admin)

---

## 🎯 Próximas Melhorias (Opcional)

- [ ] Exportar recibos para Excel
- [ ] Enviar recibo por e-mail automaticamente
- [ ] Dashboard de recibos emitidos por período
- [ ] Validação de CPF/CNPJ no formulário
- [ ] Histórico de alterações (audit log)
- [ ] Numeração customizável por departamento

---

## 📞 Suporte

Se encontrar problemas durante o deploy:
1. Verifique os logs do Render
2. Execute `get_errors` no VS Code
3. Teste localmente com PostgreSQL antes do deploy
4. Consulte documentação oficial: https://render.com/docs

---

**✅ Sistema pronto para produção no Render!**
