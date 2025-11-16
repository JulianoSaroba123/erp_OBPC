# 🏛️ Módulos de Secretaria - Sistema OBPC

## 📋 Visão Geral

Dois novos módulos completos foram implementados na aba **Secretaria** do Sistema OBPC:

1. **📄 Atas de Reunião** - Gestão completa de atas com geração de PDF profissional
2. **📦 Inventário Patrimonial** - Controle total do patrimônio da igreja com relatórios

---

## 🎯 1. MÓDULO - Atas de Reunião

### ✨ Funcionalidades
- ✅ **CRUD Completo**: Criar, Listar, Editar, Excluir atas
- ✅ **Geração de PDF**: Layout institucional profissional 
- ✅ **Busca Avançada**: Por título, responsável ou local
- ✅ **Histórico**: Controle cronológico de todas as atas
- ✅ **Download**: PDFs arquivados automaticamente

### 🗂️ Campos da Ata
| Campo | Tipo | Obrigatório | Descrição |
|-------|------|-------------|-----------|
| **Título** | Texto | ✅ | Nome da reunião/assembleia |
| **Data** | Data | ✅ | Data de realização |
| **Local** | Texto | ❌ | Local onde foi realizada |
| **Responsável** | Texto | ❌ | Quem conduziu a reunião |
| **Descrição** | Texto Longo | ❌ | Conteúdo detalhado da ata |

### 🔗 Rotas Implementadas
- `GET /secretaria/atas` → Lista todas as atas
- `GET /secretaria/atas/nova` → Formulário de cadastro
- `GET /secretaria/atas/editar/<id>` → Formulário de edição
- `POST /secretaria/atas/salvar` → Salvar ata (nova/edição)
- `GET /secretaria/atas/pdf/<id>` → Gerar/baixar PDF
- `POST /secretaria/atas/excluir/<id>` → Excluir ata

### 📄 Layout do PDF
```
ORGANIZAÇÃO BATISTA PEDRA DE CRISTO
Rua das Flores, 123 - Tietê - SP
CNPJ: 12.345.678/0001-99
═══════════════════════════════════
        ATA DE REUNIÃO

Título: [Título da Reunião]
Data: [DD/MM/AAAA]    Local: [Local]
Responsável: [Nome do Responsável]

[Conteúdo da descrição formatado...]

_______________________________     _______________________________
        Pastor João Silva                    Maria Santos
         Dirigente                          Tesoureiro

_______________________________
    [Responsável da Reunião]
   Presidente da Reunião
```

---

## 📦 2. MÓDULO - Inventário Patrimonial

### ✨ Funcionalidades
- ✅ **CRUD Completo**: Cadastrar, Listar, Editar, Excluir itens
- ✅ **Filtros Avançados**: Por categoria, estado, status, busca textual
- ✅ **Controle de Status**: Ativar/Inativar itens sem excluir
- ✅ **Relatório PDF**: Inventário completo por categoria
- ✅ **Estatísticas**: Valor total, quantidades por tipo
- ✅ **Responsabilidade**: Controle de responsável por item

### 🏷️ Campos do Item
| Campo | Tipo | Obrigatório | Descrição |
|-------|------|-------------|-----------|
| **Código** | Texto | ✅ | Código único (ex: MOV001) |
| **Nome** | Texto | ✅ | Nome descritivo do item |
| **Categoria** | Lista | ✅ | Categoria predefinida |
| **Descrição** | Texto Longo | ❌ | Detalhes técnicos |
| **Valor** | Decimal | ❌ | Valor de aquisição |
| **Data Aquisição** | Data | ❌ | Quando foi adquirido |
| **Estado** | Lista | ✅ | Conservação atual |
| **Localização** | Texto | ❌ | Onde está localizado |
| **Responsável** | Texto | ❌ | Quem é responsável |
| **Observações** | Texto Longo | ❌ | Informações extras |
| **Ativo** | Boolean | ✅ | Se está em uso |

### 📂 Categorias Disponíveis
1. **Móveis e Utensílios**
2. **Equipamentos de Som e Imagem**
3. **Instrumentos Musicais**
4. **Equipamentos de Informática**
5. **Veículos**
6. **Eletrodomésticos**
7. **Livros e Materiais**
8. **Decoração e Arte**
9. **Ferramentas e Equipamentos**
10. **Outros**

### 🎚️ Estados de Conservação
- 🟢 **Excelente** - Como novo
- 🔵 **Bom** - Funcionando perfeitamente
- 🟡 **Regular** - Pequenos desgastes
- 🟠 **Ruim** - Necessita manutenção
- 🔴 **Péssimo** - Inutilizável

