# ✅ CORREÇÃO DO CACHE DO LOGO - CONFIGURAÇÕES

## 🔍 Problema Identificado

Quando você editava as configurações e fazia upload de um novo logo, o sistema salvava corretamente, mas o navegador mantinha a imagem antiga em cache. Ao sair e voltar para a página, o logo antigo aparecia novamente.

## 🛠️ Solução Implementada

### 1. **Cache Busting com Timestamp**

Adicionamos um parâmetro de versão (timestamp) em todas as URLs das imagens do logo:

**Antes:**
```html
<img src="/static/logo_igreja.jpg">
```

**Depois:**
```html
<img src="/static/logo_igreja.jpg?v=1738483200.123456">
```

Cada vez que a configuração é atualizada, o timestamp muda, forçando o navegador a baixar a nova imagem.

### 2. **Arquivos Modificados**

#### ✅ `app/configuracoes/templates/configuracoes/configuracoes.html`

**Mudanças:**
1. **Linha 266** - Adicionado cache busting na exibição inicial do logo:
   ```html
   <img src="{{ url_for('static', filename=config.logo) }}?v={{ config.atualizado_em.timestamp() }}"
   ```

2. **Linha 267** - Adicionado ID específico para facilitar manipulação JavaScript:
   ```html
   id="logo_preview_img"
   ```

3. **Linha 738** - Corrigido seletor JavaScript de `querySelector` para `getElementById`:
   ```javascript
   const img = document.getElementById('logo_preview_img');
   ```

4. **Linhas 803-813** - Melhorada atualização após upload:
   ```javascript
   // Limpar cache e atualizar imagem
   img.src = '';
   setTimeout(() => {
       img.src = newSrc;
   }, 50);
   ```

5. **Linha 830** - Corrigida reversão em caso de erro com cache busting:
   ```javascript
   img.src = '{{ url_for("static", filename=config.logo) }}?v=' + timestamp;
   ```

#### ✅ `app/templates/base.html`

**Mudança:**
- **Linha 446** - Adicionado cache busting no logo do menu lateral:
  ```html
  <img src="{{ url_for('static', filename=igreja_config.logo) }}?v={{ igreja_config.atualizado_em.timestamp() }}">
  ```

### 3. **Como Funciona**

1. **Ao carregar a página:** O timestamp do campo `atualizado_em` é convertido em um número (ex: `1738483200.123456`)
2. **Esse número é anexado à URL:** `logo_igreja.jpg?v=1738483200.123456`
3. **Quando você faz upload de um novo logo:**
   - O backend salva o arquivo
   - Atualiza `config.atualizado_em` com a data/hora atual
   - O JavaScript força o reload da imagem com novo timestamp
4. **Quando você sai e volta:** O novo timestamp está no banco, então a URL é diferente, forçando o navegador a buscar a nova imagem

## ✅ Benefícios

- ✅ **Cache busting automático** - Não precisa limpar cache manualmente
- ✅ **Atualização imediata** - Logo muda na hora após upload
- ✅ **Persistência correta** - Ao recarregar a página, sempre mostra o logo correto
- ✅ **Performance mantida** - Cache ainda funciona até você trocar o logo
- ✅ **Funciona em todas as páginas** - Menu lateral também atualiza

## 🧪 Como Testar

1. Acesse **Configurações** → Aba **Gerais**
2. Faça upload de um novo logo
3. Verifique se a imagem muda imediatamente
4. **Saia da página** (vá para Painel)
5. **Volte para Configurações**
6. Verifique se o **novo logo está lá** (não o antigo)
7. Teste também no **menu lateral** - deve mostrar o novo logo

## 📝 Observações Técnicas

- O campo `atualizado_em` é atualizado automaticamente pelo método `salvar()` do modelo
- O SQLAlchemy já tem `onupdate=datetime.utcnow` configurado
- O timestamp é convertido via `.timestamp()` no Jinja2 para gerar um número único
- O parâmetro `?v=` não afeta o servidor, é apenas para o navegador

## 🎯 Resultado

Agora o logo será sempre atualizado corretamente, sem precisar limpar cache do navegador! 🎉
