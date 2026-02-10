# Sistema de Notificações por Email e WhatsApp - Sistema OBPC

## 📋 Descrição

Sistema completo de notificações que permite enviar alertas de aniversariantes via **Email** e **WhatsApp**. O sistema é configurável e oferece rastreamento de todas as notificações enviadas.

## 🎯 Funcionalidades Principais

### 1. **Notificações por Email**
- ✅ Envio de emails SMTP
- ✅ Suporte para Gmail, Outlook, e otros servidores
- ✅ Notificação ao próprio aniversariante
- ✅ Notificação ao administrador
- ✅ Interface de teste para validação

### 2. **Notificações por WhatsApp**
- ✅ Suporte a múltiplos providers:
  - **Twilio** - Líder em comunicações
  - **Uma-msg** - API simples brasileira
  - **Gupshup** - Solução escalável
- ✅ Envio automático para membros
- ✅ Rastreamento de entregas

### 3. **Configurações Flexíveis**
- ✅ Habilitar/desabilitar por canal
- ✅ Notificar membros sobre seu aniversário
- ✅ Notificar administrador
- ✅ Antecipação de dias antes do aniversário
- ✅ Histórico completo de notificações

## 📁 Estrutura do Módulo

```
app/notificacoes/
├── __init__.py                          # Inicialização
├── notificacoes_model.py                # Modelos de dados
├── notificacoes_service.py              # Serviço de notificações
├── notificacoes_routes.py               # Rotas e views
└── templates/notificacoes/
    ├── configurar_notificacoes.html     # Página de configuração
    └── historico_notificacoes.html      # Histórico
```

## 🚀 Como Começar

### 1. **Acessar Configurações**
1. Acesse o menu de administração
2. Clique em "Notificações" → "Configurações"
3. Configure Email e/ou WhatsApp

### 2. **Configurar Email**

#### Gmail
```
Servidor SMTP: smtp.gmail.com
Porta: 587
Usuário: seu-email@gmail.com
Senha: (Usar senha de app gerada em https://myaccount.google.com/apppasswords)
```

#### Outlook
```
Servidor SMTP: smtp-mail.outlook.com
Porta: 587
Usuário: seu-email@outlook.com
Senha: sua-senha
```

### 3. **Configurar WhatsApp**

#### Opção 1: Twilio
1. Acesse https://www.twilio.com
2. Crie uma conta
3. Configure um serviço WhatsApp
4. Copie Account SID e Auth Token
5. Obtenha um número Twilio
6. Preencha os dados na configuração

#### Opção 2: Uma-msg
1. Acesse https://www.umamsg.com
2. Crie uma conta
3. Gere uma API Key
4. Copie a URL do endpoint
5. Preencha os dados na configuração

### 4. **Testar Configurações**

**Para Email:**
- Clique no botão "Testar Email"
- Informe um email válido
- Verifique a caixa de entrada

**Para WhatsApp:**
- Clique no botão "Testar WhatsApp"
- Informe um número no formato: 55XXXXXXXXXXX
- Aguarde a mensagem

## 📊 Modelos de Dados

### ConfiguracaoNotificacoes
Armazena as configurações globais de notificações:

```python
- email_habilitado: bool
- email_remetente: str
- email_admin: str
- smtp_server: str
- smtp_porta: int
- smtp_usuario: str
- smtp_senha: str (criptografado)
- whatsapp_habilitado: bool
- whatsapp_provider: str ('twilio', 'uma-msg', 'gupshup')
- whatsapp_account_sid: str
- whatsapp_auth_token: str
- whatsapp_numero: str
- whatsapp_api_key: str
- whatsapp_api_url: str
- notificar_aniversariantes: bool
- notificar_admin: bool
- dias_antes: int
```

### HistoricoNotificacoes
Rastreia cada notificação enviada:

```python
- tipo: str ('email', 'whatsapp')
- destinatario: str
- membro_id: int
- titulo: str
- mensagem: str (texto/conteúdo)
- status: str ('enviando', 'enviado', 'erro')
- erro_mensagem: str
- enviado_em: datetime
```

## 🔌 API de Serviço

### ServicoNotificacoes

#### Enviar Email
```python
from app.notificacoes.notificacoes_service import ServicoNotificacoes

resultado = ServicoNotificacoes.enviar_email(
    destinatario='usuario@example.com',
    assunto='Título do email',
    corpo_html='<h1>Conteúdo em HTML</h1>',
    corpo_texto='Conteúdo em texto (opcional)'
)

# Resposta: {'sucesso': True/False, 'mensagem': 'mensagem...'}
```

