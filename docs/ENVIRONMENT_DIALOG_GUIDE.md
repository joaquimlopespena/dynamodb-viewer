# 🎯 Environment Dialog - Selecionar e Configurar Servidor

## O que é?

Uma **tela completa de configuração** que aparece ao iniciar a aplicação, permitindo:

1. **Escolher entre Local ou Production**
2. **Configurar o servidor Local** (Protocolo, Host, Porta)
3. **Testar a conexão** antes de conectar
4. **Selecionar região AWS** para Production

---

## 🎨 Interface

### Tela Principal

```
╔══════════════════════════════════════════════════╗
║  🗄️ Escolher Servidor DynamoDB                 ║
║     Qual servidor você deseja usar?             ║
╠══════════════════════════════════════════════════╣
║                                                  ║
║  ◯ 📱 DynamoDB Local (Desenvolvimento)          ║
║    ✓ Sem custos                                 ║
║    ✓ Rápido para desenvolvimento                ║
║    ✓ Dados locais - não persistem               ║
║                                                  ║
║    ⚙️ Configuração                              ║
║    Protocolo:  [http      ▼]                    ║
║    Host:       [localhost          ]            ║
║    Porta:      [8000               ]            ║
║    Endpoint:   [http://localhost:9000]          ║
║                                                  ║
║  ◯ ☁️ AWS Cloud (Produção)                      ║
║    ✓ Dados persistentes                         ║
║    ✓ Acesso a dados reais                       ║
║    ⚠ Requer AWS CLI configurado                 ║
║                                                  ║
║    ⚙️ Configuração                              ║
║    Região AWS: [us-east-1        ▼]             ║
║                                                  ║
║  [🧪 Testar] [✓ Conectar] [✕ Cancelar]         ║
╚══════════════════════════════════════════════════╝
```

---

## 🚀 Modo de Uso

### Iniciar a Aplicação

```bash
python main.py
```

**Resultado:** EnvironmentDialog aparece com opções de configuração

---

## 📱 Opção 1: DynamoDB Local

### Configuração Padrão

```
Protocolo:  http
Host:       localhost
Porta:      8000
Endpoint:   http://localhost:9000
```

### Customizar

Você pode alterar qualquer um dos campos:

**Exemplo 1: Porta Diferente**
- Porta: `8001`
- Endpoint: `http://localhost:8001`

**Exemplo 2: Host Remoto**
- Host: `192.168.1.100`
- Porta: `8000`
- Endpoint: `http://192.168.1.100:8000`

**Exemplo 3: HTTPS**
- Protocolo: `https`
- Host: `dynamodb.local`
- Porta: `8000`
- Endpoint: `https://dynamodb.local:8000`

### Testar Conexão

Antes de conectar, você pode **testar a conexão**:

```
1. Clicar em [🧪 Testar Conexão]
2. Aguardar validação
3. Ver resultado:
   ✓ Sucesso - Endpoint está respondendo
   ✗ Erro - Verificar se DynamoDB está rodando
```

### Conectar

```
1. Configurar endpoint
2. Clicar em [✓ Conectar]
3. MainWindow abre conectado no endpoint configurado
```

---

## ☁️ Opção 2: AWS Cloud (Produção)

### Regiões Disponíveis

```
us-east-1          (N. Virginia - padrão)
us-east-2          (Ohio)
us-west-1          (N. California)
us-west-2          (Oregon)
ca-central-1       (Canada)
eu-west-1          (Ireland)
eu-west-2          (London)
eu-central-1       (Frankfurt)
ap-northeast-1     (Tokyo)
ap-northeast-2     (Seoul)
ap-southeast-1     (Singapore)
ap-southeast-2     (Sydney)
sa-east-1          (São Paulo)
```

### Selecionar Região

```
1. Selecionar: ◯ AWS Cloud (Produção)
2. Escolher região no dropdown
3. Clicar em [✓ Conectar]
4. MainWindow abre conectado em AWS na região selecionada
```

### Pré-requisitos

- ✅ AWS CLI instalado
- ✅ Credenciais configuradas (`aws configure`)
- ✅ Acesso à região selecionada

---

## 🧪 Testar Conexão Local

### Como Funciona

1. Coleta o endpoint configurado
2. Tenta fazer conexão HTTP
3. Mostra resultado

### Resultado de Sucesso

```
╔════════════════════════════╗
║ Sucesso                    ║
║                            ║
║ ✓ Conexão bem-sucedida!   ║
║                            ║
║ Endpoint: ...             ║
║ Status: 200               ║
║                            ║
║         [OK]              ║
╚════════════════════════════╝
```

### Resultado de Erro

