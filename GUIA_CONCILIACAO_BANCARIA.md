# 📚 GUIA COMPLETO DE CONCILIAÇÃO BANCÁRIA - SISTEMA OBPC

## 🎯 **O QUE É CONCILIAÇÃO BANCÁRIA?**

A conciliação bancária é o processo de **comparar e identificar** quais lançamentos manuais do sistema correspondem aos lançamentos do extrato bancário, evitando duplicações e garantindo controle financeiro preciso.

---

## 💡 **POR QUE FAZER CONCILIAÇÃO?**

✅ **Evitar duplicatas**: Não registrar a mesma operação duas vezes  
✅ **Controle preciso**: Saber exatamente o que entrou e saiu  
✅ **Auditoria**: Facilitar prestação de contas e relatórios  
✅ **Confiabilidade**: Garantir que os dados estão corretos  

---

## 🚀 **PASSO A PASSO PRÁTICO**

### **PASSO 1: ACESSAR O SISTEMA**
1. Abra o navegador em: `http://127.0.0.1:5000`
2. Faça login no sistema OBPC
3. Vá para: **Financeiro → Conciliação Bancária**

### **PASSO 2: ENTENDER A TELA**
Na tela de conciliação você verá:
- 🔍 **Botão "Gerar Sugestões"**: Busca correspondências automaticamente
- 📋 **Lista de Pares**: Mostra as correspondências encontradas  
- ✅ **Botões de Ação**: Aceitar, Exportar, Desfazer
- 📊 **Estatísticas**: Quantos foram conciliados, pendentes, etc.

### **PASSO 3: GERAR SUGESTÕES**
1. **Clique em "Gerar Sugestões"**
2. O sistema analisará todos os lançamentos procurando por:
   - 💰 **Valores iguais ou próximos** (considera taxas bancárias)
   - 📅 **Datas iguais ou próximas** (compara ±3 dias)
   - 📝 **Descrições similares** (busca palavras-chave em comum)
   - ↔️ **Tipos compatíveis** (entrada com entrada, saída com saída)

---

## 📋 **CENÁRIOS DE EXEMPLO (criamos dados para você testar)**

### **1️⃣ CORRESPONDÊNCIA EXATA** ⭐⭐⭐
**Situação**: Lançamento manual e bancário idênticos
- 📝 Manual: "Dízimo - João Silva" = R$ 250,00 (01/11/24)
- 🏦 Extrato: "PIX João Silva - dizimo" = R$ 250,00 (01/11/24)
- 🎯 **Score**: 95% (quase perfeito)
- ✅ **Ação**: Aceitar sem hesitação

### **2️⃣ VALORES PRÓXIMOS** ⭐⭐
**Situação**: Valor manual maior que bancário (taxa descontada)
- 📝 Manual: "Oferta Domingo - Maria Santos" = R$ 100,00
- 🏦 Extrato: "TED Maria Santos oferta" = R$ 98,50
- 🎯 **Score**: 85% (diferença de R$ 1,50 por taxa)
- ✅ **Ação**: Aceitar (normal ter diferença por taxa)

### **3️⃣ DATAS DIFERENTES** ⭐⭐
**Situação**: Lançado em uma data, compensado em outra
- 📝 Manual: "Contribuição Pedro Costa" = R$ 500,00 (30/10/24)
- 🏦 Extrato: "DEPOSITO PEDRO COSTA" = R$ 500,00 (03/11/24)  
- 🎯 **Score**: 80% (4 dias de diferença)
- ✅ **Ação**: Aceitar (normal ter diferença de data)

### **4️⃣ SAÍDAS/GASTOS** ⭐⭐⭐
**Situação**: Pagamentos que devem ser conciliados
- 📝 Manual: "Pagamento energia elétrica" = R$ 180,50
- 🏦 Extrato: "CEMIG ENERGIA ELETRICA" = R$ 180,50
- 🎯 **Score**: 90% (descrições diferentes mas mesmo valor)
- ✅ **Ação**: Aceitar

### **5️⃣ SEM CORRESPONDÊNCIA** ❌
**Situação**: Lançamentos órfãos (sem par)
- 📝 Manual órfão: "Doação anônima" = R$ 75,00
- 🏦 Extrato órfão: "TARIFA BANCARIA" = R$ 12,90
- 🎯 **Score**: 0% (sem correspondência)
- 🔍 **Ação**: Investigar ou deixar separado

