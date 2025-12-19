# PADRONIZAÇÃO DAS OFERTAS - SISTEMA OBPC

## 📋 **Nova Lógica Implementada**

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
- **Definição:** Ofertas direcionadas à convenção (não passa pelo caixa local, só para comunicação)
- **Categoria:** `OFERTA OMN`
- **Descrição:** Qualquer descrição
- **Características:**
  - Não entra no caixa da igreja local
  - Aparece no relatório sede para comunicação
  - Enviada diretamente para a convenção

---

## 🔧 **Implementação Técnica**

### **Código de Classificação:**
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

### **Aplicado nas Funções:**
- ✅ `relatorio_sede()` - Relatório principal
- ✅ `relatorio_sede_preview()` - Visualização
- ✅ `relatorio_sede_pdf()` - Geração de PDF

---

## 📊 **Resultado nos Relatórios**

### **Relatório Sede:**
- **Ofertas Alçadas:** Soma de ofertas do ofertório + ofertas OMN
- **Outras Ofertas:** Soma de ofertas externas e outras categorias

### **Fluxo de Caixa:**
- **Ofertas Alçadas:** Apenas ofertas do ofertório (OMN não entra no caixa)
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
1. Categoria: `OFERTA OMN`
2. Descrição: Livre (ex: "Oferta OMN - Convenção")
3. Conta: Não aplicável (não entra no caixa)

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

**Última Atualização:** 11 de outubro de 2025