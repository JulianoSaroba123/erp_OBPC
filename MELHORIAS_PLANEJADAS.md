# 🎯 MELHORIAS PLANEJADAS - SISTEMA ERP OBPC
## Igreja O Brasil para Cristo - Tietê/SP

**Data de Criação:** 21/01/2026  
**Versão:** 1.0  
**Status do Projeto:** 8.5/10 ⭐⭐⭐⭐⭐

---

## 📊 RESUMO DA ANÁLISE

### ✅ Pontos Fortes
- Arquitetura modular e escalável (Blueprints)
- Sistema de níveis de acesso hierárquico bem implementado
- Segurança básica com Flask-Login e hashing de senhas
- Geração de PDFs profissionais (ReportLab + WeasyPrint)
- Suporte PostgreSQL (produção) + SQLite (desenvolvimento)
- Interface Bootstrap moderna e responsiva

### ⚠️ Pontos de Atenção
- Senha padrão hardcoded em produção
- SECRET_KEY exposta no código
- Falta de testes automatizados
- Muitos arquivos de debug/teste na raiz
- Tratamento de erros incompleto em alguns pontos

---

## 🚨 CRÍTICO - SEGURANÇA (Prioridade 1)

### 1. SECRET_KEY em Variável de Ambiente
**Arquivo:** `app/config.py`  
**Status:** ❌ Pendente  
**Risco:** Alto

**Problema:**
```python
SECRET_KEY = "chave-secreta-obpc-2025-igreja-brasil-para-cristo"
```

**Solução:**
```python
SECRET_KEY = os.environ.get('SECRET_KEY')
if not SECRET_KEY:
    raise ValueError("SECRET_KEY não configurada nas variáveis de ambiente!")
```

**Ações:**
- [ ] Criar arquivo `.env.example` com template
- [ ] Atualizar `.env` com SECRET_KEY forte
- [ ] Modificar `app/config.py`
- [ ] Atualizar documentação

---

### 2. Senha Admin Padrão Forte
**Arquivo:** `run.py`  
**Status:** ❌ Pendente  
**Risco:** Alto

**Problema:**
```python
admin.set_senha('admin123')  # Senha fraca e previsível
```

**Solução:**
```python
import os
senha_admin = os.environ.get('ADMIN_PASSWORD')
if not senha_admin:
    raise ValueError("ADMIN_PASSWORD não configurada!")
admin.set_senha(senha_admin)
```

**Ações:**
- [ ] Adicionar ADMIN_PASSWORD no `.env`
- [ ] Modificar lógica em `run.py`
- [ ] Implementar troca obrigatória no primeiro login
- [ ] Documentar no README

---

### 3. Modo Debug Desabilitado em Produção
**Arquivo:** `run.py`  
**Status:** ✅ OK (já implementado corretamente)

---

## ⚠️ IMPORTANTE - ARQUITETURA (Prioridade 2)

### 4. Logs Estruturados
**Status:** ❌ Pendente  
**Impacto:** Médio

**Implementar:**
```python
# app/__init__.py
import logging
from logging.handlers import RotatingFileHandler
import os

if not os.path.exists('logs'):
    os.mkdir('logs')

file_handler = RotatingFileHandler(
    'logs/obpc.log', 
    maxBytes=10240000,  # 10MB
    backupCount=10
)
file_handler.setFormatter(logging.Formatter(
    '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
))
file_handler.setLevel(logging.INFO)
app.logger.addHandler(file_handler)
app.logger.setLevel(logging.INFO)
app.logger.info('Sistema OBPC iniciado')
```

**Ações:**
- [ ] Criar pasta `logs/`
- [ ] Adicionar código de logging em `app/__init__.py`
- [ ] Adicionar `logs/` no `.gitignore`
- [ ] Documentar localização dos logs

---

### 5. Tratamento de Erros Consistente
**Status:** ⚠️ Parcial  
**Impacto:** Médio

**Padrão a Seguir:**
```python
try:
    db.session.commit()
    flash('Operação realizada com sucesso!', 'success')
    current_app.logger.info(f'Sucesso: {descricao_operacao}')
except Exception as e:
    db.session.rollback()
    current_app.logger.error(f'Erro: {str(e)}', exc_info=True)
    flash('Erro ao processar operação. Contate o suporte.', 'danger')
```

