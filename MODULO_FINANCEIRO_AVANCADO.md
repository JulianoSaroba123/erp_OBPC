# Módulo Financeiro Aprimorado - Conciliação Bancária

## 🎯 Visão Geral

O módulo financeiro do OBPC foi aprimorado com funcionalidades avançadas de conciliação bancária, incluindo importação automática de extratos, conciliação inteligente e dashboards analíticos.

## 🚀 Novas Funcionalidades

### 1. Dashboard de Conciliação Bancária
**Rota:** `/financeiro/conciliacao/dashboard`

**Características:**
- Visão geral de métricas de conciliação
- Indicadores de performance em tempo real
- Lançamentos pendentes organizados por origem
- Histórico de conciliações recentes
- Detecção automática de discrepâncias

**Métricas Disponíveis:**
- Total de lançamentos no sistema
- Percentual de conciliação
- Lançamentos pendentes
- Duplicatas detectadas
- Top regras de conciliação utilizadas

### 2. Importação Inteligente de Extratos
**Rota:** `/financeiro/conciliacao/importar-extrato`

**Formatos Suportados:**
- CSV (separadores `;` ou `,`, encoding UTF-8/Latin-1)
- Excel (.xlsx, .xls)

**Bancos com Mapeamento Específico:**
- Bradesco
- Itaú
- Santander
- Banco do Brasil
- Caixa Econômica Federal
- Nubank
- PagBank
- Genérico (mapeamento automático)

**Recursos:**
- Interface drag & drop intuitiva
- Validação de formato em tempo real
- Preview dos dados antes da importação
- Detecção automática de duplicatas
- Log detalhado do processo

### 3. Conciliação Automática Inteligente
**Rota:** `/financeiro/conciliacao/executar-automatica`

**Regras de Conciliação:**
1. **Exata:** Mesmo valor, data e tipo (Score: 100%)
2. **Valor e Data Similar:** Valor igual, data ±3 dias (Score: 95-80%)
3. **Valor e Descrição Similar:** Valor igual, descrição similar (Score: 85-95%)
4. **Valor e Data Próxima:** Valor ±5%, data ±7 dias (Score: 80-70%)
5. **Descrição Fuzzy:** Descrição muito similar (Score: 75-90%)

**Algoritmos Utilizados:**
- Fuzzy string matching (difflib)
- Análise de palavras-chave
- Cálculo de similaridade ponderada
- Scores mínimos configuráveis

### 4. Conciliação Manual Assistida
**Rota:** `/financeiro/conciliacao/manual`

**Recursos:**
- Interface lado a lado para comparação
- Sugestões automáticas por lançamento
- Filtros avançados (data, valor, tipo)
- Validação de compatibilidade
- Atalhos de teclado (ESC, Ctrl+Enter)

### 5. Controle de Duplicatas
**Sistema Automático:**
- Hash SHA256 baseado em data + valor + descrição
- Detecção durante importação
- Relatório de duplicatas pendentes
- Prevenção de conciliação duplicada

### 6. Histórico e Auditoria
**Rota:** `/financeiro/conciliacao/historico`

**Dados Registrados:**
- Data e usuário da conciliação
- Método utilizado (manual/automático)
- Regras aplicadas
- Tempo de execução
- Score de similaridade
- Possibilidade de desfazer

### 7. Relatórios de Discrepâncias
**Rota:** `/financeiro/conciliacao/relatorio-discrepancias`

**Tipos de Discrepâncias:**
- Valores anormalmente altos
- Lançamentos duplicados não conciliados
- Diferenças significativas de valor
- Padrões suspeitos

### 8. Exportação de Dados
**Rota:** `/financeiro/conciliacao/exportar-dados`

**Formatos:**
- CSV com dados completos de conciliação
- Inclui scores, regras aplicadas e timestamps
- Dados para análise externa

## 🗂️ Estrutura de Arquivos

