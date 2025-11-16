Atualização: Lista de Inventário - Botões e Ações

O que foi alterado:

1) Template `app/secretaria/inventario/templates/inventario/lista_itens.html`
   - Adicionados os botões por item para:
     - Visualizar (ícone eye)
     - Editar (ícone edit)
     - Gerar PDF do item (ícone file-pdf) -> chama `inventario.gerar_pdf_item`
     - Menu para alterar o "Estado de Conservação" (dropdown) -> envia POST para `inventario.atualizar_estado`
     - Inativar/Ativar
     - Excluir
   - O layout e comportamento seguem o padrão dos templates de `atas` e `oficios`.

2) Rotas adicionadas em `app/secretaria/inventario/inventario_routes.py`
   - `gerar_pdf_item(id)` - gera/retorna um PDF com os detalhes de um único item.
     - Usa WeasyPrint quando disponível; caso contrário usa ReportLab como fallback.
   - `atualizar_estado(id)` - rota POST que atualiza o campo `estado_conservacao` do item e persiste no banco.

3) Novo template `app/secretaria/inventario/templates/inventario/pdf_item.html`
   - Template simples para renderizar a ficha do item que é usada para gerar o PDF.

Como testar rapidamente (local):

1) Inicie o servidor:

```powershell
python run.py
```

2) Acesse a lista de inventário e verifique os botões por item:

- URL: http://127.0.0.1:5000/secretaria/inventario/lista

3) Teste Gerar PDF (por item):

- Clique no ícone de PDF ao lado de um item. O PDF deve abrir em nova aba.

4) Teste Alterar Estado:

- Clique no ícone de engrenagem e selecione um estado. A página será recarregada e deve exibir uma mensagem de sucesso.

Observações e próximos passos:

- A listagem de estados é baseada na variável `estados` passada pela rota `lista_itens` (['Novo','Bom','Regular','Ruim','Péssimo']).
- Se quiser que o botão de PDF abra um layout mais detalhado, podemos aprimorar `pdf_item.html` com logo/rodapé/assinaturas.
- Testes automatizados podem ser adicionados para validar as rotas e geração de PDF.

Se quiser, eu executo os testes funcionais agora (vou iniciar o servidor em background e fazer requisições para verificar PDF e atualização de estado).