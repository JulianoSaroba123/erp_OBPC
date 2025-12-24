# ⚡ Guia Rápido - Despesas Fixas da Igreja

## 🚀 Acesso Rápido

```
Menu Lateral → Financeiro → Despesas Fixas
ou
http://localhost:5000/financeiro/despesas-fixas
```

## 📝 Operações Disponíveis

### ➕ Criar Nova Despesa
1. Clique em **"+ Nova Despesa"** (botão verde)
2. Preencha nome, descrição, **selecione a categoria** e valor
3. **IMPORTANTE**: Use categorias de saída dos lançamentos (ex: DESP. FIXAS)
4. Clique em **"Salvar"**

### ⚡ Gerar Lançamentos Automáticos ⭐ NOVO
1. Clique em **"⚡ Gerar Lançamentos"** (botão azul)
2. Selecione mês e ano
3. Clique em **"Gerar Lançamentos"**
4. Lançamentos de saída serão criados automaticamente!

### ✏️ Editar Despesa
1. Na tabela, clique no botão **azul** (ícone de lápis)
2. Altere os dados (incluindo categoria)
3. Clique em **"Atualizar"**

### ⏸️ Ativar/Desativar
1. Clique no botão **amarelo** (pausar) ou **verde** (play)
2. Confirme a ação

### 🗑️ Excluir Permanentemente
1. Clique no botão **vermelho** (lixeira)
2. Confirme a exclusão (NÃO pode ser desfeita!)

## 💡 Dicas

- **Use categorias consistentes**: Selecione categorias de saída já existentes
- **Gere lançamentos mensalmente**: Use "Gerar Lançamentos" no início de cada mês
- **Não exclua** despesas que podem voltar - apenas **desative**
- O **valor total mensal** e **anual** são calculados automaticamente
- Despesas **inativas** aparecem em cinza na tabela
- Lançamentos gerados têm origem "automatico" para rastreabilidade

## 🔄 Integração com Lançamentos

- ✅ Categorias sincronizadas com lançamentos de saída
- ✅ Gera lançamentos automáticos no formato padrão
- ✅ Evita duplicação de lançamentos
- ✅ Usa a mesma estrutura de dados dos lançamentos manuais

## 🧪 Testar o Sistema

Execute o script de teste:
```bash
python testar_despesas_fixas.py
```

## 📊 Exemplos de Despesas

- Contador Sede: R$ 500,00
- Site da Igreja: R$ 50,00
- Luz: R$ 300,00
- Água: R$ 100,00
- Internet: R$ 150,00
- Telefone: R$ 80,00
- Limpeza: R$ 200,00
- Segurança: R$ 400,00

## ⚠️ Importante

- Apenas usuários com **permissão de Tesoureiro, Admin ou Master** podem acessar
- Todas as alterações são **salvas imediatamente** no banco de dados
- A **exclusão é permanente** - não pode ser desfeita!

---
**Sistema OBPC** | Igreja O Brasil para Cristo - Tietê/SP