**Ações:**
- [ ] Revisar todos os `db.session.commit()` sem try/except
- [ ] Adicionar logging em operações críticas
- [ ] Padronizar mensagens de erro
- [ ] Criar helper function para commits seguros

---

### 6. Organização de Arquivos
**Status:** ❌ Pendente  
**Impacto:** Baixo (organização)

**Estrutura Proposta:**
```
/scripts/
  /debug/          # arquivos debug_*.py
  /migracao/       # adicionar_*.py, atualizar_*.py
  /testes/         # teste_*.py, testar_*.py
  /utils/          # criar_*.py, verificar_*.py
/docs/             # arquivos .md de documentação
/backups/          # backups automáticos
```

**Ações:**
- [ ] Criar estrutura de pastas
- [ ] Mover arquivos para pastas apropriadas
- [ ] Atualizar imports se necessário
- [ ] Atualizar `.gitignore`

---

### 7. Testes Automatizados
**Status:** ❌ Não implementado  
**Impacto:** Alto (qualidade)

**Estrutura de Testes:**
```python
# tests/test_usuario.py
import pytest
from app import create_app, db
from app.usuario.usuario_model import Usuario

@pytest.fixture
def client():
    app = create_app()
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    
    with app.test_client() as client:
        with app.app_context():
            db.create_all()
        yield client

def test_criar_usuario(client):
    response = client.post('/usuario/cadastrar', data={
        'nome': 'Teste',
        'email': 'teste@obpc.com',
        'senha': 'senha123'
    }, follow_redirects=True)
    assert response.status_code == 200
    
def test_login_sucesso(client):
    # Criar usuário
    user = Usuario(nome='Admin', email='admin@test.com')
    user.set_senha('senha123')
    db.session.add(user)
    db.session.commit()
    
    # Testar login
    response = client.post('/usuario/login', data={
        'email': 'admin@test.com',
        'senha': 'senha123'
    }, follow_redirects=True)
    assert b'Bem-vindo' in response.data
```

**Ações:**
- [ ] Instalar pytest e pytest-flask
- [ ] Criar pasta `tests/`
- [ ] Implementar testes básicos (usuário, login)
- [ ] Implementar testes financeiro
- [ ] Configurar CI/CD (GitHub Actions)
- [ ] Meta: 50% cobertura de código

---

## 📱 FUNCIONALIDADES MINISTERIAIS (Prioridade 3)

### 8. Dashboard com Métricas Espirituais
**Status:** ❌ Não implementado  
**Impacto:** Alto (gestão pastoral)

**Funcionalidades:**
- Total de membros (ativos/inativos)
- Crescimento mensal de membros
- Novos convertidos (últimos 30 dias)
- Batizados no ano
- Frequência média de cultos
- Dizimistas regulares (%)
- Gráficos interativos (Chart.js)

**Ações:**
- [ ] Criar rota `/dashboard/metricas`
- [ ] Implementar queries de estatísticas
- [ ] Integrar Chart.js
- [ ] Criar cards com indicadores
- [ ] Adicionar filtros (período, departamento)

---

### 9. Gestão de Células/Grupos Pequenos
**Status:** ❌ Não implementado  
**Impacto:** Alto (crescimento da igreja)

**Modelo de Dados:**
```python
class Celula(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    lider_id = db.Column(db.Integer, db.ForeignKey('membros.id'))
    vice_lider_id = db.Column(db.Integer, db.ForeignKey('membros.id'))
    dia_semana = db.Column(db.String(20))
    horario = db.Column(db.Time)
    endereco = db.Column(db.String(200))
    bairro = db.Column(db.String(100))
    ativa = db.Column(db.Boolean, default=True)
    meta_membros = db.Column(db.Integer, default=12)
    
class MembroCelula(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    celula_id = db.Column(db.Integer, db.ForeignKey('celulas.id'))
    membro_id = db.Column(db.Integer, db.ForeignKey('membros.id'))
    data_entrada = db.Column(db.Date, default=datetime.utcnow)
    
class RelatorioCelula(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    celula_id = db.Column(db.Integer, db.ForeignKey('celulas.id'))
    data_reuniao = db.Column(db.Date, nullable=False)
    presentes = db.Column(db.Integer)
    visitantes = db.Column(db.Integer, default=0)
    decisoes = db.Column(db.Integer, default=0)
    tema_estudo = db.Column(db.String(200))
    observacoes = db.Column(db.Text)
```

