# Indicadores de Distribuição Financeira - Implementado ✅

## Data: 11/05/2026

## Descrição
Implementação de um sistema completo de indicadores que mostra como as entradas (Ofertas e Dízimos) devem ser distribuídas e alerta quando a distribuição real não está seguindo o planejamento.

---

## 📊 Funcionalidades Implementadas

### 1. Modelo de Dados
**Arquivo:** `app/configuracoes/configuracoes_model.py`

Novos campos adicionados à tabela `configuracoes`:
- `percentual_administrativo` (FLOAT) - Percentual para Administrativo Sede (fixo 30%)
- `percentual_prebenda` (FLOAT) - Percentual para Prebenda Pastoral (ajustável 0-30%)
- `percentual_cuidados_igreja` (FLOAT) - Percentual para Cuidados da Igreja (fixo 40%)
- `exibir_indicador_distribuicao` (BOOLEAN) - Controla exibição no dashboard

### 2. Script de Migração
**Arquivo:** `adicionar_indicadores_distribuicao.py`

Script que:
- ✅ Adiciona as novas colunas ao banco de dados
- ✅ Define valores padrão (30%, 30%, 40%)
- ✅ Compatível com SQLite e PostgreSQL
- ✅ Valida se as colunas já existem antes de adicionar
- ✅ Atualiza configuração existente

### 3. Dashboard com Indicadores
**Arquivo:** `app/financeiro/financeiro_routes.py`

Cálculos implementados:
- ✅ Total de Ofertas e Dízimos do mês
- ✅ Valores ideais por categoria baseados nos percentuais
- ✅ Valores reais das despesas por categoria
- ✅ Percentuais reais vs ideais
- ✅ Desvios calculados com tolerância de ±5%
- ✅ Sistema de alertas automático
- ✅ Status geral (ok, atenção, crítico)

**Categorias monitoradas:**
1. **Administrativo Sede (30%)**
   - Despesas administrativas, sede, escritório, material escritório
   
2. **Prebenda Pastoral (0-30% ajustável)**
   - Prebenda, salários, honorários, pastoral
   
3. **Cuidados da Igreja (40%)**
   - Manutenção, energia, água, internet, telefone, limpeza, reforma, conservação, aluguel

### 4. Interface Visual no Dashboard
**Arquivo:** `app/financeiro/templates/financeiro/dashboard_moderno.html`

Componentes visuais:
- ✅ Card destacado com total de Ofertas e Dízimos
- ✅ Alertas automáticos quando desvios > 5%
- ✅ 3 cards coloridos (um por categoria)
- ✅ Indicadores visuais:
  - Percentual Ideal vs Real
  - Valor Ideal vs Valor Gasto
  - Barra de progresso de utilização
  - Status com ícones (✓ ok, ⚠ acima, ℹ abaixo)
- ✅ Badges identificando campos fixos e ajustáveis
- ✅ Cores dinâmicas baseadas no status
- ✅ Link direto para configurações

### 5. Página de Configuração
**Arquivo:** `app/configuracoes/templates/configuracoes/configuracoes.html`

Aba Financeiro atualizada com:
- ✅ Switch para ativar/desativar indicadores
- ✅ Campo Administrativo Sede (30% - somente leitura)
- ✅ Campo Prebenda Pastoral (0-30% - editável)
- ✅ Campo Cuidados da Igreja (40% - somente leitura)
- ✅ Cálculo automático do total em tempo real
- ✅ Validação de limites (Prebenda: 0-30%)
- ✅ Indicador visual do total (verde=100%, amarelo<100%, vermelho>100%)
- ✅ Explicação detalhada de cada categoria

**JavaScript implementado:**
- ✅ Função `atualizarTotalPercentuais()`
- ✅ Validação em tempo real do campo Prebenda
- ✅ Feedback visual imediato
- ✅ Prevenção de valores fora dos limites

### 6. Rotas Atualizadas
**Arquivo:** `app/configuracoes/configuracoes_routes.py`

Salvar configurações atualizado:
- ✅ Leitura dos novos campos do formulário
- ✅ Validação: Prebenda entre 0% e 30%
- ✅ Alerta se total ≠ 100%
- ✅ Persistência no banco de dados

---

## 🎨 Design e UX

### Cores e Status
- **Verde** (success): Dentro do planejado (desvio ≤ 5%)
- **Amarelo** (warning): Acima do ideal (desvio > 5%)
- **Azul** (info): Abaixo do ideal (desvio > 5%)
- **Vermelho** (danger): Crítico (utilização > 120%)

### Badges
- 🔒 **Fixo**: Campos com percentual não editável
- 🎚️ **Ajustável**: Campos que podem ser modificados

### Alertas Automáticos
Aparecem quando:
- Desvio > 5% em qualquer categoria
- Tipo: warning (acima) ou info (abaixo)
- Podem ser fechados pelo usuário
- Exemplos:
  - "Despesas administrativas acima do ideal (8.5%)"
  - "Prebenda pastoral abaixo do ideal (12.3%)"

---

## 📐 Regras de Negócio

### Distribuição Padrão (100%)
```
30% - Administrativo Sede (fixo)
30% - Prebenda Pastoral (ajustável 0-30%)
40% - Cuidados da Igreja (fixo)
────────────────────────────
100% Total
```

### Tolerância
- ±5% é considerado aceitável
- Status "ok" se desvio ≤ 5%
- Alertas apenas se desvio > 5%

