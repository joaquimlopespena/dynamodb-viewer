# 🎯 Guia Rápido - Como Pesquisar na Interface

## Baseado na sua tela:

```
┌─────────────────────────────────────────────────────┐
│ Tabelas DynamoDB        │ 📋 Dados  🔍 Query  ℹ Info │
├─────────────────────────────────────────────────────┤
│ □ Atualizar            │ Query/Scan                  │
│                        │                             │
│ ☑ audiocall-chat...    │ Operação: ◉ Scan  ○ Query │
│   channels             │                             │
│   chatbot-ia-analyti...│ Filter Expression:          │
│   chatbot-ia-analyti...│ [___________________]       │
│   ...                  │                             │
│                        │ Key Condition (Query):      │
│ ✓ Conectado           │ [___________________]       │
│                        │                             │
│                        │          [▶ Executar]       │
│                        │                             │
│                        │ Resultado:                  │
│                        │ [                         ] │
│                        │ [                         ] │
└─────────────────────────────────────────────────────┘
```

---

## ⚡ Como Usar - 3 Passos

### 1️⃣ Selecione uma Tabela
Clique em uma tabela no painel esquerdo (ex: "channels")

### 2️⃣ Configure a Busca

**Opção A - Buscar Tudo (Scan Simples):**
- ✅ Deixe **Scan** selecionado
- ✅ Deixe campos vazios
- ✅ Clique **▶ Executar**

**Opção B - Buscar com Filtro:**
- ✅ Deixe **Scan** selecionado
- ✅ No campo "Filter Expression", digite:
  ```
  attribute_exists(email)
  ```
- ✅ Clique **▶ Executar**

### 3️⃣ Veja o Resultado
Os dados aparecem na área "Resultado" em formato JSON

---

## 📝 Exemplos Práticos

### Exemplo 1: Ver Todos os Channels
```
1. Selecione tabela: "channels"
2. Operação: Scan
3. Filter Expression: (vazio)
4. Clique: ▶ Executar
```

### Exemplo 2: Ver Items com Campo "userId"
```
1. Selecione uma tabela
2. Operação: Scan
3. Filter Expression: attribute_exists(userId)
4. Clique: ▶ Executar
```

### Exemplo 3: Ver Items Não Deletados
```
1. Selecione uma tabela
2. Operação: Scan
3. Filter Expression: attribute_not_exists(deletedAt)
4. Clique: ▶ Executar
```

---

## 🎓 Filtros que Funcionam

✅ **ESTES FUNCIONAM:**
```
attribute_exists(email)
attribute_exists(userId)
attribute_not_exists(deletedAt)
attribute_not_exists(removed)
```

❌ **ESTES NÃO FUNCIONAM (por enquanto):**
```
userId = '123'          ❌ (precisa ExpressionAttributeValues)
age > 18               ❌ (precisa ExpressionAttributeValues)
status = 'active'      ❌ (precisa ExpressionAttributeValues)
```

---

## 💡 Dicas

### Para Ver Poucos Items:
1. Vá para aba **📋 Dados**
2. Ajuste o campo "Limite" para 5 ou 10
3. Clique **📥 Carregar Dados**
4. Veja em formato de tabela (mais fácil de ler)

### Para Ver Details de Um Item:
1. Na aba **📋 Dados**
2. Dê **duplo-clique** em qualquer linha
3. Veja o JSON completo em popup

### Para Queries Avançadas:
Use a versão CLI:
```bash
python3 dynamodb_cli.py
```

---

## 🚀 Workflow Recomendado

**Exploração inicial:**
```
1. Abra a aba "📋 Dados"
2. Carregue 10 items
3. Veja a estrutura dos dados
4. Identifique campos importantes
```

**Busca específica:**
```
1. Vá para aba "🔍 Query"
2. Use Scan + Filter
3. Veja resultados
```

**Informações da tabela:**
```
1. Vá para aba "ℹ Info"
2. Veja chaves, índices, estatísticas
```

---

## ⚙️ Configurações Úteis

### Ajustar Limite de Resultados:
- Na aba "📋 Dados", campo "Limite"
- Valores: 10-1000
- Padrão: 100

### Atualizar Lista de Tabelas:
- Clique no botão "🔄 Atualizar"
- Útil se criar novas tabelas

---

## 🔍 Fluxo de Uso Típico

```
1. Iniciar app
   ↓
2. Selecionar tabela → "channels"
   ↓
3. Ver dados (aba Dados)
   ↓
4. Carregar 10 items
   ↓
5. Duplo-clique para ver detalhes
   ↓
6. Explorar outras tabelas
```

---

## 📊 Resumo Visual

### ABA "DADOS" (📊)
```
Melhor para:
✅ Explorar dados visualmente
✅ Ver estrutura da tabela
✅ Ler poucos items completos
```

### ABA "QUERY" (🔍)
```
Melhor para:
✅ Filtros específicos
✅ Ver muitos items em JSON
✅ Validar existência de campos
```

### ABA "INFO" (ℹ️)
```
Melhor para:
✅ Ver metadados
✅ Entender chaves primárias
✅ Verificar índices
```

---

## 🎯 Conclusão

**Para sua pergunta "como eu pesquiso":**

### Pesquisa Básica (Scan Tudo):
1. Selecione tabela
2. Aba Query → Scan
3. ▶ Executar

### Pesquisa com Filtro:
1. Selecione tabela
2. Aba Query → Scan
3. Filter: `attribute_exists(campo)`
4. ▶ Executar

### Exploração Visual:
1. Selecione tabela
2. Aba Dados
3. 📥 Carregar Dados
4. Duplo-clique para detalhes

---

**💡 Dica Final:** Para a maioria dos casos, use a aba "📋 Dados" pois é mais fácil de visualizar. Use a aba "🔍 Query" apenas quando precisar de filtros específicos!

**Leia também:** `FILTROS_GUIDE.md` para exemplos avançados
