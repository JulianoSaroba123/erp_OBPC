# RELATÓRIO FINANCEIRO OBPC - FECHAMENTO 26 → 25

## Data: 03/05/2026
## Status: ✅ IMPLEMENTADO E PRONTO PARA TESTE

---

## 📋 O QUE FOI IMPLEMENTADO

**Novo Relatório OBPC** com fechamento financeiro do dia 26 de um mês até o dia 25 do mês seguinte, seguindo as regras e normas da OBPC (Ordem Batista Pentecostal do Brasil).

---

## 🗓️ COMO FUNCIONA O FECHAMENTO 26 → 25

### Exemplo Prático (Maio/2026):
- **Período considerado:** 26/Abril/2026 até 25/Maio/2026
- **Enquadramento:** Este período completo é referente ao mês de Maio/2026

### Por que 26 → 25?
A OBPC trabalha com este modelo de fechamento para:
- Facilitar o fechamento contábil
- Dar tempo para preparar o envio para a Sede
- Padronizar o processo em todas as igrejas

---

## 💰 REGRAS OBPC IMPLEMENTADAS

### 1. **30% PARA A SEDE**

#### Regra:
30% são calculados **SOMENTE** sobre:
- ✅ **Dízimos**
- ✅ **Ofertas Alçadas** (ofertas comuns do ofertório)

#### NÃO entram no cálculo dos 30%:
- ❌ Outras Ofertas (especiais/voluntárias)
- ❌ Oferta OMN (missionária)
- ❌ Rendimentos
- ❌ Outras receitas

#### Exemplo de Cálculo:
```
Dízimos:           R$ 5.000,00
Ofertas Alçadas:   R$ 2.000,00
────────────────────────────
Base 30%:          R$ 7.000,00
30% da Base:       R$ 2.100,00  ← Valor para a Sede
```

---

### 2. **PREBENDA - LIMITE DE 30%**

#### Regra:
A prebenda (salário do pastor) não deve ultrapassar **30% das entradas totais** do período.

#### Cálculo:
```
Total de Entradas:  R$ 10.000,00
Prebenda:           R$  2.800,00
────────────────────────────────
Percentual:         28% ✅ Dentro do limite
```

#### Alerta no Sistema:
Se a prebenda ultrapassar 30%, o sistema exibe um **alerta em destaque** no relatório.

---

### 3. **SALDO OPERACIONAL DA IGREJA LOCAL**

#### Regra:
É o saldo disponível para a igreja operar, **já descontando** o compromisso de 30% com a Sede.

#### Cálculo:
```
Saldo Final (Caixa):         R$ 15.000,00
(-) 30% a enviar Sede:       R$  2.100,00
────────────────────────────────────────
Saldo Operacional:           R$ 12.900,00
```

Este é o valor que a igreja **realmente tem** para operar mensalmente.

---

## 📊 ESTRUTURA DO RELATÓRIO

### ENTRADAS
- Dízimos
- Ofertas Alçadas (comuns) *
- **Subtotal: Base 30% Sede** ← Destaque
- Outras Ofertas (especiais)
- Oferta OMN (missionária)
- Rendimentos
- Outras Entradas
- **TOTAL ENTRADAS**

`* Somente dízimos e ofertas alçadas compõem a base dos 30%`

### SAÍDAS
- Prebenda (com % sobre entradas)
- Despesas Fixas
- Despesas Variáveis
- Outras Saídas
- **TOTAL SAÍDAS**

### CÁLCULOS OBPC
#### 30% para a Sede:
- Base de Cálculo (Dízimos + Ofertas Comuns)
- 30% da Base
- Despesas Fixas do Conselho
- **TOTAL ENVIO SEDE**

#### Saldos:
- Saldo Anterior
- Entradas do Período
- Saídas do Período
- **Saldo Final (Caixa)**
- (-) 30% a Enviar para Sede
- **SALDO OPERACIONAL DISPONÍVEL** ← Destaque verde

---

## 🎯 COMO USAR

### 1. **Acessar o Relatório**

