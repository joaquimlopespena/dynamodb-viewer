#!/usr/bin/env python
"""
Validation script for the fixed batch importer
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
from src.services.batch_importer import DynamoDBBatchImporter

logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s | %(message)s'
)

def test_data_cleaning():
    """Test the new data cleaning functionality"""
    print("\n" + "="*80)
    print("TESTANDO LIMPEZA DE DADOS")
    print("="*80 + "\n")
    
    importer = DynamoDBBatchImporter('http://localhost:8000')
    
    test_items = [
        {
            "name": "test1",
            "score": 3.14,  # float
            "active": True,
            "date": datetime(2026, 1, 20),  # datetime
            "empty": "",  # empty string
            "none_val": None,  # None
            "tags": ["a", "", "b"],  # list with empty string
        },
        {
            "id": 42,
            "value": Decimal("123.45"),
            "nested": {"x": 1.5, "y": 2.0},
            "inf_val": float('inf'),
        }
    ]
    
    print("Item 1 (antes da limpeza):")
    for k, v in test_items[0].items():
        print(f"  {k:15} = {str(v)[:50]:50} ({type(v).__name__})")
    
    print("\nItem 1 (depois da limpeza):")
    cleaned = importer._clean_item(test_items[0])
    for k, v in cleaned.items():
        print(f"  {k:15} = {str(v)[:50]:50} ({type(v).__name__})")
    
    print("\n\nItem 2 (antes da limpeza):")
    for k, v in test_items[1].items():
        print(f"  {k:15} = {str(v)[:50]:50} ({type(v).__name__})")
    
    print("\nItem 2 (depois da limpeza):")
    cleaned = importer._clean_item(test_items[1])
    for k, v in cleaned.items():
        print(f"  {k:15} = {str(v)[:50]:50} ({type(v).__name__})")
    
    # Agora testar a serialização dos items limpos
    print("\n" + "="*80)
    print("TESTANDO SERIALIZAÇÃO APÓS LIMPEZA")
    print("="*80 + "\n")
    
    serializer = TypeSerializer()
    
    for idx, item in enumerate(test_items):
        print(f"Item {idx+1}:")
        cleaned = importer._clean_item(item)
        
        if not cleaned:
            print("  (item vazio após limpeza)")
            continue
        
        for k, v in list(cleaned.items())[:5]:
            try:
                result = serializer.serialize(v)
                print(f"  ✅ {k:15} → {result}")
            except Exception as e:
                print(f"  ❌ {k:15} → ERROR: {e}")
        print()

def test_format_detection():
    """Test DynamoDB format detection"""
    print("\n" + "="*80)
    print("TESTANDO DETECÇÃO DE FORMATO DYNAMODB")
    print("="*80 + "\n")
    
    importer = DynamoDBBatchImporter('http://localhost:8000')
    
    # Formato Python
    python_format = {
        "name": "John",
        "age": 30,
        "active": True
    }
    
    # Formato DynamoDB
    dynamodb_format = {
        "name": {"S": "John"},
        "age": {"N": "30"},
        "active": {"BOOL": True}
    }
    
    print(f"Formato Python:   {importer._is_dynamodb_format(python_format)}")
    print(f"Formato DynamoDB: {importer._is_dynamodb_format(dynamodb_format)}")

if __name__ == '__main__':
    test_data_cleaning()
    test_format_detection()
    print("\n✅ Testes concluídos!")