### 🔗 Rotas Implementadas
- `GET /secretaria/inventario` → Lista itens (com filtros)
- `GET /secretaria/inventario/novo` → Formulário cadastro
- `GET /secretaria/inventario/editar/<id>` → Formulário edição
- `POST /secretaria/inventario/salvar` → Salvar item
- `POST /secretaria/inventario/excluir/<id>` → Excluir item
- `POST /secretaria/inventario/inativar/<id>` → Ativar/Inativar
- `GET /secretaria/inventario/pdf` → Relatório PDF completo

---

## 🎨 Interface do Usuário

### 🧭 Menu de Navegação
```
📁 Secretaria
├── 👥 Membros
├── 👔 Obreiros  
├── 👑 Líderes
├── 📄 Atas de Reunião    ← NOVO
└── 📦 Inventário         ← NOVO
```

### 🔍 Filtros do Inventário
- **Busca Textual**: Código, nome, descrição, responsável
- **Categoria**: Todas as categorias disponíveis
- **Estado**: Todos os estados de conservação
- **Status**: Ativos, Inativos, Todos

### 📊 Dashboard do Inventário
- 📦 **Total de Itens** - Quantidade absoluta
- ✅ **Itens Ativos** - Em uso na igreja
- 💰 **Valor Total** - Soma dos valores ativos
- 🔍 **Resultados** - Items filtrados

---

## 🛠️ Configuração Técnica

### 📦 Dependências Adicionadas
```txt
weasyprint==61.2  # Para geração de PDFs
```

### 🗄️ Modelos de Banco
```python
# Tabela: atas
class Ata(db.Model):
    id, titulo, data, local, responsavel, 
    descricao, arquivo, criado_em

# Tabela: inventario  
class ItemInventario(db.Model):
    id, codigo, nome, categoria, descricao,
    valor_aquisicao, data_aquisicao, estado_conservacao,
    localizacao, responsavel, observacoes, ativo,
    criado_em, atualizado_em
```

### 📁 Estrutura de Arquivos
```
app/secretaria/
├── __init__.py
├── atas/
│   ├── __init__.py
│   ├── atas_model.py
│   ├── atas_routes.py
│   └── templates/atas/
│       ├── lista_atas.html
│       ├── cadastro_ata.html
│       └── pdf_ata.html
└── inventario/
    ├── __init__.py
    ├── inventario_model.py
    ├── inventario_routes.py
    └── templates/inventario/
        ├── lista_itens.html
        ├── cadastro_item.html
        └── pdf_inventario.html

app/static/
├── atas/          ← PDFs das atas
└── inventario/    ← PDFs do inventário
```

---

## 🚀 Como Usar

### 1️⃣ **Atas de Reunião**
1. Acesse **Secretaria > Atas de Reunião**
2. Clique **"Nova Ata"**
3. Preencha título e data (obrigatórios)
4. Adicione local, responsável e conteúdo
5. Clique **"Salvar Ata"**
6. Use **"Gerar PDF"** para criar documento oficial

### 2️⃣ **Inventário Patrimonial**
1. Acesse **Secretaria > Inventário**
2. Clique **"Novo Item"**
3. Defina código único (ex: MOV001)
4. Preencha nome e categoria (obrigatórios)
5. Complete demais campos conforme necessário
6. Marque como **"Ativo"** se em uso
7. Use filtros para localizar itens específicos
8. Gere **"PDF Completo"** para relatório geral

### 3️⃣ **Geração de Relatórios**
- **PDFs Individuais**: Cada ata gera seu PDF próprio
- **Relatório de Inventário**: PDF com todos itens ativos por categoria
- **Arquivos Salvos**: PDFs ficam em `/app/static/atas/` e `/app/static/inventario/`

---

## 📋 Dados de Exemplo

Execute o script para criar dados de teste:
```bash
python criar_dados_secretaria.py
```

**Dados criados:**
- 📄 **3 Atas**: Reunião de Diretoria, Assembleia, Conselho de Obreiros
- 📦 **10 Itens**: Móveis, equipamentos de som, instrumentos, informática, eletrodomésticos
- 💰 **Valor Total**: R$ 16.960,00 em patrimônio

---

## 🎯 Próximos Passos

1. **Teste os Módulos**: Acesse as novas funcionalidades
2. **Gere PDFs**: Teste a geração de documentos
3. **Customize**: Ajuste categorias conforme necessidade
4. **Treine Usuários**: Capacite a equipe para usar as novas ferramentas
5. **Backup**: Configure backup automático dos PDFs gerados

---

## ✅ Status de Implementação

| Módulo | Status | CRUD | PDF | Filtros | Menu |
|--------|--------|------|-----|---------|------|
| **Atas de Reunião** | ✅ Completo | ✅ | ✅ | ✅ | ✅ |
| **Inventário** | ✅ Completo | ✅ | ✅ | ✅ | ✅ |

🎉 **Implementação 100% concluída e testada!**