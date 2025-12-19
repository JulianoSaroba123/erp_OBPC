# 📦 INSTALADOR OBPC - GUIA COMPLETO

## 🚀 Sistema de Instalação Rápida

Este projeto contém múltiplas opções de instalação para diferentes cenários:

### 📋 **Opções de Instalador Disponíveis**

#### 1. **InstalarOBPC.bat** ⚡ **(RECOMENDADO)**
- **Uso**: Instalação rápida em Windows
- **Interface**: CMD com cores e emojis
- **Funcionalidades**:
  - ✅ Detecção automática de Python
  - ✅ Verificação de primeira execução  
  - ✅ Instalação automática ou inicialização direta
  - ✅ Interface amigável no terminal

**Como usar:**
```cmd
# Clique duplo no arquivo ou execute:
InstalarOBPC.bat
```

#### 2. **instalador_rapido.py** 🎨
- **Uso**: Interface gráfica moderna
- **Interface**: Tela de splash profissional
- **Funcionalidades**:
  - ✅ Tela de loading com barra de progresso
  - ✅ Instalação automática silenciosa
  - ✅ Abertura automática do navegador
  - ✅ Design com cores da igreja (verde/dourado)

**Como usar:**
```cmd
python instalador_rapido.py
```

#### 3. **instalador_gui.py** 🛠️
- **Uso**: Instalador completo com opções
- **Interface**: GUI completa com configurações
- **Funcionalidades**:
  - ✅ Escolha do diretório de instalação
  - ✅ Opções de configuração
  - ✅ Criação de atalhos
  - ✅ Instalação personalizada

**Como usar:**
```cmd
python instalador_gui.py
```

#### 4. **Gerador de Executável** 📱
- **Arquivo**: `gerar_instalador_executavel.py`
- **Finalidade**: Criar instalador .EXE para distribuição
- **Funcionalidades**:
  - ✅ Auto-extração
  - ✅ Sem dependências externas
  - ✅ Instalador único para máquinas sem Python

---

## 🎯 **Para Diferentes Cenários**

### 🏠 **Instalação Local (Desenvolvimento)**
```cmd
# Método mais rápido
InstalarOBPC.bat
```

### 🏢 **Instalação em Máquina da Igreja**
```cmd
# Com interface amigável
python instalador_rapido.py
```

### 💾 **Distribuição para Outras Igrejas**
```cmd
# Gerar executável primeiro
python gerar_instalador_executavel.py

# Distribuir o arquivo .exe gerado
```

---

## ⚙️ **Requisitos do Sistema**

### Mínimos:
- **SO**: Windows 7/10/11
- **Python**: 3.8+ (instalado automaticamente se necessário)
- **RAM**: 2GB
- **Espaço**: 500MB

### Recomendados:
- **SO**: Windows 10/11
- **Python**: 3.9+
- **RAM**: 4GB
- **Espaço**: 1GB

---

## 🔧 **Configuração Automática**

Todos os instaladores executam automaticamente:

1. **Verificação de Python** 🐍
2. **Instalação de dependências** 📦
   - Flask
   - SQLAlchemy
   - ReportLab
   - Outros pacotes necessários
3. **Criação do banco SQLite** 🗄️
4. **Configuração do usuário admin** 👤
5. **Inicialização do sistema** 🚀

### 👤 **Login Padrão**
- **Usuário**: `admin@obpc.com`
- **Senha**: `admin123`
- **⚠️ IMPORTANTE**: Altere a senha no primeiro acesso!

---

## 🌐 **Acesso ao Sistema**

Após a instalação:
- **URL Local**: http://localhost:5000
- **URL da Rede**: http://[IP-DA-MÁQUINA]:5000

---

## 📁 **Estrutura de Arquivos**

```
OBPC_Sistema/
├── app/                    # Aplicação principal
├── static/                 # Arquivos estáticos
├── instance/              # Banco de dados
├── run.py                 # Inicializador
├── requirements.txt       # Dependências
├── InstalarOBPC.bat      # Instalador rápido
└── instalador_*.py       # Instaladores GUI
```

---

## 🆘 **Solução de Problemas**

### Python não encontrado
```cmd
# Baixar e instalar Python:
https://python.org/downloads/
# Marcar "Add to PATH" durante instalação
```

### Erro de permissão
```cmd
# Executar como Administrador
# Botão direito > "Executar como administrador"
```

### Porta 5000 ocupada
```cmd
# Finalizar processos conflitantes
taskkill /F /IM python.exe
```

### Banco de dados corrompido
```cmd
# Deletar e recriar
del instance\igreja.db
python verificar_banco.py
```

---

## 🔄 **Atualizações**

Para atualizar o sistema:
1. Fazer backup do banco (`instance/igreja.db`)
2. Substituir arquivos da aplicação
3. Executar `InstalarOBPC.bat` novamente

---

## 📞 **Suporte**

- **Igreja**: O Brasil Para Cristo - Tietê/SP
- **Sistema**: OBPC v2.0
- **Última atualização**: Outubro 2025

---

## 🎨 **Personalização**

Para adaptar para sua igreja:
1. Editar `app/templates/base.html` (logo e cores)
2. Substituir `static/logo_obpc.ico`
3. Atualizar informações em `app/config.py`

---

## 📝 **Changelog**

### v2.0 (Outubro 2025)
- ✅ Sistema de filtros avançados
- ✅ Interface responsiva
- ✅ Relatórios profissionais
- ✅ Instaladores múltiplos
- ✅ Barra de rolagem otimizada

### v1.0 (Base)
- ✅ Sistema básico de gestão
- ✅ Controle financeiro
- ✅ Cadastro de membros
- ✅ Relatórios básicos