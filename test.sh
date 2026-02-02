#!/bin/bash
# Script para testar a aplicação DynamoDB Viewer

echo "╔════════════════════════════════════════════╗"
echo "║ DynamoDB Viewer - Teste Rápido             ║"
echo "╚════════════════════════════════════════════╝"
echo ""

# Verificar se está em um ambiente virtual
if [[ ! -d ".venv" ]]; then
    echo "❌ Ambiente virtual não encontrado!"
    echo "Crie um com: python3 -m venv .venv"
    exit 1
fi

# Ativar ambiente virtual
echo "🔧 Ativando ambiente virtual..."
source .venv/bin/activate

# Verificar sintaxe
echo "🔍 Verificando sintaxe do código..."
python -m py_compile main.py src/config.py src/ui/windows/main_window.py
if [ $? -ne 0 ]; then
    echo "❌ Erros de sintaxe encontrados!"
    exit 1
fi
echo "✅ Sintaxe OK"
echo ""

# Verificar importações
echo "📦 Verificando importações..."
python -c "
import sys
sys.path.insert(0, '.')
from src.config import config
from src.services import DynamoDBService
from src.ui.windows import MainWindow
print('✅ Todas as importações funcionam!')
"

if [ $? -ne 0 ]; then
    echo "❌ Erro nas importações!"
    exit 1
fi
echo ""

# Exibir informações
echo "📋 Informações da Aplicação:"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
python -c "
from src.config import config
print(f'Versão: {config.APP_VERSION}')
print(f'Modo Padrão: Local')
print(f'Endpoint Padrão: http://localhost:9000')
print(f'Janela: {config.WINDOW_WIDTH}x{config.WINDOW_HEIGHT}')
"
echo ""

# Pronto para usar
echo "✅ TUDO PRONTO!"
echo ""
echo "Para executar a aplicação, digite:"
echo "  python main.py"
echo ""
echo "Você verá uma janela com opções:"
echo "  📱 DynamoDB Local"
echo "  ☁️ AWS DynamoDB (Produção)"
echo ""
