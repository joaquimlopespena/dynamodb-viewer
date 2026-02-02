# Feature: Deleção em Lote de Itens

## Descrição
Agora é possível deletar múltiplos itens de uma vez no DynamoDB Viewer!

## Como Usar

### 1. Seleção Múltipla
- **Ctrl+Click**: Seleciona/deseleciona itens individuais
- **Shift+Click**: Seleciona um intervalo de itens contíguo
- **Ctrl+A**: Seleciona todos os itens

### 2. Deletar Vários Itens
1. Selecione os itens desejados usando Ctrl+Click ou Shift+Click
2. Clique no botão **"🗑️ Deletar Vários Itens"**
3. Uma janela de confirmação mostrará:
   - Quantidade de itens a deletar
   - Preview das chaves dos primeiros 5 itens
   - Aviso de que a ação é irreversível
4. Confirme a deleção

### 3. Deletar Um Item
Para deletar apenas um item:
1. Clique no item para selecioná-lo
2. Clique no botão **"🗑️ Deletar Item Selecionado"**
3. Confirme a deleção

## Recursos da Funcionalidade

✅ **Seleção múltipla intuitiva** - Use os atalhos padrão do sistema
✅ **Preview antes da deleção** - Veja quais itens serão deletados
✅ **Feedback de progresso** - Acompanhe o status da operação
✅ **Relatório de erros** - Saiba se algum item falhou na deleção
✅ **Atualização automática** - Contador de itens é atualizado
✅ **Dica visual** - Mensagem explicativa na interface

## Mudanças no Código

### Arquivo: `src/ui/windows/main_window.py`

**Alterações:**
1. Adicionado botão "Deletar Vários Itens" na seção de ações
2. Habilitado `selectmode='extended'` no Treeview para seleção múltipla
3. Nova função `delete_multiple_items()` que:
   - Valida seleção múltipla
   - Mostra preview dos itens a deletar
   - Deleta itens com feedback de progresso
   - Atualiza a UI com resultado da operação
4. Adicionado label informativo sobre atalhos de seleção

## Exemplo de Uso

```python
# Seleção múltipla com Ctrl+Click
# → Clique em um item
# → Mantenha Ctrl pressionado e clique em outros itens

# Intervalo com Shift+Click
# → Clique em um item
# → Mantenha Shift pressionado e clique em outro item
# → Todos os itens entre eles serão selecionados

# Depois de selecionar, clique em "Deletar Vários Itens"
```

## Tratamento de Erros

- Se nenhum item for selecionado, uma mensagem de aviso é exibida
- Se apenas um item estiver selecionado, sugere usar o botão de deleção única
- Se alguns itens falharem, um relatório é mostrado com os erros
- A UI é atualizada apenas com os itens deletados com sucesso

## Desempenho

A deleção é feita sequencialmente para evitar sobrecarga do DynamoDB e permitir feedback de progresso em tempo real.

## Compatibilidade

- Funciona com DynamoDB Local e AWS DynamoDB
- Mantém compatibilidade com a deleção de item único
- Respeita o mesmo esquema de chaves primárias
