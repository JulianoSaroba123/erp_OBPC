# 📊 SOLUÇÃO: Despesas Fixas e 30% Administrativo

## 🎯 Objetivo

Implementar de forma profissional:
1. **Lançamento automático dos 30% administrativo** como saída real (não apenas informativo)
2. **Cadastro e geração automática de despesas fixas recorrentes**

---

## 📋 Problema Identificado

### Antes da Solução:
- ❌ Os **30% do administrativo** eram apenas informativos no relatório
- ❌ Não impactavam o **saldo real** da igreja
- ❌ Despesas fixas precisavam ser lançadas manualmente todo mês
- ❌ Risco de esquecer de lançar despesas recorrentes

### Depois da Solução:
- ✅ Os **30% administrativo** são criados como **lançamento de saída**
- ✅ Impactam o **saldo real** corretamente
- ✅ **5 despesas fixas** cadastradas e podem ser geradas automaticamente
- ✅ Interface profissional com dois botões no modal

---

## 🔧 Arquivos Criados/Modificados

### 1. **Script de Cadastro Inicial** 📝
**Arquivo:** `cadastrar_despesas_fixas_iniciais.py`

**Função:** Cadastra as 5 despesas fixas no banco de dados:
- Contribuição Força para Viver
- Contador
- Site
- Projeto Filipe
- Auxílio Conchas

**Como executar:**
```bash
python cadastrar_despesas_fixas_iniciais.py
```

**Resultado:**
- Cria as 5 despesas no banco com valor R$ 0,00 (para serem configuradas manualmente)
- Mostra lista de todas as despesas ativas
- Não duplica se já existirem

---

### 2. **Nova Rota: Gerar 30% Administrativo** 🚀
**Arquivo:** `app/financeiro/financeiro_routes.py`

**Rota:** `/financeiro/gerar-lancamento-administrativo` (POST)

**Funcionamento:**
1. Recebe mês/ano do formulário
2. Busca todos os lançamentos de **Entrada** do mês
3. Calcula base: **Dízimos + Ofertas Alçadas** (exclui OMN e Outras Ofertas)
4. Aplica percentual configurado (padrão 30%)
5. Cria lançamento de **saída** automático
6. Evita duplicação (verifica se já existe)

**Observações no lançamento:**
```
Base de cálculo: R$ X.XXX,XX 
(Dízimos: R$ X.XXX,XX + Ofertas Alçadas: R$ X.XXX,XX)
```

---

### 3. **Interface Atualizada** 🎨
**Arquivo:** `app/financeiro/templates/financeiro/gerenciar_despesas_fixas.html`

**Melhorias:**
- Modal reformulado em 2 colunas (layout profissional)
- **Card esquerdo:** Gerar Despesas Fixas
  - Lista todas as despesas ativas com valores
  - Mostra total mensal
  - Botão: "Gerar Despesas Fixas"
  
- **Card direito:** Gerar 30% Administrativo
  - Explica o cálculo (Dízimos + Ofertas Alçadas)
  - Calcula automaticamente
  - Botão: "Gerar 30% Administrativo"

- **Sincronização:** Ambos os formulários usam o mesmo mês/ano selecionado

---

## 📖 Como Usar (Passo a Passo)

### **PASSO 1: Cadastrar Despesas Fixas Iniciais**
```bash
# No terminal, na pasta do projeto:
python cadastrar_despesas_fixas_iniciais.py
```

**Resultado esperado:**
```
================================================================================
CADASTRO DE DESPESAS FIXAS - OBPC
================================================================================

✓ Cadastrando 'Contribuição Força para Viver'...
✓ Cadastrando 'Contador'...
✓ Cadastrando 'Site'...
✓ Cadastrando 'Projeto Filipe'...
✓ Cadastrando 'Auxílio Conchas'...

================================================================================
✅ OPERAÇÃO CONCLUÍDA COM SUCESSO!
   - 5 nova(s) despesa(s) cadastrada(s)
================================================================================
```

---

### **PASSO 2: Configurar Valores das Despesas**
1. Acesse o sistema ERP
2. Vá em **Financeiro** → **Gerenciar Despesas Fixas**
3. Para cada despesa:
   - Clique no botão **Editar** (ícone lápis)
   - Defina o **valor mensal correto**
   - Confirme que está **Ativa**
   - Salve

**Exemplo de valores:**
- Contribuição Força para Viver: R$ 200,00
- Contador: R$ 350,00
- Site: R$ 50,00
- Projeto Filipe: R$ 150,00
- Auxílio Conchas: R$ 300,00
- **Total mensal: R$ 1.050,00**

---

### **PASSO 3: Gerar Lançamentos Mensais**

#### **3.1 - Gerar Despesas Fixas**
1. Clique no botão **"Gerar Lançamentos"** (topo da página)
2. Selecione **mês e ano** desejado
3. No card **"Despesas Fixas"**, clique em **"Gerar Despesas Fixas"**
4. Sistema cria lançamentos de saída para todas as despesas ativas
5. Mensagem de sucesso mostra quantos lançamentos foram criados

