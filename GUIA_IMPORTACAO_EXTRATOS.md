# 📋 GUIA DE ORIENTAÇÃO PARA IMPORTAÇÃO DE EXTRATOS

## 🎯 Como Preparar Arquivos para Importação

Este guia mostra **exatamente** como suas colunas devem estar organizadas para cada tipo de extrato.

---

## 🏦 PAGBANK (.xlsx ou .csv)

### ✅ Colunas Obrigatórias:
- **DATA** - Data da transação (formato: DD/MM/AAAA)
- **TIPO** - Tipo da operação (ex: "Pix recebido", "Rendimento da conta")
- **DESCRICAO** - Descrição da transação
- **VALOR** - Valor da transação (número decimal)

### 📄 Exemplo de Arquivo PagBank:
```
CODIGO DA TRANSACAO | DATA        | TIPO               | DESCRICAO                    | VALOR
404ee56a-32ee...    | 01/10/2025  | Rendimento da conta| Rendimento sobre dinheiro    | 0,03
18ff075b-0eab...    | 02/10/2025  | Pix recebido       | Juliano Saroba Pereira       | 10
```

### 🔧 Colunas Opcionais:
- **CODIGO DA TRANSACAO** - ID único da transação

---

## 🏦 BANCO DO BRASIL (.xlsx)

### ✅ Colunas Obrigatórias:
- **Data** ou **Data Operação** - Data da movimentação
- **Descrição** ou **Histórico** - Descrição da operação
- **Valor** ou **Valor Movimentação** - Valor da transação
- **Natureza** ou **Tipo** - Tipo (Crédito/Débito)

---

## 🏦 ITAÚ (.xlsx)

### ✅ Colunas Obrigatórias:
- **Data** ou **Data Operação**
- **Descrição** ou **Histórico**
- **Valor** ou **Amount**
- **Natureza** ou **Tipo**

---

## 🏦 BRADESCO (.xlsx)

### ✅ Colunas Obrigatórias:
- **Data** ou **Data Operação**
- **Descrição** ou **Histórico**
- **Valor** ou **Amount**
- **Tipo** ou **Natureza**

---

## 📄 CSV GENÉRICO (.csv)

### ✅ Formato Padrão:
```
data,descricao,valor,tipo
01/11/2025,PIX RECEBIDO - JOÃO SILVA,150.50,ENTRADA
02/11/2025,PAGAMENTO BOLETO ENERGIA,89.75,SAIDA
```

### ✅ Colunas Aceitas:
- **Data**: data, date, fecha
- **Descrição**: descricao, description, memo, historico
- **Valor**: valor, value, amount, montante
- **Tipo**: tipo, type, natureza

---

## 📄 ARQUIVO OFX (.ofx)

### ✅ Formato Padrão OFX:
O sistema detecta automaticamente as tags OFX padrão.

---

## 🚨 REGRAS IMPORTANTES

### 📋 Formato de Dados:

1. **DATAS**:
   - ✅ DD/MM/AAAA (01/11/2025)
   - ✅ DD-MM-AAAA (01-11-2025)
   - ✅ AAAA-MM-DD (2025-11-01)

2. **VALORES**:
   - ✅ 150.50 (ponto como decimal)
   - ✅ 150,50 (vírgula como decimal)
   - ✅ R$ 150,50 (com símbolo)
   - ❌ 1.500,50 (milhares com ponto E decimal com vírgula)

3. **TIPOS**:
   - ✅ ENTRADA/SAIDA
   - ✅ CREDITO/DEBITO
   - ✅ Positivo/Negativo (detectado automaticamente)

### 🔍 Sistema de Detecção:

O sistema procura colunas que contenham estas palavras (não precisa ser exato):
- **Data**: data, date, operacao, movimentacao
- **Descrição**: descricao, description, historico, memo
- **Valor**: valor, value, amount, montante, quantia
- **Tipo**: tipo, type, natureza, credito, debito

---

## 🛠️ COMO CORRIGIR PROBLEMAS

### ❌ "Nenhum registro válido encontrado"

**Possíveis causas:**
1. Nomes de colunas não reconhecidos
2. Formato de data inválido
3. Valores não numéricos
4. Arquivo vazio ou corrompido

**Soluções:**
1. Renomeie as colunas para os nomes padrão
2. Verifique o formato das datas
3. Remova caracteres especiais dos valores
4. Verifique se o arquivo não está corrompido

### ❌ "Arquivo sem colunas essenciais"

**Solução:**
Certifique-se de que seu arquivo tem pelo menos:
- 1 coluna de DATA
- 1 coluna de DESCRIÇÃO  
- 1 coluna de VALOR

---

## 📋 CHECKLIST ANTES DA IMPORTAÇÃO

- [ ] Arquivo está no formato correto (.xlsx, .csv, .txt, .ofx)
- [ ] Colunas têm nomes reconhecíveis
- [ ] Datas estão no formato DD/MM/AAAA
- [ ] Valores são numéricos (sem caracteres especiais)
- [ ] Arquivo não está vazio
- [ ] Selecionou o tipo correto no sistema

---

## 🎯 EXEMPLO PERFEITO - PAGBANK

Para garantir 100% de sucesso com PagBank, organize assim:

```excel
DATA        | TIPO               | DESCRICAO                           | VALOR
01/10/2025  | Pix recebido       | Juliano Saroba Pereira             | 10
02/10/2025  | Rendimento da conta| Rendimento sobre dinheiro em conta | 0,03
03/10/2025  | Pix recebido       | Anizio Domingos Nunes Viana        | 227,7
```

**Dica**: Se suas colunas estão diferentes, renomeie para estes nomes exatos!

---

## 🆘 SUPORTE

Se ainda tiver problemas:
1. Verifique se as colunas seguem este guia
2. Teste com um arquivo pequeno primeiro
3. Use o formato CSV genérico se outros não funcionarem

**Lembre-se**: O sistema é inteligente, mas precisa que as colunas tenham nomes reconhecíveis! 🎯