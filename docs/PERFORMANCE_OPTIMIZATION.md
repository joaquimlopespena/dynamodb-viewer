# 🚀 Otimizações de Performance - Tabela "message" em Produção

## 🔴 Problemas Identificados

### 1. **Full Table Scan (O MAIOR PROBLEMA)**
**Localização**: [src/services/dynamodb_service.py](src/services/dynamodb_service.py#L430-L460)

**Problema**: Quando não há chave primária ou índice, o código faz um **full table scan**:
```python
# Linha 430 - MUITO LENTO!
while len(items) < limit:
    scan_kwargs = {'Limit': page_size}
    if filter_expr is not None:
        scan_kwargs['FilterExpression'] = filter_expr
    page = self.current_table.scan(**scan_kwargs)  # ❌ Varre TODA a tabela!
```

**Impacto**: 
- Se `message` tem 1M+ items, ele varre até encontrar limite (muito custoso)
- Cada página scanneia 500 itens
- `ScannedCount >> ReturnedCount` = muita banda e throughput desperdiçado

**Solução**: 
- ✅ Detectar automaticamente a chave primária
- ✅ Usar `query()` ao invés de `scan()`
- ✅ Obrigatoriamente usar um índice se disponível

---

### 2. **Limite Padrão Muito Alto**
**Localização**: [src/ui/windows/main_window.py](src/ui/windows/main_window.py#L180)

**Problema**: O limite padrão é 100 itens, mas em tabelas grandes isso significa:
- 100 itens × 10KB média = 1MB lido (pode ser 10-20MB com scans)
- Timeout em queries lentas

**Solução**: 
- ✅ Reduzir limite padrão para 20-50
- ✅ Adicionar paginação manual
- ✅ Avisar ao usuário quando resultado será lento

---

### 3. **Falta de Índices Globais (GSI)**
**Localização**: [src/services/dynamodb_service.py](src/services/dynamodb_service.py#L274-L340)

**Problema**: Se não há GSI em `sender_id`, `timestamp`, `thread_id`, etc., qualquer filtro é slow:
```python
# Sem GSI em sender_id:
WHERE sender_id = 'user123'  # Full table scan!
```

**Solução**:
- ✅ Criar GSI em atributos frequentemente filtrados
- ✅ Detectar automaticamente GSI disponíveis
- ✅ Avisar quando query vai ser lenta (sem índice)

---

### 4. **Projeção de Atributos Ineficiente**
**Localização**: [src/services/dynamodb_service.py](src/services/dynamodb_service.py#L304-L320)

**Problema**: Retorna TODOS os atributos de cada item:
```python
# known_attributes = TODOS (potencialmente 50+ campos)
# Se message tem documentos com 100KB cada:
100 items × 100KB = 10MB transferência!
```

**Solução**:
- ✅ Usar `ProjectionExpression` para retornar apenas colunas visíveis
- ✅ Compress dados em transferência
- ✅ Permitir lazy-loading de atributos

---

### 5. **Sem Cache de Resultados**
**Localização**: [src/ui/windows/main_window.py](src/ui/windows/main_window.py#L436-L460)

**Problema**: A mesma query é executada múltiplas vezes se usuário clicar "Executar" 2x:
```python
# Sem cache, cada clique = nova query custosa!
```

**Solução**:
- ✅ Cachear últimas queries (TTL 5min)
- ✅ Detectar queries idênticas
- ✅ Indicar para usuário quando está usando cache

---

### 6. **Conversão JSON Ineficiente**
**Localização**: [src/services/dynamodb_service.py](src/services/dynamodb_service.py#L446)

**Problema**: Converte Decimal → float para TODOS os itens:
```python
items_json = json.loads(json.dumps(items, cls=DecimalEncoder))
# Em 100 items × 50 campos = 5000 conversões!
```

**Solução**:
- ✅ Lazy-loading de conversão (só when displayed)
- ✅ Usar custom serializer na UI

---

## ✅ Recomendações Imediatas (Impacto Alto)

### 1. Criar Índices (ANTES DE TUDO!)
```bash
# Para tabela "message", criar GSI para:
aws dynamodb create-global-secondary-index \
  --table-name message \
  --attribute-definitions AttributeName=sender_id,AttributeType=S \
  --global-secondary-indexes "[{
    'IndexName': 'sender_id-timestamp-index',
    'KeySchema': [
      {'AttributeName': 'sender_id', 'KeyType': 'HASH'},
      {'AttributeName': 'timestamp', 'KeyType': 'RANGE'}
    ],
    'Projection': {'ProjectionType': 'KEYS_ONLY'},
    'BillingMode': 'PAY_PER_REQUEST'
  }]"
```

**Por quê?**
- `KEYS_ONLY` retorna apenas chaves primárias (muito mais rápido)
- Depois busca items completos via `get_item()` (paralelo)
- Reduz throughput de 10MB/s para 100KB/s

---

### 2. Adicionar Heurística de Detecção de Query Lenta
[src/services/dynamodb_service.py](src/services/dynamodb_service.py#L435-L460)

```python
def query_with_filters(self, filters, limit=100, ...):
    # Detectar se vai ser lento:
    if not has_pk_filter and not has_index_filter:
        print("⚠️ AVISO: Query vai fazer full table scan!")
        print(f"   Isso pode demorar {estimated_minutes}min para tabela com {item_count} items")
        print("   Considere criar um índice em:", suggested_attributes)
```

---

### 3. Reduzir Limite Padrão
Mudar de 100 para 20 itens:
```python
# main_window.py linha 180
self.limit_var.set(20)  # era 100
```

---

### 4. Implementar Paginação Manual
Adicionar botões "Próxima página" / "Anterior":
```python
def next_page(self):
    self.last_evaluated_key = current_page['LastEvaluatedKey']
    self.execute_filters()
```

---

## 📊 Benchmark Esperado

| Operação | Antes | Depois | Melhoria |
|----------|-------|--------|----------|
| Query com filtro (sem índice) | 30-60s | 3-5s | **10-20x** ❌ → ✅ |
| Query com GSI (KEYS_ONLY) | 30-60s | 0.5-1s | **50-60x** |
| Retornar 100 items | 10MB | 100KB | **100x** |
| Full table scan | 60min+ | N/A | N/A (use índice!) |

---

## 🛠️ Próximas Ações (Ordem de Impacto)

1. **[CRÍTICO]** Criar GSI em `sender_id`, `timestamp`, `thread_id`
2. **[ALTO]** Implementar `ProjectionExpression` para não buscar todos os campos
3. **[ALTO]** Reduzir limite padrão de 100 → 20
4. **[MÉDIO]** Adicionar avisos de query lenta
5. **[MÉDIO]** Implementar paginação manual
6. **[BAIXO]** Adicionar cache de resultados

---

## 🎯 Teste de Validação

Depois de implementar as otimizações, executar:

```bash
# Teste de query com índice
time python3 -c "
from src.services.dynamodb_service import DynamoDBService
db = DynamoDBService()
db.connect()
db.select_table('message')
# Query com índice
items, scanned, elapsed = db.query_with_filters([
    {'attribute': 'sender_id', 'condition': 'Igual a', 'value': 'user123'}
], limit=20)
print(f'Tempo: {elapsed}s, Scanned: {scanned}, Retornados: {len(items)}')
"
```

**Esperado**: `Tempo: <1s, Scanned: ~20, Retornados: 20`

---

## 📝 Notas

- Em produção, **SEMPRE preferir query() sobre scan()**
- Se não temos índice, consider async batch fetching
- Considerar DynamoDB Streams para cache invalidation
- Usar DAX (DynamoDB Accelerator) se disponível
