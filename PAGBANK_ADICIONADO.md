# ✅ PagBank Adicionado às Configurações

## Modificação Realizada

**Data**: 29 de Novembro de 2025  
**Arquivo modificado**: `app/configuracoes/configuracoes_model.py`  
**Função**: `get_bancos_disponiveis()`

## Alteração

Adicionado "PagBank" à lista de bancos disponíveis nas configurações do sistema.

### Antes:
```python
return [
    'Caixa Econômica Federal',
    'Banco do Brasil',
    'Banco Santander',
    'Banco Itaú',
    'Banco Bradesco',
    'Nubank',
    'Banco Inter',
    'Banco Original',
    'Outros'
]
```

### Depois:
```python
return [
    'Caixa Econômica Federal',
    'Banco do Brasil',
    'Banco Santander',
    'Banco Itaú',
    'Banco Bradesco',
    'Nubank',
    'Banco Inter',
    'Banco Original',
    'PagBank',        # ✅ ADICIONADO
    'Outros'
]
```

## Onde o PagBank aparece agora:

1. **Configurações > Financeiro > Banco Padrão**: Dropdown com todos os bancos incluindo PagBank
2. **Importação de Extratos**: PagBank já estava disponível como "Extrato PagBank (.csv)"

## Teste Realizado

✅ Verificado que a lista retorna corretamente com PagBank incluído:
```bash
python -c "from app.configuracoes.configuracoes_model import Configuracao; print(Configuracao.get_bancos_disponiveis())"
```

## Resultado

O PagBank agora está disponível para seleção como banco padrão nas configurações administrativas do sistema.