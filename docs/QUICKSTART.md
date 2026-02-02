# 🚀 Guia Rápido - DynamoDB Viewer

## Instalação Rápida (3 minutos)

### Linux/macOS

```bash
# 1. Execute o setup
chmod +x setup.sh
./setup.sh

# 2. Inicie o aplicativo
python3 dynamodb_viewer.py
```

### Windows

```cmd
REM 1. Execute o setup
setup.bat

REM 2. Inicie o aplicativo
python dynamodb_viewer.py
```

## Uso Básico

### 1️⃣ Conectar
- O app usa automaticamente suas credenciais do AWS CLI
- Se não estiver configurado, rode: `aws configure`

### 2️⃣ Ver Tabelas
- As tabelas aparecem no painel esquerdo
- Clique em uma tabela para selecioná-la

### 3️⃣ Ver Dados
- Aba "📊 Dados" mostra os items da tabela
- Ajuste o limite (10-1000 items)
- Duplo-clique em um item para ver JSON completo

### 4️⃣ Fazer Queries
- Aba "🔍 Query" para scans/queries customizados
- Escolha entre Scan ou Query
- Clique em "▶ Executar"

### 5️⃣ Ver Info da Tabela
- Aba "ℹ️ Info" mostra metadados
- Chaves primárias, índices, estatísticas

## Atalhos

### Teclas Úteis
- `F5`: Refresh dados
- `Duplo-clique`: Ver detalhes do item
- `Ctrl+W`: Fechar janela de detalhes

## Configurações do AWS CLI

### Ver configuração atual
```bash
aws configure list
```

### Configurar região
```bash
aws configure set region us-east-1
```

### Usar perfil específico
```bash
# Configure um perfil
aws configure --profile meu-perfil

# No código, edite connect_to_dynamodb():
self.dynamodb = boto3.resource('dynamodb', profile_name='meu-perfil')
```

### Testar conexão
```bash
aws dynamodb list-tables
```

## Permissões IAM Necessárias

Seu usuário/role AWS precisa destas permissões:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "dynamodb:ListTables",
        "dynamodb:DescribeTable",
        "dynamodb:Scan",
        "dynamodb:Query",
        "dynamodb:GetItem"
      ],
      "Resource": "*"
    }
  ]
}
```

## Exemplos de Uso

### Exemplo 1: Ver todos os usuários
1. Selecione tabela "Users"
2. Clique "Carregar Dados"
3. Veja a lista de usuários

### Exemplo 2: Buscar por email
1. Vá para aba "Query"
2. Selecione "Scan"
3. Execute

### Exemplo 3: Ver item específico
1. Na lista de dados
2. Duplo-clique no item
3. Veja JSON formatado

## Troubleshooting Rápido

### ❌ Erro de credenciais
```bash
aws configure
# Insira suas credenciais
```

### ❌ Nenhuma tabela aparece
```bash
# Verifique a região
aws configure get region

# Liste tabelas manualmente
aws dynamodb list-tables --region us-east-1
```

### ❌ Erro de conexão
- Verifique internet
- Confirme credenciais válidas
- Teste: `aws sts get-caller-identity`

## DynamoDB Local (Desenvolvimento)

Para usar com DynamoDB Local:

```python
# Edite dynamodb_viewer.py, função connect_to_dynamodb():
self.dynamodb = boto3.resource(
    'dynamodb',
    endpoint_url='http://localhost:9000',
    region_name='us-east-1',
    aws_access_key_id='dummy',
    aws_secret_access_key='dummy'
)
```

Inicie DynamoDB Local:
```bash
docker run -p 8000:8000 amazon/dynamodb-local
```

## Dicas

💡 **Performance**: Para tabelas grandes, use limite menor (100-200 items)

💡 **Exploração**: Use Scan para ver dados rapidamente

💡 **Detalhes**: Duplo-clique para ver estrutura completa dos items

💡 **Refresh**: Clique em 🔄 para atualizar dados

## Recursos Adicionais

- 📚 [Documentação AWS DynamoDB](https://docs.aws.amazon.com/dynamodb/)
- 🔧 [Boto3 Docs](https://boto3.amazonaws.com/v1/documentation/api/latest/index.html)
- ⚙️ [AWS CLI Docs](https://docs.aws.amazon.com/cli/)

## Próximos Passos

Experimente:
- ✅ Ver diferentes tabelas
- ✅ Ajustar limites de dados
- ✅ Explorar metadados das tabelas
- ✅ Fazer scans com filtros

---

**Desenvolvido com ❤️ usando Python + Tkinter + Boto3**
