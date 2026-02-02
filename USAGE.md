# 🚀 DynamoDB Viewer - Pronto para Usar!

## ⚡ Iniciar Agora

```bash
python main.py
```

Uma tela aparecerá para você **escolher e configurar** seu servidor DynamoDB:

```
┌─────────────────────────────────────┐
│ 🗄️ Escolher Servidor DynamoDB      │
│                                     │
│ ◯ 📱 DynamoDB Local                │
│    Configure: Protocolo, Host, Porta│
│    Teste: 🧪 Testar Conexão        │
│                                     │
│ ◯ ☁️ AWS Cloud (Produção)          │
│    Selecione: Região AWS            │
│                                     │
│ [✓ Conectar] [✕ Cancelar]         │
└─────────────────────────────────────┘
```

---

## 🎯 Opções

### 1. DynamoDB Local (Desenvolvimento)

```bash
# Padrão
Protocolo:  http
Host:       localhost
Porta:      8000
Endpoint:   http://localhost:9000

# Customizável
Porta: 8001
Host: 192.168.1.100
...
```

**Com teste de conexão integrado! 🧪**

### 2. AWS Cloud (Produção)

```bash
Escolha sua região:
- us-east-1 (padrão)
- eu-west-1
- ap-northeast-1
... e mais 10 regiões
```

---

## ⌨️ CLI Rápida

```bash
# Local padrão
python main.py --local

# Local customizado
python main.py --local http://localhost:8001

# Production
python main.py --production eu-west-1

# Pular dialog
python main.py --skip-dialog
```

---

## 📚 Documentação

| Documento | Descrição |
|-----------|-----------|
| `ENVIRONMENT_DIALOG_GUIDE.md` | 📖 Guia completo do dialog |
| `DYNAMODB_LOCAL_GUIDE.md` | 📖 Setup DynamoDB Local |
| `QUICK_START.md` | 📖 Início rápido |
| `ARCHITECTURE.md` | 📖 Arquitetura do projeto |

---

## ✅ Pronto!

Agora você pode:

- ✅ Escolher servidor (Local ou AWS)
- ✅ Configurar endpoint local
- ✅ Testar conexão
- ✅ Visualizar tabelas DynamoDB
- ✅ Filtrar dados
- ✅ Exportar resultados

Bom desenvolvimento! 🚀
