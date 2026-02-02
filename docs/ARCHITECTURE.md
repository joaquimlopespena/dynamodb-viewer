# Estrutura do Projeto - Arquitetura Orientada a Objetos

## Visão Geral

O projeto foi refatorado para seguir padrões de orientação a objetos com uma estrutura de diretórios clara e modular.

## Estrutura de Diretórios

```
dynamodb-viewer/
├── src/
│   ├── __init__.py
│   ├── models/              # Modelos de dados
│   │   ├── __init__.py
│   │   └── filter_row.py   # Classe FilterRow para linhas de filtro
│   │
│   ├── services/            # Lógica de negócio
│   │   ├── __init__.py
│   │   └── dynamodb_service.py  # Serviço DynamoDB
│   │
│   ├── ui/                  # Interface do usuário
│   │   ├── __init__.py
│   │   ├── components/      # Componentes reutilizáveis
│   │   │   ├── __init__.py
│   │   │   └── loading_indicator.py  # Indicador de carregamento
│   │   │
│   │   └── windows/         # Janelas da aplicação
│   │       ├── __init__.py
│   │       └── main_window.py  # Janela principal
│   │
│   └── utils/               # Funções utilitárias
│       ├── __init__.py
│       └── encoders.py      # Encoders JSON (Decimal)
│
├── main.py                  # Ponto de entrada
├── requirements.txt
└── ... (outros arquivos)
```

## Componentes Principais

### 1. **Services** (`src/services/`)
- **DynamoDBService**: Gerencia todas as operações com DynamoDB
  - Conexão e gerenciamento de tabelas
  - Construção de filtros
  - Queries e scans
  - Conversão de tipos

### 2. **Models** (`src/models/`)
- **FilterRow**: Representa uma linha de filtro na UI
  - Gerenciamento de widgets
  - Validação de filtros
  - Conversão de tipos de valores

### 3. **UI** (`src/ui/`)

#### Windows (`src/ui/windows/`)
- **MainWindow**: Janela principal da aplicação
  - Setup da interface
  - Gerenciamento de abas
  - Controle de eventos
  - Integração com serviços

#### Components (`src/ui/components/`)
- **LoadingIndicator**: Componente de indicador de carregamento
  - Animação de spinner
  - Estados (sucesso, erro, aviso)

### 4. **Utils** (`src/utils/`)
- **DecimalEncoder**: Encoder JSON customizado para tipos Decimal do DynamoDB

## Como Usar

### Executar a Aplicação

```bash
# Ativar ambiente virtual (se necessário)
source .venv/bin/activate

# Executar a aplicação
python main.py
```

### Estrutura de Importações

```python
# Importar serviços
from src.services import DynamoDBService

# Importar modelos
from src.models import FilterRow

# Importar componentes UI
from src.ui.components import LoadingIndicator
from src.ui.windows import MainWindow

# Importar utilitários
from src.utils.encoders import DecimalEncoder
```

## Padrões de Design Utilizados

### 1. **Service Pattern**
- Lógica de negócio isolada em serviços
- `DynamoDBService` encapsula todas as operações com DynamoDB

### 2. **Component Pattern**
- Componentes UI reutilizáveis (`LoadingIndicator`, `FilterRow`)
- Separação de responsabilidades

### 3. **Separation of Concerns**
- **Models**: Representação de dados
- **Services**: Lógica de negócio
- **UI/Windows**: Apresentação
- **Utils**: Funções auxiliares

### 4. **Single Responsibility**
- Cada classe tem uma responsabilidade clara
- Facilita testes e manutenção

## Benefícios da Refatoração

✅ **Modularidade**: Código dividido em módulos independentes
✅ **Reutilização**: Componentes podem ser reutilizados
✅ **Testabilidade**: Cada componente pode ser testado isoladamente
✅ **Manutenibilidade**: Estrutura clara e bem organizada
✅ **Escalabilidade**: Fácil adicionar novos recursos
✅ **Documentação**: Docstrings em todas as classes

## Próximos Passos Sugeridos

1. Adicionar testes unitários em `tests/`
2. Criar camada de configuração (`src/config/`)
3. Adicionar logging estruturado
4. Implementar tratamento de erros customizado
5. Adicionar persistência de preferências do usuário

---

**Nota**: Os arquivos antigos (`dynamodb_viewer.py`, `dynamodb_viewer-1.py`, `dynamodb_viewer-bkp.py`) podem ser removidos ou mantidos como backup.