**Pelo Menu:**
1. Entre no módulo **Financeiro**
2. Clique no menu **"Relatórios"** (dropdown)
3. Selecione **"Relatório OBPC (26→25)"**

**Ou diretamente:**
- Acesse: `/financeiro/relatorio-obpc`

---

### 2. **Selecionar Período**

O relatório abre **automaticamente no mês atual**.

Para ver outros períodos:
- Use o **dropdown "Mês"** para selecionar
- Use o **dropdown "Ano"** para selecionar

**Exemplo:**
- Selecione **Maio/2026**
- O sistema automaticamente mostra: **26/Abril → 25/Maio**

---

### 3. **Visualizar e Imprimir**

**Opções disponíveis:**
- ✅ **Imprimir** - Botão "Imprimir" (versão otimizada para impressão)
- ✅ **Visualizar na tela** - Todos os dados já aparecem formatados
- 📋 **Copiar dados** - Pode copiar valores para relatórios externos

---

## 🚨 ALERTAS AUTOMÁTICOS

### Alerta 1: Prebenda Acima de 30%
```
⚠️ Atenção: A prebenda está em 32,5% das entradas, 
ultrapassando o limite recomendado de 30%.
```

### Alerta 2: Informações sobre o Fechamento
```
ℹ️ Fechamento OBPC: Este relatório considera o período de 
26/04/2026 até 25/05/2026. A OBPC trabalha com fechamento 
do dia 26 de um mês até o dia 25 do mês seguinte.
```

---

## 🧪 TESTE LOCAL - PASSO A PASSO

### 1. **Iniciar o Sistema**
```powershell
python run.py
```

### 2. **Fazer Login**
- Entre com suas credenciais

### 3. **Acessar Financeiro**
- Menu: Financeiro → Lançamentos

### 4. **Abrir Relatório OBPC**
- Click em "Relatórios" → "Relatório OBPC (26→25)"

### 5. **Verificar Dados**

**Conferir se está mostrando:**
- ✅ Período correto (26 do mês anterior → 25 do mês atual)
- ✅ Entradas classificadas corretamente
- ✅ Base 30% Sede (apenas dízimos + ofertas comuns)
- ✅ Cálculo dos 30%
- ✅ Prebenda com percentual
- ✅ Saldo operacional correto

### 6. **Testar Navegação**
- ✅ Trocar de mês
- ✅ Trocar de ano  
- ✅ Imprimir o relatório
- ✅ Voltar para listagem

---

## 📐 FÓRMULAS IMPLEMENTADAS

### Base para 30% da Sede:
```python
base_30_sede = dizimos + ofertas_alcadas
valor_30_sede = base_30_sede * 0.30
```

### Prebenda Percentual:
```python
if total_entradas > 0:
    prebenda_percentual = (prebenda / total_entradas) * 100
```

### Saldo Operacional:
```python
saldo_operacional = saldo_final - valor_30_sede
```

### Saldo Anterior (até dia 25 do mês anterior):
```python
data_limite = data_inicial - 1 dia
saldo_anterior = (entradas até data_limite) - (saídas até data_limite)
```

---

## 🎨 INTERFACE

### Cores e Destaques:

**Cards Superiores (Resumo):**
- 🟢 Verde: Total Entradas
- 🔴 Vermelho: Total Saídas
- 🔵 Azul: 30% para Sede
- 🔵 Azul/Amarelo: Saldo Operacional (positivo/negativo)

**Tabelas:**
- Dízimos: ícone 💚
- Ofertas Alçadas: ícone 🎁
- Outras Ofertas: ícone 🤝
- OMN: ícone 🌍
- Prebenda: ícone 👔

**Destaques:**
- Base 30%: linha destacada em azul claro
- Total Envio Sede: linha destacada em azul
- Saldo Operacional: linha destacada em verde, tamanho grande

---

## ✅ CHECKLIST DE VALIDAÇÃO

Use esta lista para confirmar que tudo funciona:

### Funcionalidades Básicas:
- [ ] O relatório abre sem erros
- [ ] Mostra o período correto (26 → 25)
- [ ] Calcula entradas corretamente
- [ ] Calcula saídas corretamente
- [ ] Exibe os cards de resumo