**Ações:**
- [ ] Criar modelos (Celula, MembroCelula, RelatorioCelula)
- [ ] Criar blueprint `celulas`
- [ ] Implementar CRUD de células
- [ ] Sistema de relatórios semanais
- [ ] Dashboard de células (mapa, estatísticas)
- [ ] Relatório de multiplicação

---

### 10. Acompanhamento de Novos Convertidos
**Status:** ❌ Não implementado  
**Impacto:** Alto (discipulado)

**Modelo:**
```python
class NovoConvertido(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    telefone = db.Column(db.String(20))
    email = db.Column(db.String(100))
    data_decisao = db.Column(db.Date, nullable=False)
    como_conheceu = db.Column(db.String(200))  # Célula, Culto, Evento
    conselheiro_id = db.Column(db.Integer, db.ForeignKey('membros.id'))
    fase_discipulado = db.Column(db.String(50))  # Inicial, Batismo, Membro
    visitas_realizadas = db.Column(db.Integer, default=0)
    proximo_contato = db.Column(db.Date)
    batizado = db.Column(db.Boolean, default=False)
    data_batismo = db.Column(db.Date)
    membro = db.Column(db.Boolean, default=False)
```

**Ações:**
- [ ] Criar modelo NovoConvertido
- [ ] Criar blueprint `discipulado`
- [ ] Formulário de cadastro rápido
- [ ] Sistema de lembretes de contato
- [ ] Relatório de acompanhamento
- [ ] Integração com módulo de membros

---

### 11. Relatório de Dízimos Individual (Para IR)
**Status:** ❌ Não implementado  
**Impacto:** Alto (serviço aos membros)

**Funcionalidade:**
```python
@financeiro_bp.route('/dizimos/<int:membro_id>/ano/<int:ano>/pdf')
@login_required
def relatorio_dizimos_membro_pdf(membro_id, ano):
    """
    Gera declaração de dízimos para Imposto de Renda
    Dedução até 6% do IR conforme legislação
    """
    membro = Membro.query.get_or_404(membro_id)
    
    dizimos = Lancamento.query.filter(
        Lancamento.categoria == 'Dízimo',
        Lancamento.descricao.contains(membro.nome),
        extract('year', Lancamento.data) == ano
    ).order_by(Lancamento.data).all()
    
    total_ano = sum(d.valor for d in dizimos)
    
    # Gerar PDF oficial com:
    # - Logo da igreja
    # - CNPJ da igreja
    # - Dados do membro
    # - Lista mensal de dízimos
    # - Total anual
    # - Assinatura do tesoureiro
```

**Ações:**
- [ ] Criar rota de relatório individual
- [ ] Template PDF profissional
- [ ] Validar dados (CPF do membro)
- [ ] Assinatura digital (opcional)
- [ ] Portal do membro (auto-serviço)

---

### 12. Sistema de Pedidos de Oração
**Status:** ❌ Não implementado  
**Impacto:** Médio (cuidado pastoral)

**Modelo:**
```python
class PedidoOracao(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    membro_id = db.Column(db.Integer, db.ForeignKey('membros.id'))
    pedido = db.Column(db.Text, nullable=False)
    categoria = db.Column(db.String(50))  # Saúde, Família, Trabalho, Espiritual
    urgente = db.Column(db.Boolean, default=False)
    publico = db.Column(db.Boolean, default=False)  # Compartilhar no culto?
    respondido = db.Column(db.Boolean, default=False)
    testemunho_resposta = db.Column(db.Text)
    data_pedido = db.Column(db.DateTime, default=datetime.utcnow)
    data_resposta = db.Column(db.Date)
```

**Ações:**
- [ ] Criar modelo PedidoOracao
- [ ] Formulário de cadastro
- [ ] Painel para liderança
- [ ] Lista de orações para culto (PDF)
- [ ] Registro de testemunhos

---