### Categorias de Lançamentos
**Ofertas e Dízimos (Entradas):**
- Categorias contendo: 'oferta', 'dízimo', 'dizimo'

**Administrativo Sede (Saídas):**
- Categorias contendo: 'administrativo', 'sede', 'escritório', 'escritorio', 'material escritório', 'material escritorio'

**Prebenda Pastoral (Saídas):**
- Categorias contendo: 'prebenda', 'salário', 'salario', 'honorário', 'honorario', 'pastoral'

**Cuidados da Igreja (Saídas):**
- Categorias contendo: 'manutenção', 'manutencao', 'energia', 'água', 'agua', 'internet', 'telefone', 'limpeza', 'reforma', 'conservação', 'conservacao', 'aluguel'

---

## 🚀 Como Usar

### 1. Executar o Script de Migração
```bash
python adicionar_indicadores_distribuicao.py
```

### 2. Acessar o Dashboard
- Navegar para `/financeiro/dashboard`
- Visualizar os indicadores de distribuição
- Verificar alertas (se houver)

### 3. Configurar Percentuais
- Ir para "Configurações" → Aba "Financeiro"
- Seção "Indicadores de Distribuição Financeira"
- Ajustar o percentual de Prebenda (0-30%)
- Verificar que o total atinge 100%
- Salvar configurações

### 4. Interpretar os Indicadores
- **Verde**: Tudo certo, distribuição dentro do planejado
- **Amarelo/Azul**: Pequenos desvios, atenção necessária
- **Vermelho**: Requer ajustes urgentes

---

## 📝 Exemplos de Uso

### Cenário 1: Igreja com Pastor Fixo (30%)
```
Administrativo: 30%
Prebenda: 30%
Cuidados: 40%
Total: 100% ✓
```

### Cenário 2: Igreja sem Pastor (0%)
```
Administrativo: 30%
Prebenda: 0%
Cuidados: 40%
Total: 70% ⚠️ (Ajustar Administrativo ou Cuidados manualmente)
```

### Cenário 3: Meio Período (15%)
```
Administrativo: 30%
Prebenda: 15%
Cuidados: 40%
Total: 85% ⚠️ (Ajustar outras categorias conforme necessário)
```

> **Nota:** Se o total não for 100%, o sistema emite um alerta mas permite salvar, para flexibilidade.

---

## ✅ Validações Implementadas

1. ✅ Prebenda entre 0% e 30%
2. ✅ Alerta se total ≠ 100%
3. ✅ Tolerância de ±5% nos desvios
4. ✅ Proteção contra valores negativos
5. ✅ Campos fixos são readonly no formulário
6. ✅ JavaScript valida em tempo real

---

## 🔧 Manutenção

### Adicionar Nova Categoria
1. Editar `financeiro_routes.py` → função `dashboard_moderno()`
2. Adicionar palavras-chave na lista de categorias
3. Exemplo:
```python
any(keyword in l.categoria.lower() for keyword in ['nova', 'categoria', 'palavras'])
```

### Ajustar Tolerância
Alterar linha no `financeiro_routes.py`:
```python
if abs(desvio) <= 5:  # Alterar 5 para outro valor
    return 'ok'
```

### Modificar Percentuais Fixos
1. Editar modelo: `configuracoes_model.py`
2. Atualizar valores default
3. Executar script de migração novamente
4. Atualizar template HTML com novos valores

---

## 📊 Benefícios

✅ **Visibilidade**: Saber exatamente para onde o dinheiro está indo
✅ **Planejamento**: Comparar ideal vs real mensalmente
✅ **Alertas**: Notificação automática de desvios
✅ **Flexibilidade**: Ajustar Prebenda conforme necessidade (0-30%)
✅ **Conformidade**: Manter distribuição dentro do planejamento
✅ **Decisão**: Dados para ajustes orçamentários

---

## 🎯 Próximas Melhorias (Opcional)

- [ ] Gráfico visual (pizza/barras) dos percentuais
- [ ] Histórico mensal da distribuição
- [ ] Relatório PDF com indicadores
- [ ] Notificações por email quando desvio > 10%
- [ ] Meta ajustável por categoria
- [ ] Comparação ano a ano

---

## 📌 Arquivos Modificados

1. ✅ `app/configuracoes/configuracoes_model.py` - Modelo de dados
2. ✅ `app/configuracoes/configuracoes_routes.py` - Rotas de configuração
3. ✅ `app/configuracoes/templates/configuracoes/configuracoes.html` - Interface de configuração
4. ✅ `app/financeiro/financeiro_routes.py` - Cálculo dos indicadores
5. ✅ `app/financeiro/templates/financeiro/dashboard_moderno.html` - Visualização dos indicadores
6. ✅ `adicionar_indicadores_distribuicao.py` - Script de migração

---

## ✨ Conclusão

Sistema de **Indicadores de Distribuição Financeira** implementado com sucesso!

O sistema agora permite:
- ✅ Visualizar distribuição ideal vs real das ofertas e dízimos
- ✅ Receber alertas automáticos de desvios
- ✅ Ajustar o percentual de Prebenda (0-30%) conforme necessidade
- ✅ Monitorar se consegue manter a igreja com a distribuição planejada

**Status:** 🟢 Concluído e Funcional
**Data:** 11/05/2026
**Testado:** ✅ Sim