### Cálculos OBPC:
- [ ] Base 30% = Dízimos + Ofertas Alçadas apenas
- [ ] Outras ofertas NÃO entram na base
- [ ] OMN NÃO entra na base
- [ ] 30% calculado corretamente
- [ ] Prebenda % calculado corretamente
- [ ] Saldo operacional correto

### Alertas e Avisos:
- [ ] Mostra alerta se prebenda > 30%
- [ ] Exibe badge verde se prebenda ≤ 30%
- [ ] Mostra informações sobre fechamento OBPC

### Navegação:
- [ ] Dropdown de mês funciona
- [ ] Dropdown de ano funciona
- [ ] Botão "Voltar" funciona
- [ ] Botão "Imprimir" funciona

### Impressão:
- [ ] Layout de impressão está limpo
- [ ] Assinaturas aparecem na impressão
- [ ] Cabeçalho correto na impressão
- [ ] Dados completos na impressão

---

## 🔄 DIFERENÇA ENTRE RELATÓRIOS

### Relatório de **Caixa Interno** (mensal):
- Período: 1º dia até último dia do mês
- Uso: Controle interno da igreja
- Formato: Detalhado com banco/dinheiro separados

### Relatório **OBPC** (26 → 25):
- Período: Dia 26 até dia 25 (fechamento OBPC)
- Uso: Prestação de contas oficial para a Sede
- Formato: Consolidado com regras OBPC
- Destaque: 30% apenas sobre dízimos + ofertas comuns
- Inclui: Saldo operacional e controle de prebenda

### Relatório para **Sede** (mensal):
- Período: 1º dia até último dia do mês
- Uso: Envio oficial para a Sede OBPC
- Formato: Oficial com campos específicos para preenchimento

---

## 🔍 EXEMPLO COMPLETO

### Dados do Período (26/Abr → 25/Mai):

**ENTRADAS:**
- Dízimos: R$ 5.000,00
- Ofertas Alçadas: R$ 2.000,00
- Outras Ofertas: R$ 800,00
- Oferta OMN: R$ 500,00
- Rendimentos: R$ 50,00
- **Total: R$ 8.350,00**

**SAÍDAS:**
- Prebenda: R$ 2.400,00 (28,7% ✅)
- Despesas Fixas: R$ 800,00
- Despesas Variáveis: R$ 1.200,00
- **Total: R$ 4.400,00**

**CÁLCULOS OBPC:**
- Base 30%: R$ 7.000,00 (dízimos + ofertas comuns)
- 30% Sede: R$ 2.100,00
- Despesas Fixas Conselho: R$ 150,00
- **Total Envio Sede: R$ 2.250,00**

**SALDOS:**
- Saldo Anterior: R$ 3.000,00
- Saldo Período: R$ 3.950,00
- Saldo Final: R$ 6.950,00
- (-) 30% Sede: R$ 2.100,00
- **Saldo Operacional: R$ 4.850,00** ✅

---

## 📞 PRÓXIMOS PASSOS

Após confirmar que o relatório OBPC funciona perfeitamente:

1. **Testar com dados reais** do seu banco
2. **Validar os cálculos** comparando manualmente
3. **Treinar usuários** no uso do novo relatório
4. **Fazer backup** antes de usar em produção

---

## 📁 ARQUIVOS MODIFICADOS/CRIADOS

### Modificados:
- ✅ `app/financeiro/financeiro_routes.py` - Nova rota adicionada
- ✅ `app/financeiro/templates/financeiro/lista_lancamentos.html` - Link no menu

### Criados:
- ✅ `app/financeiro/templates/financeiro/relatorio_obpc.html` - Template novo
- ✅ `RELATORIO_OBPC_26_25_IMPLEMENTADO.md` - Esta documentação

---

**Status:** ✅ Implementado e pronto para teste  
**Desenvolvido em:** 03/05/2026  
**Próxima funcionalidade:** Ajustes finos conforme feedback
