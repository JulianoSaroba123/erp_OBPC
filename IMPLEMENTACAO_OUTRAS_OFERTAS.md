# IMPLEMENTAÇÃO DA CATEGORIA "OUTRAS OFERTAS"

## 🎯 **Objetivo**
Adicionar uma nova categoria "OUTRAS OFERTAS" no módulo financeiro com lógica especial que exclui esses valores do cálculo dos 30% do valor administrativo para a sede.

## ✅ **O que foi implementado**

### 1. **Nova Categoria no Formulário**
- Adicionada categoria "OUTRAS OFERTAS" no formulário de cadastro de lançamentos
- Localização: `app/financeiro/templates/financeiro/cadastro_lancamento.html`

### 2. **Lógica Financeira Atualizada**
Arquivos modificados:
- `app/financeiro/financeiro_routes.py` (3 rotas atualizadas)
- `app/utils/gerar_pdf_reportlab.py` (classe RelatorioFinanceiro)

### 3. **Scripts de Atualização**
- `adicionar_categoria_outras_ofertas.py` - Script para reclassificar lançamentos existentes
- `atualizar_categorias.py` - Incluída nova categoria no mapeamento

## 📋 **Como Funciona**

### **Antes da Mudança:**
```
Valor Administrativo = Total Geral × 30%
```

### **Depois da Mudança:**
```
Valor para Cálculo = Total Geral - OUTRAS OFERTAS
Valor Administrativo = Valor para Cálculo × 30%
```

## 🔧 **Rotas Atualizadas**

### 1. `/financeiro/relatorio-sede`
- Cálculo dos 30% agora exclui "OUTRAS OFERTAS"
- Tratamento específico para a nova categoria

### 2. `/financeiro/relatorio-sede/preview` 
- Preview HTML com a nova lógica implementada
- Campo `trinta_porcento_conselho` calculado corretamente

### 3. `/financeiro/relatorio-sede/pdf`
- PDF gerado com cálculos corretos
- Valor do conselho exclui "OUTRAS OFERTAS"

## 📊 **Relatórios Atualizados**

### **Classe RelatorioFinanceiro**
- `_calcular_totais_sede()` - Lógica de cálculo atualizada
- `_criar_secao_arrecadacao_sede()` - Informações explicativas atualizadas
- `_criar_secao_envios_sede()` - Texto do conselho atualizado

### **Informações nos PDFs**
- Texto explicativo: "Do total arrecadado (excluindo OUTRAS OFERTAS), 30% vai para o Conselho"
- Linha do conselho: "Conselho (30% - excl. Outras Ofertas)"

## 🎯 **Categorização das Ofertas**

### **OFERTA** (Alçadas)
- Ofertas do ofertório durante cultos
- **ENTRA** no cálculo dos 30%

### **OFERTA OMN**
- Ofertas direcionadas à convenção
- **ENTRA** no cálculo dos 30%

### **OUTRAS OFERTAS** ⭐ (Nova)
- Doações especiais
- Projetos específicos  
- Vendas e eventos
- **NÃO ENTRA** no cálculo dos 30%

## 📈 **Exemplo Prático**

### **Cenário:**
- Dízimos: R$ 1.000,00
- Ofertas: R$ 500,00  
- Outras Ofertas: R$ 300,00
- **Total Geral:** R$ 1.800,00

### **Cálculo do Valor Administrativo:**
```
Valor para cálculo = R$ 1.800,00 - R$ 300,00 = R$ 1.500,00
Valor administrativo = R$ 1.500,00 × 30% = R$ 450,00
```

### **Antes era:**
```
Valor administrativo = R$ 1.800,00 × 30% = R$ 540,00
```

**Economia de R$ 90,00 para a igreja local!**

## 🚀 **Como Usar**

### **Para Novos Lançamentos:**
1. No formulário de lançamento, selecionar "OUTRAS OFERTAS"
2. Adicionar descrição específica (ex: "Doação para reforma", "Projeto X")
3. O sistema automaticamente excluirá do cálculo administrativo

### **Para Lançamentos Existentes:**
1. Executar o script: `python adicionar_categoria_outras_ofertas.py`
2. O script identificará automaticamente lançamentos que podem ser reclassificados
3. Baseado em palavras-chave: doação, projeto, ajuda, evento, etc.

## 📝 **Palavras-chave para Auto-classificação**
O script identifica automaticamente como "OUTRAS OFERTAS":
- doação, doacao
- projeto 
- ajuda
- contribuição especial
- evento especial
- venda, bazar, festa
- campanha, externa

## ✨ **Benefícios**

1. **Maior flexibilidade** na categorização de ofertas
2. **Economia** no valor enviado para sede
3. **Transparência** nos relatórios
4. **Conformidade** com regras específicas da igreja
5. **Automatização** na classificação de ofertas especiais

## 🔍 **Verificação**

Para verificar se está funcionando:
1. Criar um lançamento com categoria "OUTRAS OFERTAS"
2. Gerar o relatório da sede
3. Verificar se o valor administrativo não inclui essa oferta
4. Conferir as informações explicativas no PDF

---

**✅ IMPLEMENTAÇÃO CONCLUÍDA - SISTEMA PRONTO PARA USO!**