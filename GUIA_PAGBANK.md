# 🏦 Guia de Importação - PagBank

## 📋 Como Exportar Extrato do PagBank

### 1. **Acessar o App PagBank**
- Abra o aplicativo PagBank no seu celular
- Faça login na sua conta

### 2. **Navegar para Extratos**
- Vá em "Conta" ou "Extrato"
- Selecione o período desejado
- Toque em "Exportar" ou "Compartilhar"

### 3. **Escolher Formato**
- Selecione formato **CSV** ou **Excel**
- Envie por email ou salve no dispositivo

## 📊 Formatos Suportados do PagBank

### Colunas Esperadas:
- **Data** (ou Data_Transacao, dt_transacao)
- **Descrição** (ou Histórico, description)
- **Valor** (ou Vlr_Transacao, amount)
- **Saldo** (ou Saldo_Final, balance)

### Exemplo de Formato:
```csv
Data,Descrição,Valor,Saldo
01/11/2025,PIX RECEBIDO - João Silva,+150.00,1150.00
01/11/2025,PAGAMENTO BOLETO - Luz,−85.50,1064.50
02/11/2025,TED RECEBIDA - Cliente ABC,+500.00,1564.50
```

## ⚙️ Como Importar no OBPC

### 1. **Acessar Importação**
- Entre no sistema OBPC
- Vá em **Financeiro** → **Importar Extrato**

### 2. **Selecionar PagBank**
- Na seção "Selecionar Banco"
- Escolha **PagBank**
- O sistema aplicará o mapeamento específico

### 3. **Fazer Upload**
- Arraste o arquivo ou clique para selecionar
- Formatos aceitos: CSV, XLS, XLSX
- Aguarde a validação

### 4. **Confirmar Importação**
- Revise os dados na prévia
- Confirme a importação
- Aguarde o processamento

## 🔧 Características do Mapeamento PagBank

### Detecção Automática:
- **Valores positivos** → Entradas (receitas)
- **Valores negativos** → Saídas (despesas)
- **Encoding** → UTF-8 ou Latin-1 automático
- **Separadores** → Vírgula ou ponto-e-vírgula

### Campos Mapeados:
```python
# O sistema procura por estas variações:
data: ['data', 'dt_transacao', 'data_transacao', 'date']
descricao: ['descrição', 'descricao', 'histórico', 'historico']
valor: ['valor', 'vlr_transacao', 'valor_transacao', 'amount']
saldo: ['saldo', 'saldo_final', 'balance']
```

## ✅ Dicas para Melhor Resultado

### Preparação do Arquivo:
- ✅ Remova linhas de cabeçalho desnecessárias
- ✅ Certifique-se que as datas estão no formato DD/MM/AAAA
- ✅ Valores devem estar em formato numérico (150.00)
- ✅ Use encoding UTF-8 se possível

### Evite Problemas:
- ❌ Não inclua células mescladas
- ❌ Não deixe linhas vazias entre os dados
- ❌ Não altere os nomes das colunas originais
- ❌ Não inclua caracteres especiais extras

## 🚀 Após a Importação

### Verificações Automáticas:
- **Duplicatas** serão detectadas automaticamente
- **Conciliação** será executada se houver lançamentos manuais
- **Relatório** será gerado com estatísticas

### Próximos Passos:
1. Verifique o **Dashboard de Conciliação**
2. Revise lançamentos **não conciliados**
3. Execute **conciliação manual** se necessário
4. Gere **relatórios** para análise

## 📞 Problemas Comuns

### "Arquivo não reconhecido"
**Solução:** Verifique se as colunas têm nomes similares aos esperados

### "Dados não processados"
**Solução:** Certifique-se que valores estão em formato numérico

### "Encoding inválido"
**Solução:** Salve o arquivo como CSV UTF-8

### "Duplicatas detectadas"
**Solução:** Normal - o sistema evita importações duplicadas

## 📈 Exemplo Prático

### Arquivo PagBank Original:
```csv
Data,Descrição,Valor,Saldo
01/11/2025,PIX - Dízimo João,150.00,1150.00
01/11/2025,Boleto - Conta de Luz,-85.50,1064.50
```

### Resultado no OBPC:
- **Lançamento 1:** Entrada - R$ 150,00 - PIX Dízimo
- **Lançamento 2:** Saída - R$ 85,50 - Conta de Luz
- **Origem:** Importado (PagBank)
- **Status:** Aguardando conciliação

---

**💡 Dica:** O PagBank é totalmente compatível com o sistema OBPC. O mapeamento inteligente detecta automaticamente o formato e processa os dados corretamente!