```
╔════════════════════════════════════╗
║ Erro de Conexão                    ║
║                                    ║
║ ✗ Não foi possível conectar a:    ║
║   http://localhost:9000           ║
║                                    ║
║ Erro: Connection refused          ║
║                                    ║
║ Certifique-se que DynamoDB Local  ║
║ está rodando.                      ║
║                                    ║
║         [OK]                       ║
╚════════════════════════════════════╝
```

---

## ⌨️ Atalhos via CLI

Se você quer pular o dialog:

### Modo Local (Rápido)

```bash
python main.py --local
python main.py --local http://localhost:8001
python main.py -l http://192.168.1.100:8000
```

### Modo Production (Rápido)

```bash
python main.py --production
python main.py --production eu-west-1
python main.py -p ap-northeast-1
```

### Pular Dialog

```bash
python main.py --skip-dialog
```

---

## 📝 Exemplos de Uso

### Exemplo 1: Local Padrão

```bash
$ python main.py

[EnvironmentDialog aparece]
✓ DynamoDB Local selecionado
✓ Endpoint: http://localhost:9000
[Clicar em Conectar]

Resultado:
✓ MainWindow conectado em http://localhost:9000
```

### Exemplo 2: Local Customizado

```bash
$ python main.py

[EnvironmentDialog aparece]
✓ DynamoDB Local selecionado
✏️ Alterar porta: 8001
✏️ Endpoint: http://localhost:8001
🧪 Testar Conexão → ✓ Sucesso
[Clicar em Conectar]

Resultado:
✓ MainWindow conectado em http://localhost:8001
```

### Exemplo 3: Production AWS

```bash
$ python main.py

[EnvironmentDialog aparece]
✓ AWS Cloud selecionado
✏️ Região: eu-west-1
[Clicar em Conectar]

Resultado:
✓ MainWindow conectado a AWS (eu-west-1)
```

### Exemplo 4: CLI Rápido

```bash
# Local customizado direto
$ python main.py --local http://192.168.1.100:8000

Resultado:
✓ MainWindow abre instantaneamente
✓ Conectado em http://192.168.1.100:8000
```

---

## 🔧 Componentes

### EnvironmentDialog Class

**Localização:** `src/ui/components/environment_dialog.py`

**Métodos:**
- `setup_dialog()` - Criar interface
- `setup_local_option()` - Setup local config
- `setup_production_option()` - Setup AWS config
- `update_local_endpoint()` - Atualizar endpoint display
- `on_env_changed()` - Lidar com mudança de ambiente
- `test_connection()` - Testar conexão (em thread)
- `on_connect()` - Processar conexão
- `on_cancel()` - Cancelar
- `show()` - Mostrar dialog

### Variáveis de Configuração

**Local:**
- `self.local_protocol` - http/https
- `self.local_host` - hostname/IP
- `self.local_port` - porta
- `self.local_endpoint_display` - endpoint montado

**Production:**
- `self.aws_region` - região AWS selecionada

---

## ✨ Recursos Especiais

### 1. Endpoint Auto-Update

Ao mudar Protocolo, Host ou Porta, o endpoint é **atualizado automaticamente**:

```
Protocolo: http      ──┐
Host: localhost      ──┼──> Endpoint: http://localhost:9000
Porta: 8000          ──┘
```

### 2. Test Button

O botão **Testar Conexão** é:
- ✅ Habilitado apenas para Local
- ❌ Desabilitado para Production
- 🔄 Mostra feedback visual durante teste
- ⚠️ Roda em thread separada (não bloqueia UI)

### 3. Validação

Antes de conectar, valida:
- ✓ Endpoint não vazio
- ✓ Endpoint válido (começa com http:// ou https://)
- ✓ Região selecionada para AWS

### 4. Threading

Testes de conexão rodam em thread separada:
- ✅ UI não congelaa
- ✅ Feedback visual
- ✅ Timeout de 5 segundos

---

## 📊 Fluxo de Inicialização

```
python main.py
    ↓
[Mostrar EnvironmentDialog]
    ├─ Local
    │  ├─ Protocolo: http/https
    │  ├─ Host: localhost/IP
    │  ├─ Porta: 8000
    │  ├─ Teste: opcional
    │  └─ Conectar
    │
    └─ Production
       ├─ Região: us-east-1
       └─ Conectar
    ↓
[Aplicar Configuração]
    ├─ set_local(endpoint)
    └─ set_production(region)
    ↓
[Abrir MainWindow]
    └─ Conectado ao servidor selecionado
```

---

## 🎯 Conclusão

O **EnvironmentDialog** oferece:

✅ Interface clara e intuitiva
✅ Configuração completa do servidor local
✅ Teste de conexão integrado
✅ Suporte a múltiplas regiões AWS
✅ Validação de entrada
✅ Threading para responsividade
✅ Atalhos CLI para usuários avançados

Bom desenvolvimento! 🚀
