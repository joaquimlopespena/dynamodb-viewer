# 🎉 DynamoDB Viewer - Configuração Local Completa!

## ✅ O que foi implementado

### 1. **Sistema de Configuração** (`src/config.py`)
```python
# Detecta automaticamente se está usando DynamoDB Local
config = Config()

# Configuração baseada em variáveis de ambiente
- DYNAMODB_LOCAL=true/false
- DYNAMODB_ENDPOINT=http://localhost:9000
- DYNAMODB_REGION=us-east-1
- DYNAMODB_ACCESS_KEY/SECRET_KEY
```

### 2. **Scripts de Setup**
- ✅ `setup-local-dynamodb.sh` (Linux/Mac)
- ✅ `setup-local-dynamodb.bat` (Windows)

### 3. **Documentação**
- ✅ `DYNAMODB_LOCAL_GUIDE.md` (Guia completo)
- ✅ `.env.example` (Configuração exemplo)

### 4. **Integração Automática**
- A aplicação detecta e exibe se está conectada ao **Local** ou **AWS Cloud**
- Mensagens de erro customizadas para cada tipo

---

## 🚀 Como Usar

### Passo 1: Iniciar DynamoDB Local

**Linux/Mac:**
```bash
bash setup-local-dynamodb.sh
# Digite: 1 (para iniciar)
```

**Windows:**
```cmd
setup-local-dynamodb.bat
REM Digite: 1 (para iniciar)
```

**Ou manualmente:**
```bash
docker run -d --name dynamodb-local -p 8000:8000 amazon/dynamodb-local:latest
```

### Passo 2: Ativar Ambiente Virtual

```bash
source .venv/bin/activate  # Linux/Mac
REM ou
.venv\Scripts\activate     # Windows
```

### Passo 3: Executar a Aplicação

```bash
python main.py
```

Você verá na janela:
- ✓ Conectado ao DynamoDB Local
- Endpoint: http://localhost:9000

---

## 📋 Estrutura de Configuração

```
Aplicação
    ↓
config.py (lê variáveis de ambiente)
    ↓
DynamoDBService (usa config para conectar)
    ↓
DynamoDB Local (http://localhost:9000)
    ou
AWS Cloud (us-east-1)
```

---

## 🔧 Configurações Suportadas

### Usar DynamoDB Local (Padrão)
```bash
export DYNAMODB_LOCAL=true
export DYNAMODB_ENDPOINT=http://localhost:9000
python main.py
```

### Usar AWS Cloud
```bash
export DYNAMODB_LOCAL=false
python main.py
```

### Com arquivo `.env`
```bash
cp .env.example .env
# Editar .env conforme necessário
python main.py  # Lê automaticamente .env
```

---

## 📚 Arquivos Criados

| Arquivo | Descrição |
|---------|-----------|
| `src/config.py` | Sistema de configuração central |
| `setup-local-dynamodb.sh` | Script de setup (Linux/Mac) |
| `setup-local-dynamodb.bat` | Script de setup (Windows) |
| `.env.example` | Configuração exemplo |
| `DYNAMODB_LOCAL_GUIDE.md` | Guia completo de uso |

---

## 🔍 Verificar Configuração Atual

Quando a aplicação inicia, exibe:

```
============================================================
DynamoDB Viewer - Configuração Atual
============================================================
Modo Local: ✓ SIM
Endpoint: http://localhost:9000
Região: us-east-1
Janela: 1400x800
============================================================
```

---

## 💡 Casos de Uso

### Desenvolvimento Local
```bash
# Desenvolver sem gastar AWS
python main.py  # Conecta a localhost:8000
```

### Testar com AWS
```bash
# Testar com dados reais
DYNAMODB_LOCAL=false python main.py
```

### Produção
```bash
# Deploy em produção
# Mudar em src/config.py ou variáveis de ambiente
```

---

## ⚠️ Diferenças Local vs Cloud

| Aspecto | Local | Cloud |
|--------|-------|-------|
| Custo | Gratuito | Pago por uso |
| Velocidade | Rápido | Depende da rede |
| Persistência | Apenas container | Permanente |
| Limite | Ilimitado | Conforme plano |
| Credenciais | Qualquer valor | AWS credentials |

---

## 🛠️ Gerenciar DynamoDB Local

### Ver status
```bash
docker ps | grep dynamodb-local
```

### Parar
```bash
docker stop dynamodb-local
```

### Remover
```bash
docker rm dynamodb-local
```

### Ver logs
```bash
docker logs -f dynamodb-local
```

---

## 📊 Verificar Tabelas

### Via CLI
```bash
aws dynamodb list-tables \
  --endpoint-url http://localhost:9000 \
  --region us-east-1
```

### Via Python
```python
from src.services import DynamoDBService
service = DynamoDBService()
service.connect()
tables = service.get_tables()
print(tables)
```

### Via Aplicação
1. Abrir `python main.py`
2. Ver lista de tabelas no painel esquerdo
3. Selecionar e visualizar dados

---

## ✨ Próximos Passos

- [ ] Criar tabelas de exemplo em DynamoDB Local
- [ ] Importar dados para teste
- [ ] Executar queries complexas
- [ ] Exportar dados para CSV/JSON
- [ ] Usar em produção com AWS

---

## 📞 Suporte

Consulte `DYNAMODB_LOCAL_GUIDE.md` para:
- Criar tabelas
- Inserir dados
- Troubleshooting
- Ferramentas visuais
- Converter para AWS

---

## ✅ Conclusão

Você agora tem um **DynamoDB Viewer totalmente funcional** que:

✓ Funciona com **DynamoDB Local** (desenvolvimento)
✓ Funciona com **AWS Cloud** (produção)
✓ Suporta **múltiplas configurações**
✓ Detecção **automática** de ambiente
✓ **Sem custos** durante desenvolvimento

Bom trabalho! 🚀