---

## ⚡ **COMO ANALISAR OS RESULTADOS**

### **✅ ACEITAR UM PAR**
- Marque a checkbox do par que está correto
- Clique **"Aceitar Selecionados"**
- O sistema marcará ambos como conciliados

### **📁 EXPORTAR DADOS**  
- Selecione os pares que quer analisar
- Clique **"Exportar Selecionados (CSV)"**
- Baixe o arquivo para análise detalhada

### **↩️ DESFAZER CONCILIAÇÃO**
- No histórico, clique **"Desfazer"** ao lado do registro
- Os lançamentos voltam a ficar disponíveis para conciliação

---

## 🎯 **SCORES DE SIMILARIDADE**

| Score | Qualidade | O que significa | Ação recomendada |
|-------|-----------|-----------------|-------------------|
| 90-100% | ⭐⭐⭐ Excelente | Correspondência quase perfeita | ✅ Aceitar |
| 80-89% | ⭐⭐ Boa | Boa correspondência com pequenas diferenças | ✅ Revisar e aceitar |
| 70-79% | ⭐ Regular | Correspondência duvidosa | 🔍 Analisar com cuidado |
| <70% | ❌ Ruim | Provavelmente não correspondem | ❌ Não aceitar |

---

## 🛠️ **REGRAS DO ALGORITMO**

O sistema usa estas regras para encontrar correspondências:

### **1. VALOR EXATO** (+40 pontos)
- Valores idênticos ganham pontuação máxima

### **2. VALOR PRÓXIMO** (+20-35 pontos)  
- Diferenças até 5% são consideradas (taxas bancárias)
- Quanto menor a diferença, maior a pontuação

### **3. DATA EXATA** (+30 pontos)
- Mesma data ganha pontuação máxima

### **4. DATA PRÓXIMA** (+15-25 pontos)
- Diferenças de ±1 a ±7 dias são consideradas
- Quanto menor a diferença, maior a pontuação  

### **5. DESCRIÇÃO SIMILAR** (+10-25 pontos)
- Busca palavras em comum nas descrições
- Remove acentos, conectores e normaliza o texto
- Nomes de pessoas ganham pontuação extra

### **6. MESMO TIPO** (+5 pontos)  
- Entrada com entrada, saída com saída

---

## 🔍 **DICAS IMPORTANTES**

### **✅ FAÇA**
- ✅ Sempre revise pares com score baixo (<80%)
- ✅ Aceite primeiro os scores altos (>90%)  
- ✅ Exporte dados para análise detalhada quando houver dúvidas
- ✅ Use o histórico para desfazer se necessário

### **❌ NÃO FAÇA**
- ❌ Não aceite pares duvidosos sem analisar
- ❌ Não ignore lançamentos órfãos - investigue a origem
- ❌ Não aceite diferenças grandes de valor (>5%) sem justificativa
- ❌ Não esqueça de verificar se os tipos estão corretos

---

## 📊 **RELATÓRIOS DISPONÍVEIS**

1. **Histórico de Conciliações**: Lista todas as conciliações feitas
2. **Lançamentos Órfãos**: Mostra itens sem correspondência  
3. **Export CSV**: Dados detalhados para análise externa
4. **Dashboard**: Estatísticas gerais do processo

---

## 🚨 **SOLUÇÃO DE PROBLEMAS**

### **Problema**: Não encontra correspondências óbvias
**Solução**: Verifique se as datas e valores estão corretos nos lançamentos

### **Problema**: Muitos falsos positivos  
**Solução**: Aumente os critérios de threshold nas configurações

### **Problema**: Score baixo para correspondência correta
**Solução**: Padronize as descrições dos lançamentos manuais

---

## 🎉 **PRONTO PARA COMEÇAR!**

Agora você já sabe como fazer conciliação bancária no OBPC! 

**Próximos passos**:
1. Acesse: http://127.0.0.1:5000/financeiro/conciliacao
2. Clique "Gerar Sugestões"  
3. Analise os resultados usando este guia
4. Aceite as correspondências corretas
5. Investigue os lançamentos órfãos

**Dados de exemplo já criados** para você praticar! 🎯