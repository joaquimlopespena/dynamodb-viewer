#!/bin/bash

# Caminho onde estão os dumps
DUMP_DIR="/home/joaquim/dumps/DynamoDB"

# Endpoint do DynamoDB local
DYNAMODB_ENDPOINT="http://localhost:9000"

# Loop pelos arquivos -dump.json
for FILE in "$DUMP_DIR"/*-dump.json; do
    # Extrai nome da tabela (removendo -dump.json)
    TABLE_NAME=$(basename "$FILE" | sed 's/-dump\.json//')

    echo "📥 Importando arquivo: $FILE para a tabela: $TABLE_NAME"

    # Gera script Python temporário
    PYTHON_SCRIPT=$(mktemp)

    cat <<EOF > "$PYTHON_SCRIPT"
import json
import boto3
import sys

dynamodb = boto3.client('dynamodb', endpoint_url="$DYNAMODB_ENDPOINT", region_name='us-east-1')

with open("$FILE", "r") as f:
    try:
        data = json.load(f)
        items = data.get("Items", data)  # Se não tiver "Items", assume que é lista direta
    except Exception as e:
        print(f"❌ Erro ao carregar JSON de $FILE: {e}")
        sys.exit(1)
        
print(f"➡️  Iniciando importação de {len(items)} itens para a tabela '$TABLE_NAME'...")

for item in items:
    try:
        dynamodb.put_item(TableName="$TABLE_NAME", Item=item)
    except Exception as e:
        print(f"⚠️  Erro ao inserir item na tabela '$TABLE_NAME': {e}")
        continue

print(f"✅ Importação concluída para '$TABLE_NAME'")
EOF

    # Executa o script Python
    python3 "$PYTHON_SCRIPT"

    # Remove o script temporário
    rm "$PYTHON_SCRIPT"
    echo ""
done

echo "🎉 Importações concluídas para todos os arquivos."
