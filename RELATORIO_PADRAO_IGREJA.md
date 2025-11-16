# 📊 RELATÓRIO DA SEDE - PADRÃO OFICIAL DA IGREJA OBPC

## 🎯 Objetivos da Atualização

Esta documentação descreve as melhorias implementadas no sistema de relatórios da sede para seguir o **padrão oficial da Igreja O Brasil para Cristo**.

## 🆕 Novo Formato do Relatório

### 📋 Estrutura Oficial

1. **Cabeçalho Institucional**
   - Logo e título "OBPC - O BRASIL PARA CRISTO"
   - Subtítulo "RELATÓRIO MENSAL OFICIAL"
   - Linha decorativa azul institucional

2. **Informações da Igreja**
   - Dados em formato tabular organizado
   - Cidade: Tietê / Bairro: Centro
   - Dirigente: Pastor João Silva
   - Tesoureiro: Maria Santos
   - Mês/Ano e Data do Relatório

3. **Seções Financeiras com Cores Identificadoras**
   - 🤲 **ARRECADAÇÃO DO MÊS** (Verde)
   - 💳 **DESPESAS FINANCEIRAS** (Vermelho)
   - ⚖️ **SALDO DO MÊS** (Azul)
   - 👥 **VALOR DO CONSELHO ADMINISTRATIVO** (Laranja)
   - 📤 **LISTA DE ENVIOS À SEDE** (Turquesa)

4. **Campos de Assinatura Oficiais**
   - Pastor João Silva (DIRIGENTE)
   - Maria Santos (TESOUREIRO)

5. **Rodapé com Data e Local**
   - Data por extenso: "Tietê, XX de Mês de XXXX"
   - Informações do sistema

## 🎨 Identidade Visual

### Cores Oficiais Utilizadas
- **Azul Institucional**: `#000080` (títulos principais)
- **Verde Arrecadação**: `#006400` (receitas)
- **Vermelho Despesas**: `#DC143C` (gastos)
- **Azul Saldo**: `#4169E1` (saldo)
- **Laranja Conselho**: `#FF6B35` (conselho administrativo)
- **Turquesa Envios**: `#20B2AA` (envios sede)

### Tipografia
- **Títulos**: Helvetica-Bold, 18pt
- **Subtítulos**: Helvetica-Bold, 14pt
- **Textos**: Helvetica, 10-12pt
- **Valores**: Helvetica-Bold (destaque)

## ⚙️ Configurações Dinâmicas

### Percentual do Conselho
- **Valor**: 30% (configurável no sistema)
- **Cálculo**: Automático sobre total arrecadado
- **Fonte**: Tabela `configuracoes_igreja`

### Despesas Fixas da Sede
Sistema integrado com base de dados:
- Contador Sede: R$ 100,00
- Força para Viver: R$ 50,00
- Oferta Voluntária Conchas: R$ 100,00
- Projeto Filipe: R$ 10,00
- Site: R$ 20,00

**Total de Envios**: R$ 280,00

## 📊 Seções Detalhadas

### 1. Arrecadação do Mês
```
┌─────────────────────┬────────────┐
│ Dízimos             │ R$ XXX,XX  │
│ Ofertas Alçadas     │ R$ XXX,XX  │
│ Outras Ofertas      │ R$ XXX,XX  │
├─────────────────────┼────────────┤
│ TOTAL GERAL         │ R$ XXX,XX  │
└─────────────────────┴────────────┘
```

### 2. Despesas Financeiras
```
┌─────────────────────┬────────────┐
│ Despesas do Mês     │ R$ XXX,XX  │
└─────────────────────┴────────────┘
```

### 3. Saldo do Mês
```
┌─────────────────────┬────────────┐
│ Saldo do Mês        │ R$ XXX,XX  │
└─────────────────────┴────────────┘
```
*Cor de fundo: Verde (positivo) ou Vermelho (negativo)*

### 4. Valor do Conselho (30%)
```
┌─────────────────────┬────────────┐
│ Valor à Sede (30%)  │ R$ XXX,XX  │
└─────────────────────┴────────────┘
```

### 5. Lista de Envios à Sede
```
┌─────────────────────┬────────────┐
│ Contador Sede       │ R$ 100,00  │
│ Força para Viver    │ R$ 50,00   │
│ Of. Vol. Conchas    │ R$ 100,00  │
│ Projeto Filipe      │ R$ 10,00   │
│ Site                │ R$ 20,00   │
├─────────────────────┼────────────┤
│ TOTAL ENVIO SEDE    │ R$ 280,00  │
└─────────────────────┴────────────┘
```

## 🔧 Implementação Técnica

### Arquivo Principal
- **Localização**: `app/utils/gerar_pdf_reportlab.py`
- **Função**: `gerar_relatorio_sede()`
- **Biblioteca**: ReportLab

### Funções Auxiliares Criadas
1. `_criar_cabecalho_sede_oficial()` - Cabeçalho institucional
2. `_criar_info_periodo_sede()` - Informações da igreja
3. `_calcular_totais_sede()` - Cálculos financeiros
4. `_obter_despesas_fixas_sede()` - Despesas dinâmicas
5. `_criar_secao_arrecadacao_sede()` - Seção de receitas
6. `_criar_secao_despesas_sede()` - Seção de gastos
7. `_criar_secao_saldo_sede()` - Seção de saldo
8. `_criar_secao_conselho_sede()` - Seção do conselho
9. `_criar_secao_envios_sede()` - Seção de envios
10. `_criar_assinaturas_sede()` - Campos de assinatura
11. `_criar_rodape_sede()` - Rodapé oficial

## ✅ Validações Implementadas

### Testes Automáticos
- ✅ Percentual do conselho (30%)
- ✅ Despesas fixas (5 itens)
- ✅ Geração de PDF
- ✅ Formatação de valores
- ✅ Layout responsivo

### Arquivo de Teste
- **Script**: `testar_relatorio_sede_melhorias.py`
- **PDF Gerado**: `teste_relatorio_sede_HHMMSS.pdf`

## 📁 Arquivos Relacionados

```
app/
├── utils/
│   └── gerar_pdf_reportlab.py      # Geração do PDF
├── financeiro/
│   ├── financeiro_routes.py        # Rotas (30% conselho)
│   └── despesas_fixas_model.py     # Despesas dinâmicas
└── configuracoes/
    └── configuracoes_model.py      # Configurações gerais

tests/
├── testar_relatorio_sede_melhorias.py  # Testes
└── teste_relatorio_sede_*.pdf          # PDFs gerados
```

## 🎉 Benefícios Implementados

1. **Padronização Oficial**: Seguindo identidade visual da igreja
2. **Automatização**: Despesas e percentuais dinâmicos
3. **Profissionalismo**: Layout organizado e oficial
4. **Manutenibilidade**: Código modular e documentado
5. **Flexibilidade**: Configurações ajustáveis
6. **Qualidade**: Testes automatizados

## 📞 Suporte

Para dúvidas sobre o novo formato de relatório:
- **Sistema**: ERP OBPC
- **Versão**: 2025.1
- **Documentação**: Esta documentação
- **Testes**: Scripts automáticos inclusos

---
*Documentação atualizada em Dezembro/2024*
*Sistema Administrativo OBPC - Igreja O Brasil para Cristo*