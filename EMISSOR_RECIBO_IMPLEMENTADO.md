# Emissor de Recibo - Sistema Financeiro

## 📋 Descrição

Foi implementado um sistema completo de emissão de recibos para doações e ofertas no módulo financeiro do ERP OBPC.

## ✨ Características

### 1. Formulário Web Completo
- **Dados do Doador:**
  - Nome completo (obrigatório)
  - CPF/CNPJ (opcional, com máscara automática)
  
- **Dados da Doação:**
  - Número do recibo (gerado automaticamente se não informado)
  - Valor da doação (com formatação monetária automática)
  - Data da doação
  - Tipo de doação (Oferta, Dízimo, Oferta Missionária, Doação para Projeto, etc.)
  - Forma de pagamento (Dinheiro, PIX, Transferência, Cartão, Cheque)
  - Observações (campo opcional para informações adicionais)

### 2. Geração de PDF Profissional
- **Layout Personalizado:**
  - Utiliza as cores e configurações do sistema
  - Logo da igreja no cabeçalho
  - Informações completas da igreja (nome, endereço, CNPJ)
  - Número do recibo destacado
  - Valor em destaque e por extenso
  
- **Conteúdo do Recibo:**
  - Texto formal de recibo
  - Tabela com informações da doação
  - Local e data por extenso
  - Espaço para assinatura
  - Rodapé informativo sobre validade para imposto de renda
  - Data e hora de emissão

### 3. Validações e Segurança
- Validação de campos obrigatórios
- Validação de valor (deve ser maior que zero)
- Formatação automática de valores monetários
- Máscara automática para CPF/CNPJ
- Geração automática de número de recibo único

## 🚀 Como Usar

### Acessando o Emissor de Recibo

1. Faça login no sistema
2. Acesse o menu **Financeiro** no painel lateral
3. Clique em **Emitir Recibo**

### Emitindo um Recibo

1. Preencha os dados do doador:
   - **Nome completo** (obrigatório)
   - **CPF/CNPJ** (opcional - a máscara é aplicada automaticamente)

2. Preencha os dados da doação:
   - **Número do recibo** (opcional - será gerado automaticamente no formato REC-ANO-TIMESTAMP)
   - **Valor** (obrigatório - digite apenas números, a formatação é automática)
   - **Data da doação** (obrigatório - padrão: data atual)
   - **Tipo de doação** (selecione uma opção)
   - **Forma de pagamento** (selecione uma opção)
   - **Observações** (opcional - informações adicionais)

3. Clique em **Gerar Recibo (PDF)**

4. O PDF será baixado automaticamente e estará pronto para impressão

## 📁 Arquivos Criados/Modificados

### Arquivos Criados:
1. **`app/financeiro/templates/financeiro/emitir_recibo.html`**
   - Template HTML do formulário de emissão de recibo
   - Interface responsiva e moderna
   - JavaScript para formatação automática de valores e CPF/CNPJ

### Arquivos Modificados:

1. **`app/financeiro/financeiro_routes.py`**
   - Adicionada rota `/financeiro/emitir-recibo` (GET e POST)
   - Função `emitir_recibo()` para processar o formulário e gerar o PDF

2. **`app/utils/gerar_pdf_reportlab.py`**
   - Adicionada função `gerar_recibo_pdf()` para gerar o PDF do recibo
   - Adicionada função `converter_valor_extenso()` para converter valores numéricos em texto por extenso

3. **`app/templates/base.html`**
   - Adicionado link "Emitir Recibo" no menu Financeiro

## 🎨 Recursos Técnicos

### Frontend:
- HTML5 e CSS3
- Bootstrap 5 para layout responsivo
- JavaScript vanilla para validações e máscaras
- Formatação automática de valores monetários
- Máscara automática de CPF/CNPJ

### Backend:
- Flask para rotas e processamento
- ReportLab para geração de PDFs profissionais
- Integração com configurações do sistema (cores, logo, dados da igreja)
- Validações server-side

### Geração de PDF:
- Layout A4 profissional
- Cores personalizáveis via configurações do sistema
- Logo da igreja
- Texto formatado em português
- Valor por extenso automaticamente
- Assinatura institucional
- Rodapé informativo

## 📝 Exemplo de Uso

### Cenário: Emitir recibo de oferta
1. Doador: João Silva
2. CPF: 123.456.789-00
3. Valor: R$ 100,00
4. Tipo: Oferta
5. Forma: PIX
6. Data: 08/05/2026

**Resultado:** PDF gerado com todas as informações formatadas, valor por extenso (cem reais), pronto para impressão e entrega ao doador.

## 🔒 Segurança e Permissões

- Apenas usuários autenticados podem acessar
- Requer permissão de acesso ao módulo financeiro
- Decorator `@login_required` aplicado
- Validações tanto no frontend quanto no backend

## 💡 Observações Importantes

1. **Número do Recibo:** Se não for informado, será gerado automaticamente no formato `REC-ANO-TIMESTAMP` (ex: REC-2026-05081430)

2. **Valor por Extenso:** Implementado para valores até R$ 999.999,99 em português

3. **Validade Fiscal:** O rodapé do recibo informa que é válido para declaração de imposto de renda

4. **Personalização:** O recibo usa automaticamente as configurações do sistema (logo, cores, nome da igreja, endereço, CNPJ)

## 🔄 Melhorias Futuras Sugeridas

- [ ] Salvar histórico de recibos emitidos no banco de dados
- [ ] Sistema de busca e reimpressão de recibos anteriores
- [ ] Envio automático por e-mail
- [ ] Geração de recibos em lote
- [ ] QR Code para validação digital
- [ ] Numeração sequencial mais sofisticada
- [ ] Relatório de recibos emitidos por período
- [ ] Integração com lançamentos financeiros

## 📞 Suporte

Para dúvidas ou problemas, consulte a documentação do sistema ou entre em contato com o administrador.

---

**Implementado em:** 08/05/2026  
**Status:** ✅ Operacional  
**Versão:** 1.0