```
app/financeiro/
├── financeiro_model.py          # Modelos aprimorados
├── routes_conciliacao.py        # Novas rotas de conciliação
├── utils/
│   └── conciliacao_avancada.py  # Utilitários de conciliação
└── templates/financeiro/
    ├── dashboard_conciliacao.html    # Dashboard principal
    ├── importar_extrato.html         # Interface de importação
    ├── conciliacao_manual.html       # Conciliação manual
    ├── historico_conciliacao.html    # Histórico de operações
    └── relatorio_discrepancias.html  # Relatório de problemas
```

## 🗄️ Novos Modelos de Dados

### Tabela: `lancamentos` (campos adicionados)
```sql
hash_duplicata VARCHAR(64)      -- Hash para detecção de duplicatas
banco_origem VARCHAR(100)       -- Banco de origem (importados)
documento_ref VARCHAR(50)       -- Número documento/referência
conciliado_em DATETIME          -- Data da conciliação
conciliado_por VARCHAR(100)     -- Usuário que conciliou
par_conciliacao_id INTEGER      -- FK para tabela de pares
```

### Tabela: `conciliacao_historico`
```sql
id INTEGER PRIMARY KEY
data_conciliacao DATETIME NOT NULL
usuario VARCHAR(100) NOT NULL
total_conciliados INTEGER NOT NULL
total_pendentes INTEGER NOT NULL
tipo_conciliacao VARCHAR(20)    -- 'manual', 'automatica', 'mista'
observacao TEXT
tempo_execucao FLOAT            -- Tempo em segundos
regras_aplicadas TEXT           -- JSON com regras aplicadas
```

### Tabela: `conciliacao_pares`
```sql
id INTEGER PRIMARY KEY
historico_id INTEGER            -- FK para histórico
lancamento_manual_id INTEGER    -- FK para lançamento manual
lancamento_importado_id INTEGER -- FK para lançamento importado
score_similaridade FLOAT       -- Score de 0-1
regra_aplicada VARCHAR(200)     -- Regra que gerou o par
metodo_conciliacao VARCHAR(50)  -- 'manual', 'automatico'
usuario VARCHAR(100)
criado_em DATETIME
ativo BOOLEAN                   -- Para permitir desfazer
```

### Tabela: `importacao_extrato`
```sql
id INTEGER PRIMARY KEY
nome_arquivo VARCHAR(255) NOT NULL
hash_arquivo VARCHAR(64) UNIQUE -- Hash para evitar reimportação
banco VARCHAR(100)
data_importacao DATETIME
usuario VARCHAR(100) NOT NULL
total_registros INTEGER
registros_processados INTEGER
registros_duplicados INTEGER
registros_erro INTEGER
status VARCHAR(20)              -- 'processando', 'concluido', 'erro'
log_detalhado TEXT
```

## 🛠️ Instalação e Configuração

### 1. Dependências Necessárias
```bash
pip install pandas numpy openpyxl xlrd
```

### 2. Atualização do Banco de Dados
Execute o script de atualização:
```bash
python atualizar_modulo_financeiro.py
```

### 3. Registro dos Blueprints
Adicione ao `app/__init__.py`:
```python
from app.financeiro.routes_conciliacao import conciliacao_bp

# Na função create_app:
app.register_blueprint(conciliacao_bp)
```

### 4. Configuração de Diretórios
O sistema criará automaticamente:
- `app/static/uploads/extratos/` - Para arquivos temporários
- `app/static/uploads/comprovantes/` - Para anexos

## 📊 APIs Disponíveis

### GET `/financeiro/conciliacao/api/sugestoes/<lancamento_id>`
Retorna sugestões de conciliação para um lançamento específico.

**Resposta:**
```json
{
  "sugestoes": [
    {
      "lancamento": {...},
      "score": 0.95,
      "regra": "valor_data_similar",
      "compatibilidade": "alta"
    }
  ],
  "total": 5
}
```

