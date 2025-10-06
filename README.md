# 🏛️ Sistema OBPC - Igreja O Brasil para Cristo

## 📋 Descrição
Sistema administrativo completo desenvolvido especificamente para a **Igreja O Brasil para Cristo - Tietê/SP**. 

### ✨ Funcionalidades Principais
- 👥 **Gestão de Membros** - Cadastro completo com CEP automático
- ⛪ **Gestão de Obreiros** - Controle de ministérios e funções
- 🏢 **Gestão de Departamentos** - Organização da igreja
- 💰 **Controle Financeiro** - Dízimos, ofertas, despesas e relatórios
- 📊 **Relatórios PDF Profissionais** - Relatórios detalhados para gestão

---

## 🚀 Instalação Rápida

### 📥 Método 1: Instalação Automática (Recomendado)
1. **Execute o instalador:**
   ```bash
   install_OBPC.bat
   ```
   - ✅ Instala Python (se necessário)
   - ✅ Cria ambiente virtual
   - ✅ Instala todas as dependências
   - ✅ Inicia o sistema automaticamente

### 💻 Método 2: Instalação Manual
1. **Clone o repositório:**
   ```bash
   git clone [repositorio]
   cd ERP_OBPC
   ```

2. **Crie ambiente virtual:**
   ```bash
   python -m venv venv
   venv\Scripts\activate
   ```

3. **Instale dependências:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Execute o sistema:**
   ```bash
   python run.py
   ```

---

## 🎯 Como Usar

### 🖥️ Executando o Sistema
1. **Primeira vez:** Execute `install_OBPC.bat`
2. **Próximas vezes:** Execute `run_OBPC.bat`
3. **URL:** http://127.0.0.1:5000
4. **Login inicial:**
   - **Usuário:** `admin`
   - **Senha:** `admin123`

### 📱 Interface do Sistema
- **Dashboard Principal:** Visão geral dos dados
- **Membros:** Cadastro e consulta de membros
- **Obreiros:** Gestão de liderança e ministérios
- **Departamentos:** Organização da igreja
- **Financeiro:** Controle completo de finanças

---

## 📦 Gerando Executável

### 🔧 Para distribuir o sistema:
1. **Execute o gerador:**
   ```bash
   build_EXE.bat
   ```

2. **Resultado:**
   - 📁 `dist/Sistema_OBPC.exe`
   - ✅ Executável independente
   - ✅ Não precisa Python instalado
   - ✅ Ícone personalizado da OBPC

### 💡 Distribuição
- Copie a pasta `dist` para qualquer computador
- Execute `Sistema_OBPC.exe` diretamente
- O sistema abre automaticamente no navegador

---

## 🛠️ Estrutura do Projeto

```
ERP_OBPC/
├── 📁 app/                     # Aplicação principal
│   ├── 📁 usuario/             # Módulo de autenticação
│   ├── 📁 membros/             # Gestão de membros
│   ├── 📁 obreiros/            # Gestão de obreiros
│   ├── 📁 departamentos/       # Gestão de departamentos
│   ├── 📁 financeiro/          # Controle financeiro
│   ├── 📁 utils/               # Utilitários (PDF, etc)
│   └── 📁 templates/           # Templates HTML
├── 📁 static/                  # Arquivos estáticos
│   ├── 🖼️ logo_obpc.ico       # Ícone do sistema
│   └── 🖼️ Logo_IBPC.jpg       # Logo da igreja
├── 📁 instance/                # Banco de dados
│   └── 🗃️ igreja.db            # SQLite database
├── 📄 requirements.txt         # Dependências Python
├── 🐍 run.py                   # Arquivo principal
├── ⚙️ install_OBPC.bat         # Instalador automático
├── 🔧 build_EXE.bat            # Gerador de executável
└── 📖 README.md                # Este arquivo
```

---

## 🎨 Características Técnicas

### 🔧 Tecnologias Utilizadas
- **Backend:** Python 3.10+ com Flask
- **Frontend:** Bootstrap 5 + FontAwesome
- **Banco:** SQLite (local)
- **PDFs:** ReportLab (relatórios profissionais)
- **APIs:** ViaCEP (busca de endereços)

### 🎯 Recursos Especiais
- **Responsivo:** Funciona em desktop, tablet e mobile
- **Offline:** Não precisa internet (exceto CEP)
- **Rápido:** Interface otimizada e moderna
- **Seguro:** Autenticação e validações
- **Profissional:** Relatórios PDF corporativos

---

## 📊 Módulos do Sistema

### 👥 Gestão de Membros
- Cadastro completo de membros
- Busca automática de endereço por CEP
- Histórico de atividades
- Relatórios de membros

### ⛪ Gestão de Obreiros
- Controle de ministérios
- Hierarquia de funções
- Histórico de cargos
- Relatórios de liderança

### 🏢 Gestão de Departamentos
- Organização por departamentos
- Responsáveis e coordenadores
- Atividades e projetos
- Relatórios departamentais

### 💰 Controle Financeiro
- **Entradas:** Dízimos, ofertas, doações
- **Saídas:** Despesas fixas e variáveis
- **Contas:** Dinheiro, banco, PIX
- **Relatórios:** Caixa interno e para sede
- **Análises:** Gráficos e percentuais

---

## 🔐 Segurança e Backup

### 🛡️ Segurança
- Autenticação obrigatória
- Senhas criptografadas
- Sessões seguras
- Validação de dados

### 💾 Backup
- **Banco de dados:** `instance/igreja.db`
- **Recomendação:** Backup semanal do arquivo
- **Restauração:** Copie o arquivo de volta

---

## 📞 Suporte e Contato

### 🏛️ Desenvolvido para:
**Igreja O Brasil para Cristo - Tietê/SP**

### 🤝 Suporte Técnico
- **Sistema:** Desenvolvido especificamente para OBPC
- **Instalação:** Siga os passos do README
- **Problemas:** Verifique os requisitos

### 📋 Requisitos Mínimos
- **SO:** Windows 10 ou superior
- **RAM:** 4GB mínimo
- **Espaço:** 500MB disponível
- **Python:** 3.10+ (instalado automaticamente)

---

## 🎉 Instalação Completa Realizada!

✅ **Sistema OBPC** está pronto para uso!

### 🚀 Próximos Passos:
1. Execute `install_OBPC.bat` para instalar
2. Acesse o sistema em http://127.0.0.1:5000
3. Faça login com admin/admin123
4. Configure os dados da sua igreja
5. Comece a usar o sistema!

### 💡 Dicas de Uso:
- Cadastre primeiro os departamentos
- Depois os obreiros e membros
- Configure as categorias financeiras
- Use os relatórios PDF para prestação de contas

---

*🙏 Sistema desenvolvido com carinho para a Igreja O Brasil para Cristo - Tietê/SP*