# Sistema de Despesas Fixas da Igreja - OBPC

## 📋 Resumo da Implementação

O módulo de **Despesas Fixas** foi totalmente implementado no sistema financeiro da Igreja O Brasil para Cristo (OBPC) de Tietê/SP. Agora você tem um controle completo sobre os custos fixos mensais da igreja.

## ✅ Funcionalidades Implementadas

### 1. **CREATE (Criar)**
- ✅ Adicionar novas despesas fixas através de um formulário modal
- ✅ Campos disponíveis:
  - Nome da despesa (obrigatório)
  - Descrição detalhada (opcional)
  - Categoria (opcional)
  - Valor mensal (obrigatório)
  - Status automático (sempre ativa ao criar)

### 2. **READ (Visualizar)**
- ✅ Tabela completa com todas as despesas fixas (ativas e inativas)
- ✅ Cards informativos mostrando:
  - Total de despesas ativas
  - Valor total mensal
  - Projeção anual (valor mensal × 12)
- ✅ Identificação visual de despesas inativas na tabela

### 3. **UPDATE (Editar)**
- ✅ Botão de edição para cada despesa
- ✅ Modal de edição com todos os campos preenchidos
- ✅ Possibilidade de ativar/desativar despesas
- ✅ Validação de dados antes de salvar
- ✅ Feedback visual de sucesso/erro

### 4. **DELETE (Excluir)**
- ✅ Botão de exclusão com ícone de lixeira
- ✅ Confirmação dupla antes de excluir
- ✅ Mensagem clara de que a exclusão é permanente
- ✅ Remoção completa do banco de dados

### 5. **Outros Recursos**
- ✅ Ativar/Desativar despesas sem excluí-las
- ✅ Integração com relatórios financeiros
- ✅ Cálculo automático de totais
- ✅ Interface moderna e responsiva
- ✅ Validação de dados com mensagens de erro claras

## 🔗 Como Acessar

1. Faça login no sistema OBPC
2. No menu lateral, clique em **Financeiro**
3. No submenu que se abre, clique em **Despesas Fixas**
4. Ou acesse diretamente: `http://localhost:5000/financeiro/despesas-fixas`

## 📝 Como Usar

### Criar Nova Despesa Fixa

1. Clique no botão verde **"+ Nova Despesa"** no canto superior direito
2. Preencha o formulário:
   - **Nome**: Ex: "Contador Sede", "Site da Igreja", "Luz", "Água"
   - **Descrição**: Ex: "Pagamento mensal do contador responsável pela sede"
   - **Categoria**: Ex: "Serviços Profissionais", "Utilidades", "Manutenção"
   - **Valor Mensal**: Ex: 500.00
3. Clique em **"Salvar"**

### Editar Despesa Fixa

1. Na tabela, localize a despesa que deseja editar
2. Clique no botão azul com ícone de lápis (✏️)
3. Altere os campos necessários no modal que se abre
4. Marque/desmarque "Despesa ativa" conforme necessário
5. Clique em **"Atualizar"**

### Ativar/Desativar Despesa

1. Na tabela, localize a despesa
2. Clique no botão amarelo (▶) para desativar ou verde (▶) para reativar
3. Confirme a ação
4. Despesas inativas ficam em cinza na tabela e não são contabilizadas nos totais

### Excluir Despesa Permanentemente

1. Na tabela, localize a despesa que deseja excluir
2. Clique no botão vermelho com ícone de lixeira (🗑️)
3. **ATENÇÃO**: Leia a mensagem de confirmação cuidadosamente
4. Confirme a exclusão (esta ação NÃO pode ser desfeita)

## 🎨 Interface Visual

### Cards de Resumo
- **Card Azul**: Total de despesas ativas
- **Card Verde**: Valor total mensal de todas as despesas ativas
- **Card Laranja**: Projeção anual (total mensal × 12 meses)

### Tabela de Despesas
- **Linhas brancas**: Despesas ativas
- **Linhas cinzas**: Despesas inativas
- **Badge verde**: Status "Ativa"
- **Badge cinza**: Status "Inativa"

### Botões de Ação
- 🔵 **Azul (Lápis)**: Editar despesa
- 🟡 **Amarelo (Pausa)**: Desativar despesa ativa
- 🟢 **Verde (Play)**: Reativar despesa inativa
- 🔴 **Vermelho (Lixeira)**: Excluir permanentemente

## 💾 Estrutura de Banco de Dados

A tabela `despesas_fixas_conselho` contém:

```
- id: Identificador único
- nome: Nome da despesa
- descricao: Descrição detalhada (opcional)
- valor_padrao: Valor mensal
- ativo: Se está ativa (True/False)
- tipo: Tipo da despesa (padrão: 'despesa_fixa')
- categoria: Categoria (opcional)
- data_criacao: Data de criação automática
- data_atualizacao: Data da última atualização automática
```

## 🔒 Validações Implementadas

- ✅ Nome não pode ser vazio
- ✅ Valor deve ser maior ou igual a zero
- ✅ Espaços em branco são removidos automaticamente dos campos de texto
- ✅ Confirmação obrigatória antes de excluir
- ✅ Mensagens de erro específicas para cada tipo de validação

## 🔗 Integração com o Sistema

As despesas fixas estão integradas com:
- **Relatórios Financeiros**: Os valores são incluídos automaticamente
- **Relatório da Sede**: Despesas específicas são mapeadas (Contador, Site, Projetos, etc.)
- **Dashboard Financeiro**: Totais são calculados automaticamente

## 📊 Exemplos de Despesas Fixas

Você pode cadastrar despesas como:
- Contador Sede
- Site da Igreja
- Oferta Voluntária Conchas
- Projeto Filipe
- Força para Viver
- Luz
- Água
- Internet
- Telefone
- Aluguel
- Segurança
- Limpeza
- E qualquer outro custo fixo mensal da igreja

## 🎯 Próximos Passos Sugeridos

1. Cadastre todas as despesas fixas atuais da igreja
2. Revise e atualize os valores mensalmente
3. Use os relatórios para acompanhar o impacto das despesas fixas no orçamento
4. Desative despesas temporariamente suspensas (não exclua, para manter histórico)
5. Exclua apenas despesas que nunca mais serão utilizadas

## 🛠️ Arquivos Modificados/Criados

1. **app/financeiro/despesas_fixas_model.py** - Modelo de dados melhorado com validações
2. **app/financeiro/financeiro_routes.py** - Rotas CRUD completas
3. **app/financeiro/templates/financeiro/gerenciar_despesas_fixas.html** - Interface completa
4. **app/templates/base.html** - Menu com link para despesas fixas

## ❓ Suporte

Se tiver dúvidas ou problemas:
1. Verifique se você tem permissão de acesso ao módulo Financeiro
2. Confirme se está logado como Tesoureiro, Admin ou Master
3. Verifique se os dados estão sendo salvos corretamente no banco de dados

---

**Desenvolvido para Igreja O Brasil para Cristo - Tietê/SP**  
*Sistema ERP OBPC - Módulo Financeiro*  
Data de Implementação: Dezembro de 2024
