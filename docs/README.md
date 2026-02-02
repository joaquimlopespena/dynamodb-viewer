# DynamoDB Viewer 🗄️

Aplicativo desktop em Python para visualizar e gerenciar dados do Amazon DynamoDB, similar ao HeidiSQL para bancos de dados relacionais.

## 📋 Funcionalidades

- ✅ **Listar todas as tabelas** do DynamoDB
- ✅ **Visualizar dados** das tabelas em formato de tabela
- ✅ **Scan e Query** customizados
- ✅ **Detalhes dos items** em JSON formatado
- ✅ **Informações da tabela** (metadados, índices, etc)
- ✅ **Interface gráfica intuitiva** similar ao HeidiSQL
- ✅ **Usa credenciais do AWS CLI**

## 🚀 Instalação

### 1. Pré-requisitos

- Python 3.6 ou superior
- AWS CLI configurado
- Tkinter (interface gráfica do Python)

### Instalar Tkinter (necessário!)

**Ubuntu/Debian:**
```bash
sudo apt update
sudo apt install python3-tk
```

**Fedora:**
```bash
sudo dnf install python3-tkinter
```

**Arch Linux:**
```bash
sudo pacman -S tk
```

### 2. Instalar AWS CLI (se ainda não tiver)

**Linux/macOS:**
```bash
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
unzip awscliv2.zip
sudo ./aws/install
```

**Windows:**
Baixe e instale de: https://aws.amazon.com/cli/

### 3. Configurar AWS CLI

```bash
aws configure
```

Você precisará fornecer:
- AWS Access Key ID
- AWS Secret Access Key
- Default region (ex: us-east-1, sa-east-1)
- Default output format (json)

### 4. Instalar dependências Python

```bash
pip install -r requirements.txt --break-system-packages
```

Ou instalar diretamente:
```bash
pip install boto3
```

## 💻 Como Usar

### Iniciar o aplicativo

```bash
python dynamodb_viewer.py
```

### Interface

O aplicativo possui 3 áreas principais:

#### 1. **Painel Esquerdo - Lista de Tabelas**
- Mostra todas as tabelas disponíveis no DynamoDB
- Clique em uma tabela para selecioná-la
- Botão "Atualizar" para recarregar a lista

#### 2. **Aba "Dados"**
- Visualiza os items da tabela selecionada
- Clique em "Carregar Dados" para buscar os items
- Ajuste o limite de items a carregar (10-1000)
- Dê duplo-clique em um item para ver detalhes em JSON

#### 3. **Aba "Query"**
- Execute operações de Scan ou Query
- Adicione filtros customizados
- Resultados mostrados em formato JSON

#### 4. **Aba "Info"**
- Metadados da tabela
- Chaves primárias
- Índices secundários
- Estatísticas de uso

## 📝 Exemplos de Uso

### Visualizar dados de uma tabela

1. Selecione a tabela no painel esquerdo
2. A aba "Dados" mostrará automaticamente os items
3. Use o controle de "Limite" para ajustar quantos items carregar

### Fazer um Scan com filtro

1. Vá para a aba "Query"
2. Selecione "Scan"
3. Execute para buscar items

### Ver detalhes de um item

1. Na aba "Dados", dê duplo-clique em qualquer linha
2. Uma janela popup mostrará o JSON completo do item

## 🔧 Configuração Avançada

### Usar perfil específico do AWS CLI

Edite o código em `dynamodb_viewer.py` na função `connect_to_dynamodb`:

```python
self.dynamodb = boto3.resource('dynamodb', 
                               profile_name='seu_perfil',
                               region_name='us-east-1')
```

### Usar endpoint local do DynamoDB

Para testar com DynamoDB Local:

```python
self.dynamodb = boto3.resource('dynamodb',
                               endpoint_url='http://localhost:9000',
                               region_name='us-east-1')
```

## 🐛 Solução de Problemas

### Erro: "Unable to locate credentials"

**Solução:** Configure o AWS CLI:
```bash
aws configure
```

### Erro: "Connection refused"

**Solução:** Verifique se suas credenciais AWS estão corretas e se você tem acesso ao DynamoDB:
```bash
aws dynamodb list-tables
```

### Nenhuma tabela aparece

**Solução:** 
- Verifique a região configurada no AWS CLI
- Confirme que existem tabelas na região selecionada
- Teste: `aws dynamodb list-tables --region sua-regiao`

## 📦 Estrutura do Projeto

```
.
├── dynamodb_viewer.py    # Aplicativo principal
├── requirements.txt      # Dependências Python
└── README.md            # Esta documentação
```

## 🎨 Melhorias Futuras

- [ ] Adicionar/Editar/Deletar items
- [ ] Exportar dados para CSV/JSON
- [ ] Suporte a queries complexas com expressões
- [ ] Busca e filtros avançados
- [ ] Visualização de throughput
- [ ] Múltiplas conexões (profiles diferentes)
- [ ] Tema escuro

## 📄 Licença

Este projeto é livre para uso pessoal e comercial.

## 🤝 Contribuições

Sugestões e melhorias são bem-vindas!

## 📞 Suporte

Se encontrar problemas:
1. Verifique se o AWS CLI está configurado: `aws configure list`
2. Teste a conexão: `aws dynamodb list-tables`
3. Verifique as permissões IAM necessárias para DynamoDB

## 🔒 Segurança

⚠️ **Importante:** 
- Nunca compartilhe suas credenciais AWS
- Use IAM roles com permissões mínimas necessárias
- Em produção, considere usar AWS IAM Roles em vez de Access Keys
