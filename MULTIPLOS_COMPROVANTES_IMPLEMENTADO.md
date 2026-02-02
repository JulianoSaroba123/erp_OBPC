# ✅ MÚLTIPLOS COMPROVANTES - LANÇAMENTOS FINANCEIROS

## 🎯 Implementação Concluída

Sistema atualizado para permitir **upload de múltiplos comprovantes** por lançamento financeiro.

---

## 📋 O QUE FOI IMPLEMENTADO

### 1. **Novo Modelo de Dados**
- ✅ Criada tabela `comprovantes` com os campos:
  - `id` - Identificador único
  - `lancamento_id` - Referência ao lançamento
  - `arquivo` - Caminho do arquivo
  - `nome_original` - Nome original do arquivo
  - `tamanho` - Tamanho em bytes
  - `tipo_mime` - Tipo MIME (image/jpeg, application/pdf, etc.)
  - `criado_em` - Data de upload

### 2. **Relacionamento com Lançamentos**
- ✅ Modelo `Lancamento` atualizado com relacionamento `comprovantes`
- ✅ Suporte para comprovantes legados (campo antigo) e novos (tabela)
- ✅ Método `total_comprovantes()` para contar todos os comprovantes

### 3. **Novas Rotas Criadas**

#### ✅ Upload de Múltiplos Comprovantes
```
POST /financeiro/upload-comprovantes/<id>
```
- Permite selecionar e enviar múltiplos arquivos de uma vez
- Validação automática de formato (JPG, PNG, PDF)
- Nome único gerado para cada arquivo (evita conflitos)

#### ✅ Exclusão Individual
```
POST /financeiro/excluir-comprovante-multiplo/<comprovante_id>
```
- Exclui arquivo físico e registro do banco
- Remove apenas o comprovante selecionado

### 4. **Interface Atualizada**

**Recursos visuais:**
- ✅ **Comprovante Principal** - Exibe o comprovante legado (se existir)
- ✅ **Lista de Comprovantes Adicionais** - Card com todos os arquivos
- ✅ **Ícones diferenciados** - Imagem 🖼️ / PDF 📄
- ✅ **Informações detalhadas** - Nome, tamanho, data de upload
- ✅ **Seleção múltipla** - Input com atributo `multiple`
- ✅ **Botões de ação** - Visualizar (abre em nova aba) / Excluir

---

## 🚀 COMO USAR

### **Passo a Passo:**

1. **Acesse um Lançamento Existente**
   - Vá em **Financeiro** → **Lançamentos**
   - Clique em **Editar** em qualquer lançamento

2. **Adicione Múltiplos Comprovantes**
   - Role até a seção **"Comprovantes"**
   - Clique no botão **"Escolher arquivos"**
   - **Selecione múltiplos arquivos** (use Ctrl+Click ou Shift+Click)
   - Clique em **"Adicionar Comprovantes"**

3. **Visualize os Comprovantes**
   - Veja a lista de todos os arquivos enviados
   - Clique no nome do arquivo para **visualizar/baixar**
   - Veja informações de **tamanho** e **data de upload**

4. **Exclua Comprovantes Individualmente**
   - Clique no botão **🗑️ de excluir** ao lado de cada arquivo
   - Confirme a exclusão

---

## 📦 ARQUIVOS CRIADOS/MODIFICADOS

### ✅ **Arquivos Criados:**
1. `app/financeiro/comprovante_model.py` - Modelo de comprovantes
2. `criar_tabela_comprovantes.py` - Script de migração

### ✅ **Arquivos Modificados:**
1. `app/financeiro/financeiro_model.py` - Relacionamento adicionado
2. `app/financeiro/financeiro_routes.py` - Novas rotas de upload/exclusão
3. `app/financeiro/templates/financeiro/cadastro_lancamento.html` - Interface atualizada

---

## ✨ FUNCIONALIDADES

| Recurso | Status |
|---------|--------|
| Upload de múltiplos arquivos simultâneos | ✅ |
| Suporte para JPG, PNG, PDF | ✅ |
| Visualização de comprovantes | ✅ |
| Exclusão individual de comprovantes | ✅ |
| Informações de tamanho e tipo | ✅ |
| Ícones diferenciados por tipo | ✅ |
| Compatibilidade retroativa (campo legado) | ✅ |
| Validação de formato de arquivo | ✅ |
| Nome único para evitar conflitos | ✅ |

---

## 🔒 SEGURANÇA

- ✅ **Validação de extensão** - Apenas JPG, PNG, PDF permitidos
- ✅ **Nome seguro** - `secure_filename()` aplicado
- ✅ **UUID único** - Evita sobrescrever arquivos
- ✅ **Login obrigatório** - Todas as rotas protegidas com `@login_required`

---

## 📊 ESTRUTURA DO BANCO

```sql
CREATE TABLE comprovantes (
    id INTEGER PRIMARY KEY,
    lancamento_id INTEGER NOT NULL,
    arquivo VARCHAR(300) NOT NULL,
    nome_original VARCHAR(255),
    tamanho INTEGER,
    tipo_mime VARCHAR(100),
    criado_em DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (lancamento_id) REFERENCES lancamentos(id) ON DELETE CASCADE
);
```

---

## 💡 OBSERVAÇÕES

### **Comprovante Legado**
O campo `comprovante` antigo na tabela `lancamentos` foi **mantido** para compatibilidade. Se um lançamento já tinha um comprovante, ele aparecerá como **"Comprovante Principal"**.

### **Cascata de Exclusão**
Ao excluir um lançamento, todos os comprovantes associados são **automaticamente excluídos** do banco e do sistema de arquivos.

### **Limite de Tamanho**
O tamanho máximo por arquivo é controlado pelo servidor web (geralmente 5MB). Para aumentar, configure no Flask:
```python
app.config['MAX_CONTENT_LENGTH'] = 10 * 1024 * 1024  # 10MB
```

---

## 🧪 TESTE AGORA!

1. Vá em **Financeiro** → **Lançamentos**
2. Edite qualquer lançamento
3. Adicione **vários comprovantes de uma vez**
4. Veja a lista completa com ícones e informações
5. Exclua e adicione conforme necessário

---

## ✅ PRONTO PARA USO!

O sistema agora suporta **múltiplos comprovantes** por lançamento, facilitando a organização da documentação financeira da igreja! 🎉

**Desenvolvido para:** Igreja O Brasil para Cristo - Tietê/SP  
**Data:** 02/02/2026
