# Homologação do Módulo Financeiro OBPC

## Identificação

**Etapa:** D.2.3D.44B
**Status:** HOMOLOGADO
**Ambiente:** PostgreSQL de Produção
**Data da homologação:** 2026-08-20

## Escopo validado

- Dashboard Financeiro
- Movimentações
- Saldo mensal
- Saldo anterior
- Saldo acumulado
- Repasse à Sede
- Obrigações Financeiras
- Pagamentos de Obrigações
- Despesas Fixas
- Conciliação
- Recibos
- Projetos/Destinações
- Relatório Gerencial
- Relatório Sede
- Relatório Auditoria
- Histórico sem movimentação financeira

## Evidências numéricas

A homologação D23D44B foi executada contra o PostgreSQL de produção. As fontes diretas, o Dashboard e os relatórios apresentaram valores coerentes centavo a centavo nas competências de 01/2026 a 07/2026.

### Tipos de lançamento

- `Entrada`: 341 registros
- `Saída`: 205 registros
- Divergência de tipo Entrada/Saída em produção: **NÃO**

### Obrigações

| Competência | Valor devido | Total pago | Saldo | Status | Data quitação | Coerência |
| --- | ---: | ---: | ---: | --- | --- | --- |
| 01/2026 | R$ 1.240,95 | R$ 1.240,95 | R$ 0,00 | PAGO | 2026-08-15 | SIM |
| 02/2026 | R$ 1.361,01 | R$ 1.361,01 | R$ 0,00 | PAGO | 2026-02-01 | SIM |
| 03/2026 | R$ 1.829,11 | R$ 1.829,11 | R$ 0,00 | PAGO | 2026-07-04 | SIM |
| 04/2026 | R$ 1.865,34 | R$ 1.865,34 | R$ 0,00 | PAGO | 2026-08-15 | SIM |
| 05/2026 | R$ 1.145,59 | R$ 1.145,59 | R$ 0,00 | PAGO | 2026-08-15 | SIM |
| 06/2026 | R$ 2.403,31 | R$ 0,00 | R$ 2.403,31 | PENDENTE | - | SIM |
| 07/2026 | R$ 1.122,56 | R$ 0,00 | R$ 1.122,56 | PENDENTE | - | SIM |

### Snapshot financeiro

```text
TOTAL_LANCAMENTOS: 546
SALDO_LANCAMENTOS: 642.24
TOTAL_OBRIGACOES: 7
TOTAL_PAGAMENTOS: 8
TOTAL_ITENS: 8
TOTAL_ENVIOS: 8
```

## Consistência dos relatórios

Os relatórios **Gerencial**, **Sede** e **Auditoria** apresentaram os mesmos totais principais em 06/2026 e 07/2026.

### 06/2026

```text
total_entradas = 8092.08
total_saidas = 4663.91
saldo_anterior = -200.11
saldo_mes = 3428.17
saldo_acumulado = 3228.06
trinta_porcento_conselho = 2403.31
despesas_fixas_conselho = 280.00
total_envio_sede = 2683.31
```

### 07/2026

```text
total_entradas = 3865.08
total_saidas = 6450.90
saldo_anterior = 3228.06
saldo_mes = -2585.82
saldo_acumulado = 642.24
trinta_porcento_conselho = 1122.56
despesas_fixas_conselho = 280.00
total_envio_sede = 1402.56
```

## Distinção conceitual importante

```text
TOTAL_ENVIO_SEDE_JULHO_POR_DATA_PAGAMENTO = 3043.60
ABATIMENTO_ADMIN_JULHO_POR_COMPETENCIA = 0.00
```

O valor enviado no mês, calculado pela `data_pagamento`, pode incluir quitações de competências anteriores. Esse valor não deve ser confundido com o abatimento da obrigação administrativa da competência corrente, que é calculado pela competência atribuída ao pagamento.

Essa diferença conceitual não constitui, por si só, uma inconsistência financeira.

## Histórico sem movimentação

```text
HISTORICOS_SEM_MOVIMENTACAO = 8
HISTORICOS_COM_LANCAMENTO_FINANCEIRO = 0
```

Os pagamentos históricos utilizados na regularização não criaram lançamentos financeiros e não movimentaram o caixa ou banco.

## Governança para Alterações Futuras no Financeiro

A partir desta homologação, qualquer alteração que afete os itens abaixo deve possuir uma etapa técnica explícita:

- `Lancamento`
- saldo
- cálculo mensal
- saldo acumulado
- Obrigações Financeiras
- Repasse à Sede
- `PagamentoObrigacao`
- `PagamentoObrigacaoItem`
- `EnvioSede`
- Despesas Fixas
- Conciliação
- Relatórios financeiros
- Dashboard financeiro

Não realizar alteração financeira relevante diretamente em produção.

## Regressões obrigatórias

As seguintes regressões mínimas devem ser executadas quando aplicáveis:

- **D23D22**: regularização histórica da Sede
- **D23D24**: consistência Decimal/relatórios
- **D23D28**: Dashboard Financeiro
- **D23D44B**: homologação PostgreSQL de produção

Quando aplicável, incluir também testes específicos da mudança realizada.

## Checklist para futuras mudanças

- [ ] Regra financeira alterada?
- [ ] Banco/schema alterado?
- [ ] Models alterados?
- [ ] Cálculo de saldo alterado?
- [ ] Repasse alterado?
- [ ] Relatórios alterados?
- [ ] Dashboard alterado?
- [ ] Testes específicos criados?
- [ ] D23D22 passou?
- [ ] D23D24 passou?
- [ ] D23D28 passou?
- [ ] D23D44B passou?
- [ ] PostgreSQL validado?
- [ ] Persistência auditada?
- [ ] Commit isolado?
- [ ] Push sem force?

## Status oficial

**MÓDULO FINANCEIRO OBPC**
**HOMOLOGADO EM PRODUÇÃO**

### Baseline

```text
TOTAL_LANCAMENTOS: 546
SALDO: R$ 642,24
```

**Data:** 2026-08-20

**Observação:** 06/2026 e 07/2026 permanecem pendentes conforme a situação real auditada, não representando falha de homologação.
