# PADRONIZAÇÃO DAS OFERTAS - SISTEMA OBPC

## Regra vigente | Tesouraria OBPC, 10/11/2026

A tesouraria confirmou que as **ofertas OMN entram efetivamente no caixa da igreja**, em
Dinheiro ou Banco/Pix. A tesouraria depois paga o boleto da Convenção. A distinção
entre recebimento e pagamento deve aparecer no Livro Caixa:

- **Entrada OMN:** categoria `OFERTA OMN`, tipo `Entrada`, conta `Dinheiro`, `Pix` ou `Banco`
  conforme o valor realmente recebido; o valor efetivamente recebido aumenta o saldo financeiro
  consolidado da OBPC e é apresentado separadamente das ofertas de culto.
- **Boleto da Convenção:** tipo `Saída` na data e conta do pagamento efetivo,
  com identificação do boleto e comprovante. A evidência de conciliação não deve
  criar uma segunda saída. A convenção não equivale automaticamente à Sede.
- **Base de 30% administrativos:** **OMN NÃO integra** a base, composta por Dízimos
  e Ofertas de culto. Outras ofertas não entram automaticamente nessa base.
- **Conferência:** um boleto da Convenção pode conter outras obrigações e competências.
  Não presumir que seu valor corresponde exatamente à OMN do mesmo mês.
- **Histórico:** os registros antigos permanecem intactos; esta revisão não cria, altera ou exclui
  lançamentos financeiros. A classificação histórica demanda análise individual.

**Última revisão da regra:** 10/11/2026.

---

## 📋 **Categorias e orientações operacionais**

### **1. OFERTAS ALÇADAS** 🙏
- **Definição:** Ofertas coletadas no ofertório durante os cultos
- **Categoria:** `OFERTA`
- **Descrição:** `Oferta`
- **Exemplos:**
  - Oferta do culto de domingo
  - Oferta do culto de quarta-feira
  - Oferta de células e grupos

### **2. OUTRAS OFERTAS** 💝
- **Definição:** Ofertas vindas de fora, doações, projetos para arrecadações, investimentos no templo
- **Categoria:** `OFERTA`
- **Descrição:** `Outras Ofertas`
- **Exemplos:**
  - Doações de membros específicas
  - Campanhas para reforma
  - Projetos especiais
  - Investimentos em equipamentos
  - Ofertas externas à igreja

### **3. OFERTAS OMN** 🌐
- **Definição:** Ofertas missionárias recebidas pela tesouraria e destinadas à Convenção.
- **Categoria:** `OFERTA OMN`
- **Descrição:** Identificar o recebimento em Dinheiro ou Pix.
- **Características:**
  - Entra no caixa da igreja local na data do recebimento.
  - Aparece separadamente como OMN nos relatórios e no Livro Caixa.
  - É posteriormente paga à Convenção por boleto, com saída financeira efetiva.
  - Não integra a base dos 30% administrativos da Sede.

---

## 🔧 **Implementação Técnica (registro histórico de 2025)**

**Atenção:** o pseudocódigo abaixo é documentação histórica, **não é a regra vigente**.
Ele somava OMN com ofertas alçadas, hipótese retificada em 10/11/2026.
Na implementação vigente, OMN possui subtotal separado e não compõe os 30%.
Os cálculos atuais devem ser conferidos em `app/financeiro/financeiro_routes.py` e
`app/utils/livro_caixa_simplificado.py`.

### **Código de Classificação histórico (substituído):**
```python
if 'omn' in categoria:
    # OFERTA OMN - direcionada à convenção
    totais['ofertas_alcadas'] += valor
elif categoria == 'oferta':
    # OFERTA regular - verificar descrição
    descricao = lancamento.descricao.lower() if lancamento.descricao else ''
    if 'oferta' in descricao and 'outras' not in descricao:
        # Ofertas do ofertório durante cultos
        totais['ofertas_alcadas'] += valor
    else:
        # Ofertas externas, doações, projetos
        totais['outras_ofertas'] += valor
```

### **Funções mencionadas no registro de 2025:**
- ✅ `relatorio_sede()` - Relatório principal
- ✅ `relatorio_sede_preview()` - Visualização
- ✅ `relatorio_sede_pdf()` - Geração de PDF

---

## 📊 **Resultado nos Relatórios**

### **Relatório Sede:**
- **Ofertas Alçadas:** Ofertas do ofertório dos cultos.
- **OMN:** Entrada missionária separada, sem compor os 30% da Sede.
- **Outras Ofertas:** Soma de ofertas externas e outras categorias

### **Fluxo de Caixa:**
- **Ofertas Alçadas:** Ofertas do ofertório efetivamente recebidas.
- **OMN:** Valores efetivamente recebidos em dinheiro ou Pix entram no saldo do caixa.
- **Outras Ofertas:** Ofertas externas que entraram no caixa

---

## 🎯 **Orientações para Lançamento**

### **Para Ofertas de Culto:**
1. Categoria: `OFERTA`
2. Descrição: `Oferta`
3. Conta: `Caixa` ou `Banco`

### **Para Ofertas Externas:**
1. Categoria: `OFERTA`
2. Descrição: `Outras Ofertas`
3. Conta: `Caixa` ou `Banco`

### **Para Ofertas OMN:**
1. Tipo: `Entrada`, na data real do recebimento.
2. Categoria: `OFERTA OMN`.
3. Descrição: Identificar a oferta recebida (ex.: "Oferta OMN - Convenção").
4. Conta: `Dinheiro`, `Pix` ou `Banco`, conforme o recebimento efetivo.
5. Pagamento posterior: registrar `Saída` ao quitar o boleto da Convenção,
   com documento/comprovante e sem duplicar a conciliação.

---

## ✅ **Migração Realizada**

- **Data:** 11/10/2025
- **Registros Atualizados:** 38 ofertas padronizadas
- **Script Utilizado:** `padronizar_ofertas.py`
- **Status:** Concluída com sucesso

---

## 🚨 **Importante**

Esta padronização garante:
- **Relatórios consistentes** entre sede e local
- **Separação clara** entre tipos de ofertas
- **Comunicação precisa** com a convenção
- **Controle financeiro** adequado

**Padronização histórica:** 11 de outubro de 2025.  **Última revisão da regra:** 10/11/2026.