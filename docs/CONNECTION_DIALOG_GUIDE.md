# 🎯 Connection Dialog - Selecionar Ambiente

## O que é?

Uma **tela de seleção** que aparece ao iniciar a aplicação, permitindo escolher entre:

1. **📱 DynamoDB Local** - Desenvolvimento sem custos
2. **☁️ AWS Cloud** - Produção com dados reais

---

## 🚀 Como Usar

### Iniciar a Aplicação

```bash
python main.py
```

### Primeira Tela

Uma janela aparecerá com duas opções:

```
╔══════════════════════════════════════════════════╗
║  🗄️ DynamoDB Viewer - Selecionar Ambiente       ║
║     Escolha onde deseja conectar:               ║
╠══════════════════════════════════════════════════╣
║                                                  ║
║  ◯ 📱 DynamoDB Local                            ║
║    ✓ Desenvolvimento sem custos                 ║
║    ✓ Executando em http://localhost:9000        ║
║    ✓ Dados apenas durante a sessão              ║
║    Endpoint: [http://localhost:9000]            ║
║                                                  ║
║  ◯ ☁️ AWS Cloud (Produção)                      ║
║    ✓ Dados persistentes em produção             ║
║    ✓ Acesso a dados reais                       ║
║    ⚠ Requer AWS CLI configurado                 ║
║    Região AWS: [us-east-1 ▼]                    ║
║                                                  ║
║              [Conectar]  [Cancelar]             ║
╚══════════════════════════════════════════════════╝
```

---

## 📋 Opções Disponíveis

### 1. DynamoDB Local

**Quando usar:**
- ✅ Desenvolvimento local
- ✅ Testes sem gastar créditos AWS
- ✅ Trabalhar offline

**Configurações:**
- Endpoint customizável (padrão: `http://localhost:9000`)
- Sem custos
- Dados temporários (apenas durante a sessão)

**Pré-requisitos:**
- Docker instalado
- DynamoDB Local rodando

### 2. AWS Cloud (Produção)

**Quando usar:**
- ✅ Dados em produção
- ✅ Ambiente real
- ✅ Sincronizar com AWS

**Configurações:**
- Selecionar região AWS
- Regiões suportadas:
  - `us-east-1`
  - `us-east-2`
  - `us-west-1`
  - `us-west-2`
  - `eu-west-1`
  - `eu-central-1`
  - `ap-northeast-1`
  - `ap-southeast-1`

**Pré-requisitos:**
- AWS CLI configurado
- Credenciais AWS válidas

---

## 🔧 Como Funciona

### Fluxo de Execução

```
1. Usuário executa: python main.py
   ↓
2. Exibe ConnectionDialog
   ├─ Opção 1: DynamoDB Local
   │  └─ Entrada customizável do endpoint
   │
   └─ Opção 2: AWS Cloud
      └─ Seleção de região
   
3. Usuário escolhe e clica "Conectar"
   ↓
4. Config atualizada dinamicamente
   ├─ Local: config.set_local(endpoint)
   └─ Production: config.set_production(region)
   
5. Exibe configuração no console
   ↓
6. Abre MainWindow com conexão ativa
```

### Código de Integração

```python
# main.py
from src.ui.components import ConnectionDialog
from src.config import config

# Mostrar dialog
dialog = ConnectionDialog(hidden_root)
result = dialog.show()

# Aplicar configuração
if result['type'] == 'local':
    config.set_local(result['endpoint'])
else:
    config.set_production(result['region'])
```

---

## 🎨 Interface

### Dialog Components

| Componente | Descrição |
|-----------|-----------|
| **RadioButton** | Selecionar Local ou Production |
| **Label** | Mostrar informações de cada opção |
| **Entry** | Customizar endpoint (local) |
| **Combobox** | Selecionar região (production) |
| **Buttons** | Conectar ou Cancelar |

### Validações

- ✅ Endpoint não vazio
- ✅ Região selecionada válida
- ✅ Ambiente configurado antes de criar MainWindow

---

## 📊 Exemplos de Uso

### Exemplo 1: Conectar Local

```
1. Executar: python main.py
2. Dialog aparece
3. Selecionar: "📱 DynamoDB Local"
4. Clicar: [Conectar]
5. Resultado:
   ☞ DynamoDB Viewer - Local
   ☞ Endpoint: http://localhost:9000
```

### Exemplo 2: Conectar AWS

```
1. Executar: python main.py
2. Dialog aparece
3. Selecionar: "☁️ AWS Cloud (Produção)"
4. Escolher região: "eu-west-1"
5. Clicar: [Conectar]
6. Resultado:
   ☞ DynamoDB Viewer - AWS (eu-west-1)
```

### Exemplo 3: Cancelar

```
1. Executar: python main.py
2. Dialog aparece
3. Clicar: [Cancelar]
4. Resultado:
   ☞ Aplicação encerra
   ☞ Nenhuma conexão estabelecida
```

---

## 🔄 Mudar Ambiente em Runtime

Você também pode mudar programaticamente:

```python
from src.config import config

# Mudar para local
config.set_local("http://localhost:9000")

# Mudar para production
config.set_production("us-west-2")

# Exibir configuração
config.print_config()
```

---

## 📝 Classes Importantes

### ConnectionDialog

**Localização:** `src/ui/components/connection_dialog.py`

**Métodos principais:**
- `setup_dialog()` - Criar interface
- `setup_local_option()` - Setup opção local
- `setup_production_option()` - Setup opção produção
- `on_connect()` - Processar conexão
- `on_cancel()` - Cancelar
- `show()` - Mostrar dialog e retornar resultado

### Config

**Localização:** `src/config.py`

**Métodos principais:**
- `set_local(endpoint)` - Configurar modo local
- `set_production(region)` - Configurar modo produção
- `get_dynamodb_config()` - Retornar config do boto3
- `print_config()` - Exibir configuração atual

---

## ✨ Recurso: Customizar Endpoint

Se você tiver DynamoDB Local rodando em porta diferente:

```
1. Executar: python main.py
2. Dialog aparece
3. Selecionar: "📱 DynamoDB Local"
4. Editar endpoint: "http://localhost:8001"
5. Clicar: [Conectar]
```

---

## 🛡️ Tratamento de Erros

### Se cancelar

```
☞ Aplicação encerra gracefully
☞ Nenhuma conexão é estabelecida
```

### Se DynamoDB não estiver disponível

```
☞ Dialog é mostrado normalmente
☞ Erro de conexão ao tentar conectar
☞ Mensagem clara sobre verificar endpoint
```

### Se AWS credentials forem inválidas

```
☞ Dialog é mostrado normalmente
☞ Erro de autenticação ao tentar conectar
☞ Mensagem sobre configurar: aws configure
```

---

## 📚 Arquivo Modificado

- `main.py` - Adicionado lógica de dialog
- `src/config.py` - Adicionados métodos `set_local()` e `set_production()`
- `src/ui/components/connection_dialog.py` - Novo arquivo
- `src/ui/components/__init__.py` - Exportar ConnectionDialog

---

## ✅ Resultado Final

Agora você tem:

✓ **Tela de seleção** ao iniciar
✓ **Duas opções** claras (Local e Production)
✓ **Configuração dinâmica** baseada na escolha
✓ **Interface amigável** com descrições
✓ **Suporte a customização** de endpoint
✓ **Seleção de região** para AWS

Bom desenvolvimento! 🚀
