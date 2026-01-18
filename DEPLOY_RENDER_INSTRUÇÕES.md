# 🚀 Deploy das Novas Alterações no Render

## ✅ Alterações Prontas para Deploy

As seguintes atualizações foram enviadas para o GitHub e estão prontas para deploy:

### 📋 Novos Campos no Cadastro de Membros:
1. **CPF** - Com máscara automática
2. **Número e Bairro** - Endereço completo
3. **Estado Civil** - Solteiro, Casado, Divorciado, Viúvo
4. **Formação Teológica**:
   - Curso de Teologia (Sim/Não)
   - Nível (Básico, Médio, Pleno)
   - Instituto (nome do seminário)
5. **Interesse de Serviço**:
   - Deseja Servir (Sim/Não)
   - Área de Serviço (ministério de interesse)

### 🔧 Correções:
- Decoradores de autenticação agora retornam JSON em requisições AJAX
- Correção do erro "Erro ao excluir usuário"

---

## 📝 Passos para Deploy no Render

### Opção 1: Deploy Automático (Recomendado)

Se você configurou o Render para fazer deploy automático do GitHub:

1. ✅ **Já está feito!** - O código foi enviado para o GitHub
2. ⏳ Aguarde alguns minutos
3. 🔍 Acesse o painel do Render em: https://dashboard.render.com
4. 📊 Verifique o status do deploy em andamento
5. ✅ Quando o deploy terminar, execute o script de atualização do banco

### Opção 2: Deploy Manual

Se precisar fazer deploy manual:

1. 🌐 Acesse: https://dashboard.render.com
2. 🔍 Encontre o serviço "sistema-obpc"
3. 🔄 Clique em **"Manual Deploy"** → **"Deploy latest commit"**
4. ⏳ Aguarde o build completar

---

## 🗄️ Atualizar Banco de Dados no Render

**IMPORTANTE:** Após o deploy, você precisa adicionar as novas colunas no banco PostgreSQL.

### Via Shell do Render:

1. 🌐 Acesse https://dashboard.render.com
2. 🔍 Selecione seu serviço "sistema-obpc"
3. 💻 No menu lateral, clique em **"Shell"**
4. ⌨️ Execute o comando:
   ```bash
   python atualizar_membros_render.py
   ```
5. ✅ Aguarde a confirmação das colunas adicionadas

### Saída Esperada:
```
============================================================
🔧 ATUALIZAÇÃO DA TABELA MEMBROS - RENDER
============================================================
🔗 Conectando ao banco de dados do Render...

📋 Verificando e adicionando campos na tabela membros...
   ✅ 📋 CPF (cpf) adicionado
   ✅ 🏠 Número (numero) adicionado
   ✅ 🏘️ Bairro (bairro) adicionado
   ✅ 💍 Estado Civil (estado_civil) adicionado
   ✅ 🎓 Curso de Teologia (curso_teologia) adicionado
   ✅ 📚 Nível de Teologia (nivel_teologia) adicionado
   ✅ 🏫 Instituto (instituto) adicionado
   ✅ 🙏 Deseja Servir (deseja_servir) adicionado
   ✅ ⛪ Área de Serviço (area_servir) adicionado

✅ Atualização concluída com sucesso!
============================================================
```

---

## 🔍 Verificar o Deploy

Após completar os passos acima:

1. 🌐 Acesse seu sistema no Render (URL do seu app)
2. 🔐 Faça login
3. 👥 Vá em **Gerenciar Usuários** ou **Membros**
4. ➕ Clique em **Novo Membro**
5. ✅ Verifique se os novos campos estão aparecendo:
   - CPF
   - Número e Bairro
   - Estado Civil
   - Curso de Teologia (com campos condicionais)
   - Deseja Servir (com campo condicional)

---

## ⚠️ Troubleshooting

### Se o deploy falhar:

1. 📋 Verifique os logs no painel do Render
2. 🔍 Procure por erros de dependências ou build
3. ✅ Certifique-se que o `requirements.txt` está atualizado

### Se as colunas não forem adicionadas:

1. ✅ Verifique se executou o script `atualizar_membros_render.py`
2. 🔍 Verifique os logs do Shell no Render
3. 📊 Confirme que a variável `DATABASE_URL` está configurada

### Se aparecer erro 500:

1. 🔍 Verifique os logs da aplicação
2. ✅ Certifique-se que as migrations foram executadas
3. 🔄 Tente reiniciar o serviço

---

## 📞 Suporte

Se encontrar problemas:
- 📋 Verifique os logs no Render Dashboard
- 🔍 Confirme que todas as variáveis de ambiente estão configuradas
- ✅ Certifique-se que o PostgreSQL está acessível

---

## ✅ Checklist Final

- [ ] Código enviado para GitHub
- [ ] Deploy concluído no Render (automático ou manual)
- [ ] Script `atualizar_membros_render.py` executado
- [ ] Novos campos visíveis no formulário
- [ ] Teste de cadastro realizado
- [ ] Dados sendo salvos corretamente

**Data do Deploy:** ___/___/______

**Responsável:** _________________

---

🎉 **Pronto!** Seu sistema está atualizado com todas as novas funcionalidades!