**Exemplo de lançamento criado:**
```
Data: 01/02/2026
Tipo: Saída
Categoria: CONTRIB. SEDE
Descrição: Contribuição Força para Viver - Despesa Fixa 02/2026
Valor: R$ 200,00
Conta: Dinheiro
```

---

#### **3.2 - Gerar 30% Administrativo**
1. No mesmo modal de **"Gerar Lançamentos"**
2. Selecione **mês e ano** (mesmo das despesas fixas)
3. No card **"30% Administrativo"**, clique em **"Gerar 30% Administrativo"**
4. Sistema:
   - Busca lançamentos de Entrada do mês
   - Calcula: (Dízimos + Ofertas Alçadas) × 30%
   - Cria lançamento de saída automático

**Exemplo de lançamento criado:**
```
Data: 01/02/2026
Tipo: Saída
Categoria: CONTRIB. SEDE
Descrição: 30% Administrativo - Conselho Sede 02/2026
Valor: R$ 1.245,00
Conta: Dinheiro
Observações: Base de cálculo: R$ 4.150,00 
(Dízimos: R$ 2.800,00 + Ofertas Alçadas: R$ 1.350,00)
```

---

## 🔍 Lógica de Cálculo do 30%

### **O que ENTRA no cálculo:**
✅ **Dízimos**
✅ **Ofertas Alçadas** (ofertas normais do ofertório)

### **O que NÃO entra no cálculo:**
❌ **Ofertas OMN** (vai direto para convenção)
❌ **Outras Ofertas** (especiais, voluntárias)
❌ **Saídas** (despesas)

### **Fórmula:**
```
Base = Dízimos + Ofertas Alçadas
Valor do Conselho = Base × (Percentual / 100)
```

**Exemplo prático:**
```
Dízimos:          R$ 2.800,00
Ofertas Alçadas:  R$ 1.350,00
Ofertas OMN:      R$ 500,00  (não entra)
Outras Ofertas:   R$ 300,00  (não entra)
---------------------------------
Base de cálculo:  R$ 4.150,00
30% do conselho:  R$ 1.245,00 ✅ (criado como lançamento de saída)
```

---

## ✅ Benefícios da Solução

### **1. Profissionalismo**
- ✅ Lançamentos automáticos evitam erros humanos
- ✅ Rastreabilidade total (campo `origem='automatico'`)
- ✅ Observações detalhadas com base de cálculo

### **2. Transparência Financeira**
- ✅ 30% administrativo impacta o saldo real
- ✅ Relatórios refletem a situação financeira correta
- ✅ Despesas fixas sempre lançadas

### **3. Economia de Tempo**
- ✅ 6 lançamentos mensais automáticos (5 despesas + 30%)
- ✅ Não precisa lembrar de lançar todo mês
- ✅ Interface intuitiva e rápida

### **4. Controle Gerencial**
- ✅ Saldo real sempre atualizado
- ✅ Previsibilidade de despesas fixas
- ✅ Histórico completo de envios à sede

---

## 🚨 Avisos Importantes

### **Duplicação Inteligente**
- ✅ Sistema verifica antes de criar
- ✅ Não cria lançamento duplicado
- ✅ Mensagem clara se já existir

### **Ordem de Geração**
1. **Primeiro:** Lançar todas as ENTRADAS do mês
2. **Depois:** Gerar 30% administrativo (depende das entradas)
3. **Por último:** Gerar despesas fixas

### **Verificação Manual**
Após gerar automaticamente:
- Acesse **Financeiro** → **Lançamentos**
- Filtre pelo mês
- Confira se todos os lançamentos foram criados corretamente

---

## 📊 Relatório de Impacto

### **Antes:**
```
Total Entradas:    R$ 5.550,00
Total Saídas:      R$ 500,00
Saldo no Relatório: R$ 5.050,00 ❌ (incorreto, não descontou 30% e fixas)
```

### **Depois:**
```
Total Entradas:     R$ 5.550,00
Total Saídas:       R$ 2.795,00
  - Despesas Fixas: R$ 1.050,00
  - 30% Conselho:   R$ 1.245,00
  - Outras:         R$ 500,00
Saldo Real:         R$ 2.755,00 ✅ (correto!)
```

---

## 🎓 Recomendação de Uso Mensal

### **Rotina Sugerida:**
**Todo dia 1º do mês:**
1. Lançar todas as entradas e saídas do mês anterior
2. Acessar **Financeiro** → **Gerenciar Despesas Fixas**
3. Clicar em **"Gerar Lançamentos"**
4. Selecionar o **mês anterior**
5. Gerar **Despesas Fixas**
6. Gerar **30% Administrativo**
7. Conferir no relatório
8. Gerar PDF do relatório mensal

---

## 📞 Suporte

Em caso de dúvidas ou problemas:
1. Verifique os logs do sistema
2. Confira se as despesas estão ativas
3. Valide se há entradas lançadas no mês
4. Consulte este documento

---

**Desenvolvido por:** Equipe de Desenvolvimento ERP OBPC  
**Data:** 02/02/2026  
**Versão:** 1.0  

✅ **Sistema pronto para uso em produção!**
