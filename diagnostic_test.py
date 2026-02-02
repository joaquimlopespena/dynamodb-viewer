#!/usr/bin/env python
"""
Diagnostic script to identify the exact problem with batch import
"""

import sys
import json
import logging
from pathlib import Path
from decimal import Decimal
from datetime import datetime
import math

# Setup
sys.path.insert(0, '/home/joaquim/workspace/dynamodb-viewer')

from boto3.dynamodb.types import TypeSerializer

logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s | %(message)s'
)

def test_serialization():
    """Test serialization of various types"""
    print("\n" + "="*80)
    print("TESTANDO SERIALIZAÇÃO DE TIPOS")
    print("="*80 + "\n")
    
    serializer = TypeSerializer()
    
    test_cases = [
        ("String", "hello"),
        ("Number", 42),
        ("Float", 3.14),
        ("Boolean", True),
        ("None", None),
        ("List", [1, 2, 3]),
        ("Dict", {"key": "value"}),
        ("Decimal", Decimal("123.45")),
        ("DateTime", datetime.now()),
        ("Empty String", ""),
        ("NaN", float('nan')),
        ("Infinity", float('inf')),
        ("Negative Infinity", float('-inf')),
        ("Empty List", []),
        ("Empty Dict", {}),
    ]
    
    for name, value in test_cases:
        try:
            result = serializer.serialize(value)
            print(f"✅ {name:20} | {str(value)[:50]:50} → {result}")
        except Exception as e:
            print(f"❌ {name:20} | {str(value)[:50]:50} → ERROR: {e}")

def test_sample_json():
    """Test with a sample JSON file if it exists"""
    print("\n" + "="*80)
    print("TESTANDO COM ARQUIVO JSON")
    print("="*80 + "\n")
    
    json_files = list(Path('/home/joaquim/workspace/dynamodb-viewer').glob('*.json'))
    
    if not json_files:
        print("❌ Nenhum arquivo JSON encontrado na pasta raiz")
        return
    
    test_file = json_files[0]
    print(f"📁 Testando com: {test_file}")
    print(f"📊 Tamanho: {test_file.stat().st_size / (1024*1024):.2f} MB\n")
    
    try:
        # Ler apenas os primeiros 2 itens
        with open(test_file, 'r') as f:
            content = f.read(2000)  # Primeiros 2000 bytes
            
            # Tentar detectar estrutura
            if content.strip().startswith('['):
                print("📌 Formato: Array JSON direto\n")
                data = json.loads(content + ']')  # Tentar fechar o array
            else:
                print("📌 Formato: Objeto JSON com propriedades\n")
                data = json.loads(content[:content.rfind('}')] + '}')
            
            if isinstance(data, list):
                items = data[:2]
            elif isinstance(data, dict):
                for key in ['Items', 'items', 'Records', 'records']:
                    if key in data:
                        items = data[key][:2] if isinstance(data[key], list) else [data[key]]
                        break
                else:
                    items = [data]
            
            print(f"Primeiros itens encontrados: {len(items)}\n")
            
            serializer = TypeSerializer()
            for idx, item in enumerate(items):
                print(f"Item {idx+1}:")
                if isinstance(item, dict):
                    for k, v in list(item.items())[:5]:  # Primeiros 5 campos
                        try:
                            result = serializer.serialize(v)
                            print(f"  {k}: {str(v)[:40]:40} ✅")
                        except Exception as e:
                            print(f"  {k}: {str(v)[:40]:40} ❌ {e}")
                else:
                    print(f"  Tipo: {type(item).__name__}")
                print()
    
    except Exception as e:
        print(f"❌ Erro ao processar arquivo: {e}")

if __name__ == '__main__':
    test_serialization()
    test_sample_json()