## 💰 MELHORIAS FINANCEIRAS (Prioridade 3)

### 13. Previsão Orçamentária
**Status:** ❌ Não implementado  
**Impacto:** Médio

**Modelo:**
```python
class Orcamento(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    ano = db.Column(db.Integer, nullable=False)
    mes = db.Column(db.Integer, nullable=False)
    categoria = db.Column(db.String(100), nullable=False)
    valor_previsto = db.Column(db.Float, nullable=False)
    
    @property
    def valor_realizado(self):
        # Calcular do Lancamento
        pass
    
    @property
    def variacao_percentual(self):
        # (realizado - previsto) / previsto * 100
        pass
```

**Ações:**
- [ ] Criar modelo Orcamento
- [ ] Formulário de planejamento anual
- [ ] Relatório: Previsto x Realizado
- [ ] Alertas de desvio > 20%
- [ ] Gráficos comparativos

---

### 14. Gestão de Projetos - Melhorias
**Status:** ⚠️ Parcial (já existe, melhorar)  
**Impacto:** Médio

**Adicionar:**
- Meta de arrecadação
- Barra de progresso visual
- Prestação de contas pública (PDF)
- Upload de fotos do projeto
- Histórico de doações por membro
- Certificado de doador

**Ações:**
- [ ] Adicionar campo `meta_arrecadacao`
- [ ] Criar relatório público (PDF)
- [ ] Upload de fotos (galeria)
- [ ] Dashboard de projetos ativos

---

## 🛠️ MELHORIAS TÉCNICAS (Prioridade 4)

### 15. Backup Automático
**Status:** ❌ Não implementado  
**Impacto:** Alto (segurança)

**Implementar:**
```python
# scripts/backup_automatico.py
import schedule
import shutil
import os
from datetime import datetime

def backup_database():
    hoje = datetime.now().strftime('%Y%m%d_%H%M%S')
    origem = 'instance/igreja.db'
    
    # Backup local
    if not os.path.exists('backups'):
        os.makedirs('backups')
    
    destino = f'backups/igreja_{hoje}.db'
    shutil.copy2(origem, destino)
    print(f'✅ Backup criado: {destino}')
    
    # Limpar backups antigos (manter últimos 30 dias)
    limpar_backups_antigos()

def limpar_backups_antigos():
    # Implementar lógica
    pass

# Agendar: todo dia às 2h da manhã
schedule.every().day.at("02:00").do(backup_database)

# Backup semanal para nuvem (Google Drive, Dropbox)
schedule.every().sunday.at("03:00").do(backup_nuvem)
```

**Ações:**
- [ ] Criar script de backup
- [ ] Agendar com Windows Task Scheduler
- [ ] Integração com nuvem (opcional)
- [ ] Testar restauração

---

### 16. Validação de Formulários (Flask-WTF)
**Status:** ❌ Não implementado  
**Impacto:** Médio

**Exemplo:**
```python
from flask_wtf import FlaskForm
from wtforms import StringField, FloatField, SelectField
from wtforms.validators import DataRequired, Email, NumberRange

class LancamentoForm(FlaskForm):
    descricao = StringField('Descrição', validators=[DataRequired()])
    valor = FloatField('Valor', validators=[
        DataRequired(),
        NumberRange(min=0.01, message='Valor deve ser maior que zero')
    ])
    categoria = SelectField('Categoria', choices=[...])
    tipo = SelectField('Tipo', choices=[('Entrada', 'Entrada'), ('Saída', 'Saída')])
```

**Ações:**
- [ ] Instalar Flask-WTF
- [ ] Criar forms para módulos principais
- [ ] Substituir validação manual
- [ ] Melhorar mensagens de erro

---

### 17. Cache de Consultas
**Status:** ❌ Não implementado  
**Impacto:** Médio (performance)

**Implementar:**
```python
from flask_caching import Cache

cache = Cache(app, config={
    'CACHE_TYPE': 'simple',
    'CACHE_DEFAULT_TIMEOUT': 300
})

@cache.cached(timeout=300, key_prefix='estatisticas_painel')
def obter_estatisticas_painel():
    return {
        'total_membros': Membro.query.count(),
        'total_obreiros': Obreiro.query.count(),
        'dizimistas_mes': calcular_dizimistas()
    }
```

