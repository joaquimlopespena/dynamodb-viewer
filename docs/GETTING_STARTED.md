# 🚀 DynamoDB Viewer - Como Usar

## ⚡ Iniciar Rápido

```bash
# Ativar ambiente virtual
source .venv/bin/activate

# Executar aplicação
python main.py
```

## 🎯 O que Aparece

Uma janela simples aparecerá com duas opções:

### 📱 DynamoDB Local
- **Para desenvolvimento sem custos**
- Digite o endpoint (padrão: `http://localhost:9000`)
- Clique "Conectar"

### ☁️ AWS DynamoDB (Produção)
- **Para dados em produção**
- Selecione a região AWS
- Clique "Conectar"

## 📋 Recursos

✅ Selecionar servidor na startup
✅ Configurar endpoint do servidor local
✅ Escolher região da AWS
✅ Arquitetura modular e profissional
✅ Filtros visuais para consultas
✅ Exibição de dados em tabelas
✅ Informações detalhadas das tabelas

## 📁 Estrutura

```
src/
├── config.py              ← Configuração
├── models/                ← Modelos de dados
├── services/              ← Lógica DynamoDB
├── ui/                    ← Interface
└── utils/                 ← Utilitários

main.py                   ← Ponto de entrada
```

## 🔧 Requisitos

- Python 3.8+
- DynamoDB Local (para modo local) ou AWS CLI configurado (para produção)

## 📚 Documentação Completa

Para mais detalhes, consulte:
- `ARCHITECTURE.md` - Arquitetura do projeto
- `DYNAMODB_LOCAL_GUIDE.md` - Guia DynamoDB Local
- `CONNECTION_DIALOG_GUIDE.md` - Detalhes do dialog de conexão

## ✅ Pronto para Usar!

Bom desenvolvimento! 🚀
