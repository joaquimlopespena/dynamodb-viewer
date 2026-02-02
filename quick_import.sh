#!/bin/bash
# Script rápido para importar arquivos grandes
# Uso: ./quick_import.sh messages-dump.json messages

set -e

if [ $# -lt 2 ]; then
    echo "❌ Uso: $0 <arquivo.json> <nome-tabela>"
    echo ""
    echo "Exemplos:"
    echo "  $0 messages-dump.json messages"
    echo "  $0 /path/to/file.json minha_tabela"
    exit 1
fi

FILE="$1"
TABLE="$2"

echo "🚀 Iniciando import otimizado..."
echo "   Arquivo: $FILE"
echo "   Tabela: $TABLE"
echo ""

if [ ! -f "$FILE" ]; then
    echo "❌ Arquivo não encontrado: $FILE"
    exit 1
fi

# Mostrar tamanho do arquivo
SIZE=$(du -h "$FILE" | cut -f1)
echo "📦 Tamanho do arquivo: $SIZE"
echo ""

# Executar import
python3 import_large_dumps.py --file "$FILE" --table "$TABLE"

echo ""
echo "✅ Import concluído!"
echo ""
echo "📊 Para ver o log detalhado:"
echo "   tail -f /tmp/dynamodb_import.log"