### POST `/financeiro/conciliacao/criar-par`
Cria par de conciliação manual.

**Parâmetros:**
- `manual_id`: ID do lançamento manual
- `importado_id`: ID do lançamento importado

**Resposta:**
```json
{
  "success": true,
  "message": "Par criado com sucesso",
  "par_id": 123
}
```

### POST `/financeiro/conciliacao/desfazer-par/<par_id>`
Desfaz uma conciliação específica.

## 🎨 Interface do Usuário

### Dashboard
- Cards de métricas com cores OBPC
- Gráficos de progresso em tempo real
- Tabelas responsivas com paginação
- Indicadores visuais de status

### Importação
- Interface drag & drop
- Indicador de progresso por etapas
- Validação em tempo real
- Suporte a múltiplos bancos

### Conciliação Manual
- Layout lado a lado
- Seleção visual intuitiva
- Sugestões automáticas
- Atalhos de teclado

## 🔧 Configurações Avançadas

### Scores Mínimos
```python
scores_minimos = {
    'exata': 1.0,
    'valor_data_similar': 0.95,
    'valor_descricao_similar': 0.85,
    'valor_proxima_data': 0.80,
    'descricao_fuzzy': 0.75
}
```

### Mapeamento de Bancos
Cada banco pode ter seu próprio mapeamento de colunas:

**Bradesco:**
```python
def _mapear_bradesco(self, df):
    mapeamento = {
        'data': 'Data',
        'descricao': 'Histórico',
        'valor': 'Valor',
        'documento': 'Número'
    }
```

**PagBank:**
```python
def _mapear_pagbank(self, df):
    mapeamento_alternativo = {
        'data': ['data', 'dt_transacao', 'data_transacao'],
        'descricao': ['descrição', 'histórico', 'description'],
        'valor': ['valor', 'vlr_transacao', 'amount'],
        'saldo': ['saldo', 'saldo_final', 'balance']
    }
```

## 📈 Métricas e Monitoramento

### KPIs Disponíveis
- Taxa de conciliação automática
- Tempo médio de processamento
- Eficácia das regras de conciliação
- Volume de importações por banco
- Detecção de duplicatas

### Alertas Automáticos
- Discrepâncias de valor significativas
- Lançamentos não conciliados há muito tempo
- Falhas na importação
- Duplicatas detectadas

## 🚨 Solução de Problemas

### Problemas Comuns

**1. Arquivo não reconhecido**
- Verificar formato (CSV/Excel)
- Confirmar encoding (UTF-8)
- Validar estrutura de colunas

**2. Conciliação não funciona**
- Verificar se há lançamentos pendentes
- Ajustar scores mínimos se necessário
- Revisar formato de datas

**3. Erro de importação**
- Verificar permissões de diretório
- Confirmar instalação de dependências
- Validar estrutura do arquivo

### Logs e Debug
- Logs detalhados em `ImportacaoExtrato.log_detalhado`
- Histórico completo em `ConciliacaoHistorico`
- Scores e regras aplicadas registrados

## 🔄 Atualizações Futuras

### Roadmap
- [ ] Integração com APIs bancárias
- [ ] Machine Learning para melhorar conciliação
- [ ] Relatórios gerenciais avançados
- [ ] Notificações por email
- [ ] Conciliação de cartões de crédito
- [ ] Previsão de fluxo de caixa

### Como Contribuir
1. Fork do projeto
2. Criar branch para feature
3. Implementar com testes
4. Documentar mudanças
5. Pull request

## 📞 Suporte

Para dúvidas ou problemas:
- Verifique este documento primeiro
- Consulte os logs do sistema
- Execute script de diagnóstico
- Contate a equipe de desenvolvimento

---

**Versão:** 2.0
**Data:** Janeiro 2025
**Desenvolvido para:** OBPC - Obra Bíblica de Pregação à Cristandade