**Ações:**
- [ ] Instalar Flask-Caching
- [ ] Cachear estatísticas do painel
- [ ] Cachear relatórios pesados
- [ ] Implementar invalidação de cache

---

## 📱 COMUNICAÇÃO (Prioridade 5)

### 18. Notificações por Email
**Status:** ❌ Não implementado  
**Impacto:** Alto

**Casos de Uso:**
- Lembrete de escala (3 dias antes)
- Aniversariantes do dia
- Convocação para reuniões
- Avisos urgentes
- Relatório mensal financeiro

**Implementar:**
```python
from flask_mail import Mail, Message

app.config['MAIL_SERVER'] = os.environ.get('MAIL_SERVER')
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD')

mail = Mail(app)

def enviar_lembrete_escala(escala):
    msg = Message(
        'Lembrete: Você está escalado',
        sender='sistema@obpc.org.br',
        recipients=[escala.obreiro.email]
    )
    msg.html = render_template('emails/lembrete_escala.html', escala=escala)
    mail.send(msg)
```

**Ações:**
- [ ] Configurar Flask-Mail
- [ ] Criar templates de email
- [ ] Implementar envios agendados
- [ ] Configurar SMTP (Gmail, SendGrid)

---

### 19. Portal do Membro
**Status:** ❌ Não implementado  
**Impacto:** Alto (engajamento)

**Funcionalidades:**
- Visualizar dados cadastrais
- Histórico de dízimos (12 meses)
- Certificados obtidos
- Escalas futuras
- Células que participa
- Pedidos de oração
- Editar dados pessoais (limitado)

**Ações:**
- [ ] Criar rota `/membro/portal`
- [ ] Dashboard personalizado
- [ ] Sistema de permissões
- [ ] Auto-atualização de dados

---

## 📈 ROADMAP DE IMPLEMENTAÇÃO

### **🔴 CURTO PRAZO (1-2 meses)**
Foco: Segurança e Estabilidade

- [ ] SECRET_KEY em variável de ambiente
- [ ] Senha admin forte e obrigatória
- [ ] Logs estruturados
- [ ] Backup automático
- [ ] Organizar arquivos em pastas
- [ ] Tratamento de erros padronizado
- [ ] Relatório de dízimos individual

**Meta:** Sistema seguro e confiável para produção

---

### **🟡 MÉDIO PRAZO (3-6 meses)**
Foco: Funcionalidades Ministeriais

- [ ] Dashboard com métricas espirituais
- [ ] Gestão de células/grupos pequenos
- [ ] Acompanhamento de novos convertidos
- [ ] Sistema de pedidos de oração
- [ ] Notificações por email
- [ ] Portal do membro
- [ ] Testes automatizados (50% cobertura)

**Meta:** Ferramentas de crescimento espiritual

---

### **🟢 LONGO PRAZO (6-12 meses)**
Foco: Inovação e Expansão

- [ ] App mobile (Flutter/React Native)
- [ ] BI e relatórios gerenciais avançados
- [ ] Automações inteligentes
- [ ] API REST para integrações
- [ ] Sistema multi-igreja (SaaS)
- [ ] Integração com lives (YouTube/Facebook)
- [ ] Sistema de doações online

**Meta:** Solução completa e escalável

---

## 📝 CONTROLE DE IMPLEMENTAÇÃO

### Como Usar Este Documento:
1. Escolher item da lista
2. Marcar como em andamento: `- [x]`
3. Criar branch específica no Git
4. Implementar com testes
5. Fazer commit e merge
6. Atualizar status neste documento

### Convenção de Status:
- ❌ Não implementado
- 🔄 Em andamento
- ⚠️ Parcialmente implementado
- ✅ Concluído

---

**Última Atualização:** 21/01/2026  
**Próxima Revisão:** A cada sprint (15 dias)

---

## 🙏 ORAÇÃO

*"Que este sistema seja usado para a glória de Deus e edificação da Sua igreja.  
Que cada linha de código reflita excelência e cuidado com o povo do Senhor.  
Em nome de Jesus, amém!"*

---

**Desenvolvido com ❤️ para a Igreja O Brasil para Cristo - Tietê/SP**