#### Enviar WhatsApp
```python
resultado = ServicoNotificacoes.enviar_whatsapp(
    numero='5511999999999',
    mensagem='Sua mensagem aqui',
    membro_id=123  # opcional
)

# Resposta: {'sucesso': True/False, 'mensagem': 'mensagem...'}
```

#### Obter Histórico
```python
historico = ServicoNotificacoes.obter_historico(
    filtro_tipo='email',      # ou 'whatsapp'
    filtro_status='enviado',  # ou 'erro', 'enviando'
    limite=100
)
```

## 📧 Notificações Automáticas de Aniversário

### Como Funciona
1. Ao acessar a página de aniversariantes, o sistema:
   - Busca membros que fazem aniversário **hoje**
   - Se configured, envia notificações automáticamente
   - Registra todas no histórico

2. **Destinatários:**
   - 📨 **Próprio membro** (se configurado) - Felicidades pessoal
   - 👨‍💼 **Administrador** (se configurado) - Lembrete para contato
   - 📱 **WhatsApp** (se configurado) - Mensagem automática

### Conteúdo das Mensagens

#### Email ao Membro
```
Assunto: 🎉 Feliz Aniversário, [Nome]!

Corpo: Que o Senhor abençoe sua vida abundantemente neste novo ano!
```

#### Email ao Admin
```
Assunto: 📢 Aniversário de [Nome]

Corpo: Lembrança para entrar em contato com o membro no aniversário dele
```

#### WhatsApp
```
🎉 Feliz Aniversário, [Nome]!
Que o Senhor abençoe sua vida abundantemente neste novo ano!
Data: DD/MM
Idade: X anos
```

## 🔐 Segurança

### Boas Práticas Implementadas
- Senhas armazenadas (idealmente criptografadas)
- Validação de emails e números
- Rastreamento completo de notificações
- Tratamento robusto de erros
- Logs de todas as operações

### Recomendações
1. **Nunca** compartilhe credenciais SMTP/WhatsApp
2. **Use** senhas de aplicativos (não senhas principais)
3. **Ambientes** - configure credenciais por ambiente (DEV/PROD)
4. **Auditoria** - revise o histórico regularmente

## 🐛 Troubleshooting

### Email não é enviado
- ✅ Verificar se email está habilitado
- ✅ Validar credenciais SMTP
- ✅ Testar com o botão "Testar Email"
- ✅ Verificar firewall/proxy
- ✅ Para Gmail, usar senha de app

### WhatsApp não funciona
- ✅ Verificar se WhatsApp está habilitado
- ✅ Validar provider selecionado
- ✅ Testar com o botão "Testar WhatsApp"
- ✅ Número deve estar no formato: 55XXXXXXXXXXX
- ✅ Verificar saldo/quota do provider

### Mensagens não aparecem no histórico
- ✅ Pode estar filtrando por tipo/status
- ✅ Histórico pode estar vazio se nenhuma notificação foi enviada
- ✅ Verificar logs da aplicação

## 📚 Rotas Disponíveis

| Rota | Método | Descrição |
|------|--------|-----------|
| `/notificacoes/configuracoes` | GET, POST | Configurar notificações |
| `/notificacoes/testar-email` | POST | Testar envio de email |
| `/notificacoes/testar-whatsapp` | POST | Testar envio de WhatsApp |
| `/notificacoes/historico` | GET | Visualizar histórico |

## 🔄 Fluxo de Integração com Aniversariantes

```
Usuário acessa /membros/aniversariantes
         ↓
Sistema busca aniversariantes do mês
         ↓
Se houver aniversário hoje:
         ↓
    Chamada enviar_notificacoes_aniversario()
         ↓
   ├─ Verifica se Email habilitado
   │   └─ Envia para membro (se configurado)
   │   └─ Envia para admin (se configurado)
   │
   └─ Verifica se WhatsApp habilitado
       └─ Envia para membro (se número cadastrado)
         ↓
Todas registradas no HistoricoNotificacoes
         ↓
Página exibida normalmente
```

## 🚦 Próximos Passos

1. **Validar** as configurações com testes
2. **Ativar** notificações para seu grupo
3. **Monitorar** histórico regularmente
4. **Ajustar** horários e frequência conforme necessário

## 📞 Suporte

Para problemas ou dúvidas:
1. Verificar logs em `/notificacoes/historico`
2. Testar novamente com os botões de teste
3. Validar credenciais de provider
4. Revalidar números de telefone

---

**Desenvolvido para Igreja O Brasil para Cristo - Sistema OBPC 2026**
