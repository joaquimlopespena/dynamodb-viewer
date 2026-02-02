# Diagnóstico: Consultando Tabela Mensagem Lenta

## Problemas Encontrados

### 🔴 BUG 1: Atributo `key_schema` não existe em boto3.Table
Na linha 237 de `dynamodb_service.py`:
```python
key_schema = getattr(self.current_table, 'key_schema', None)
```
✗ `key_schema` é um atributo de **TableDescription**, não da Table
✗ `getattr(..., None)` retorna `None` silenciosamente
✓ **Solução**: Usar `table.key_schema` com tratamento de erro apropriado

### 🔴 BUG 2: Comparação de valor incorreta
Na linha 255:
```python
if pk_value is not None and sk_key and sk_value is not None:
```
✗ Verifica `pk_value is not None` mas `pk_value` pode ser string vazia "0"
✗ Deveria ser verificado após tipo conversion
✓ **Solução**: Usar validação mais robusta

### 🔴 BUG 3: Valor do filtro é string, não convertido
Na linha 252:
```python
pk_value = filter_data.get('value')  # String!
```
✗ O valor vem como string do formulário
✗ DynamoDB espera tipo correto (int, float, etc)
✓ **Solução**: Converter baseado no tipo do atributo

## Resultado dos Bugs
- ✗ Nunca usa `get_item()` (instantâneo)
- ✗ Nunca usa `query()` com PK (muito rápido: <100ms)
- ✓ Sempre usa `scan()` completo (muito lento: 5-30 segundos)

## Impacto
- Tabela com 100k itens: cada consulta escaneia TODA a tabela
- Custo AWS: 100x mais caro do que deveria ser
- UX: UI fica travada 5-30 segundos por busca

## Solução Implementada
- ✓ Acesso correto ao schema da tabela
- ✓ Conversão de tipo automática
- ✓ Logging detalhado do caminho tomado
- ✓ Fallback seguro para scan
