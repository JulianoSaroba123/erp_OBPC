# Funcionalidade de Aniversariantes - Sistema OBPC

## Descrição
Implementada uma funcionalidade completa que notifica e destaca os aniversariantes do mês no sistema de gerenciamento da igreja.

## Funcionalidades Implementadas

### 1. Página de Aniversariantes do Mês
- **Rota**: `/membros/aniversariantes`
- **Acesso**: Através do botão "Aniversariantes" na lista de membros
- **Funcionalidades**:
  - Lista todos os membros que fazem aniversário no mês atual
  - Ordena por dia do aniversário
  - Destaca aniversariantes de hoje com badge amarelo
  - Mostra contagem regressiva em dias para próximos aniversários
  - Exibe idade que a pessoa completará
  - Mostra informações de contato (telefone e email)
  - Design responsivo com visual moderno

### 2. Notificação no Painel Principal
- **Localização**: Painel principal do sistema
- **Funcionalidades**:
  - Card especial destacando aniversariantes do dia atual
  - Aparece apenas quando há aniversariantes
  - Mostra nome, idade, telefone e email
  - Link direto para ver todos os aniversariantes do mês
  - Design com destaque visual (ícone de presente, cor amarela)

### 3. Botão de Acesso Rápido
- **Localização**: Página de lista de membros
- **Funcionalidades**:
  - Botão "Aniversariantes" em destaque com ícone de bolo
  - Cor amarela/warning para chamar atenção
  - Acesso rápido à lista completa de aniversariantes

## Detalhes Técnicos

### Arquivos Modificados

1. **app/membros/membros_routes.py**
   - Adicionada importação: `from sqlalchemy import extract`
   - Nova rota: `@membros_bp.route('/aniversariantes')`
   - Função `aniversariantes()` que:
     - Busca membros por mês de nascimento
     - Calcula idade atual
     - Calcula dias restantes até o aniversário
     - Classifica status: 'hoje', 'proximo' ou 'passou'

2. **app/membros/templates/membros/aniversariantes.html**
   - Template completo com design responsivo
   - Cards coloridos por status do aniversário
   - Badges indicativos
   - Layout adaptável para mobile

3. **app/membros/templates/membros/lista_membros.html**
   - Adicionado botão "Aniversariantes" no cabeçalho

4. **app/usuario/usuario_routes.py**
   - Função `painel()` atualizada
   - Busca aniversariantes do dia atual
   - Passa dados para o template

5. **app/templates/painel.html**
   - Novo card de aniversariantes do dia
   - Design consistente com os outros cards do painel
   - Link para ver lista completa

### Lógica de Funcionamento

#### Busca de Aniversariantes
```python
# Busca membros que fazem aniversário no mês atual
aniversariantes_mes = Membro.query.filter(
    extract('month', Membro.data_nascimento) == mes_atual
).order_by(extract('day', Membro.data_nascimento)).all()
```

#### Classificação por Status
- **hoje**: Aniversário é hoje (dias_restantes == 0)
- **proximo**: Aniversário ainda vai acontecer (dias_restantes > 0)
- **passou**: Aniversário já passou neste mês (dias_restantes < 0)

#### Cálculo de Idade
```python
idade = ano_atual - membro.data_nascimento.year
```

## Como Usar

### Para Visualizar Aniversariantes do Mês
1. Acesse o menu "Membros"
2. Clique no botão amarelo "Aniversariantes"
3. Visualize a lista completa ordenada por data

### Para Ver Aniversariantes de Hoje
1. Acesse o painel principal do sistema
2. O card aparecerá automaticamente se houver aniversariantes
3. Clique no link "Ver todos os aniversariantes do mês" para mais detalhes

## Recursos Visuais

### Cores e Ícones
- **Amarelo/Warning**: Aniversariantes de hoje
- **Azul/Primary**: Próximos aniversários
- **Cinza/Secondary**: Aniversários que já passaram
- **Ícones**: 🎂 Bolo, 🎁 Presente, ⭐ Estrela

### Informações Exibidas
- Nome completo
- Dia do aniversário
- Idade atual/que completará
- Telefone (se cadastrado)
- Email (se cadastrado)
- Dias restantes ou dias passados

## Melhorias Futuras Sugeridas

1. **Notificação por Email**
   - Configurar servidor SMTP
   - Envio automático de parabéns

2. **Mensagens WhatsApp**
   - Integração com API do WhatsApp Business
   - Envio automático de mensagens

3. **Relatório Mensal**
   - Exportar lista de aniversariantes em PDF
   - Incluir estatísticas

4. **Notificações Push**
   - Alertas no navegador
   - Lembretes antecipados

5. **Aniversários da Semana**
   - Card adicional no painel
   - Visão de curto prazo

## Observações

- A funcionalidade considera apenas membros com status "Ativo"
- Necessário ter data de nascimento cadastrada
- Cálculo de idade é feito com base no ano atual
- Interface totalmente responsiva (mobile-friendly)
- Ordenação automática por dia do mês
