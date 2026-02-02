# DynamoDB Local - Guia de Configuração

## 🎯 Visão Geral

O DynamoDB Viewer agora suporta **DynamoDB Local** para desenvolvimento sem custos de AWS!

Você pode trabalhar com dados localmente antes de sincronizar com a AWS Cloud.

---

## 📋 Requisitos

- **Docker** instalado ([Download aqui](https://www.docker.com/products/docker-desktop))
- **Python 3.8+**
- **Projeto DynamoDB Viewer**

---

## 🚀 Início Rápido

### 1️⃣ Iniciar DynamoDB Local

**No Linux/Mac:**
```bash
bash setup-local-dynamodb.sh
# Escolha opção 1
```

**No Windows:**
```cmd
setup-local-dynamodb.bat
REM Escolha opção 1
```

Ou manualmente com Docker:
```bash
docker run -d \
  --name dynamodb-local \
  -p 8000:8000 \
  amazon/dynamodb-local:latest
```

### 2️⃣ Verificar Conexão

```bash
curl http://localhost:9000/
# Deve retornar uma resposta do DynamoDB
```

### 3️⃣ Executar a Aplicação

```bash
source .venv/bin/activate  # ativr ambiente virtual
python main.py
```

---

## ⚙️ Configuração

### Arquivo `.env` (Opcional)

Copie `.env.example` para `.env`:

```bash
cp .env.example .env
```

Edite conforme necessário:

```ini
# Usar DynamoDB Local
DYNAMODB_LOCAL=true

# Endpoint local
DYNAMODB_ENDPOINT=http://localhost:9000

# Região
DYNAMODB_REGION=us-east-1

# Credenciais (qualquer valor funciona localmente)
DYNAMODB_ACCESS_KEY=local
DYNAMODB_SECRET_KEY=local
```

### Arquivo de Configuração Python

A configuração é lida em `src/config.py`:

```python
from src.config import config

# Verificar se está usando local
if config.DYNAMODB_LOCAL:
    print(f"Conectando a: {config.DYNAMODB_ENDPOINT}")
else:
    print("Conectando ao AWS Cloud")
```

---

## 📊 Gerenciar DynamoDB Local

### Ver Status

```bash
docker ps | grep dynamodb-local
```

### Ver Logs

```bash
docker logs -f dynamodb-local
```

### Parar DynamoDB Local

```bash
docker stop dynamodb-local
docker rm dynamodb-local
```

Ou use o script:
```bash
bash setup-local-dynamodb.sh  # Escolha opção 2
```

### Reiniciar

```bash
docker restart dynamodb-local
```

---

## 🔨 Criar Tabelas no DynamoDB Local

### Usando AWS CLI

```bash
# Configure AWS CLI local
aws configure --profile local
# AWS Access Key ID: local
# AWS Secret Access Key: local
# Default region: us-east-1

# Criar tabela
aws dynamodb create-table \
  --table-name Users \
  --attribute-definitions AttributeName=id,AttributeType=S \
  --key-schema AttributeName=id,KeyType=HASH \
  --provisioned-throughput ReadCapacityUnits=5,WriteCapacityUnits=5 \
  --endpoint-url http://localhost:9000 \
  --profile local

# Listar tabelas
aws dynamodb list-tables \
  --endpoint-url http://localhost:9000 \
  --profile local
```

### Usando Python (boto3)

```python
import boto3

# Criar cliente DynamoDB Local
dynamodb = boto3.client('dynamodb',
    endpoint_url='http://localhost:9000',
    region_name='us-east-1',
    aws_access_key_id='local',
    aws_secret_access_key='local'
)

# Criar tabela
dynamodb.create_table(
    TableName='Users',
    KeySchema=[
        {'AttributeName': 'id', 'KeyType': 'HASH'},
    ],
    AttributeDefinitions=[
        {'AttributeName': 'id', 'AttributeType': 'S'},
    ],
    ProvisionedThroughput={
        'ReadCapacityUnits': 5,
        'WriteCapacityUnits': 5
    }
)

# Inserir dados
table = boto3.resource('dynamodb',
    endpoint_url='http://localhost:9000',
    region_name='us-east-1'
).Table('Users')

table.put_item(Item={
    'id': 'user-123',
    'name': 'João Silva',
    'email': 'joao@example.com'
})
```

---

## 🔄 Converter para AWS Cloud

Quando quiser usar AWS Cloud em vez de local:

### Opção 1: Mudar variável de ambiente

```bash
export DYNAMODB_LOCAL=false
python main.py
```

### Opção 2: Editar `.env`

```ini
DYNAMODB_LOCAL=false
```

### Opção 3: Mudar código

```python
from src.config import Config
Config.DYNAMODB_LOCAL = False
```

---

## 📱 DynamoDB Admin (Opcional)

Ferramentas visuais para gerenciar DynamoDB Local:

### dynamodb-admin

```bash
npm install -g dynamodb-admin

export DYNAMODB_ENDPOINT=http://localhost:9000
dynamodb-admin
```

Acesse: `http://localhost:8001`

### AWS NoSQL Workbench

[Download aqui](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/workbench.settingup.html)

---

## 🐛 Troubleshooting

### Erro: "Connection refused"

```
❌ Connection refused ao localhost:8000
```

**Solução:**
```bash
# Verificar se DynamoDB está rodando
docker ps | grep dynamodb-local

# Se não estiver, iniciar:
docker run -d --name dynamodb-local -p 8000:8000 amazon/dynamodb-local:latest

# Verificar conexão
curl http://localhost:9000/
```

### Erro: "Port 8000 already in use"

```
❌ Error response from daemon: Bind for 0.0.0.0:8000 failed
```

**Solução:**
```bash
# Remover container antigo
docker rm -f dynamodb-local

# Ou usar porta diferente
docker run -d --name dynamodb-local -p 8001:8000 amazon/dynamodb-local:latest
```

### Dados Desaparecem

DynamoDB Local é em memória por padrão. Para persistir:

```bash
docker run -d \
  --name dynamodb-local \
  -p 8000:8000 \
  -v dynamodb_data:/data \
  amazon/dynamodb-local:latest \
  -jar DynamoDBLocal.jar -sharedDb -dbPath /data
```

---

## 📚 Recursos Adicionais

- [DynamoDB Local Documentation](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/DynamoDBLocal.html)
- [AWS CLI DynamoDB Commands](https://docs.aws.amazon.com/cli/latest/reference/dynamodb/index.html)
- [Boto3 DynamoDB Documentation](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/dynamodb.html)

---

## ✅ Checklist

- [ ] Docker instalado
- [ ] DynamoDB Local rodando (`docker ps`)
- [ ] Conectar no DynamoDB Viewer
- [ ] Ver tabelas na aplicação
- [ ] Criar/editar dados
- [ ] Tudo funcionando? ✓

---

Bom desenvolvimento! 🚀
