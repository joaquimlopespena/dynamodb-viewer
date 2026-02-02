#!/usr/bin/env python
"""
Test script for batch import with detailed error reporting
"""

import sys
import logging
import os
from pathlib import Path

# Add src to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.services.batch_importer import DynamoDBBatchImporter

# Setup logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(levelname)-8s | %(name)s | %(message)s'
)

def test_import():
    """Test batch import"""
    
    # Configuração
    endpoint_url = 'http://localhost:8000'
    region_name = 'us-east-1'
    
    # Criar importador
    importer = DynamoDBBatchImporter(
        endpoint_url=endpoint_url,
        region_name=region_name
    )
    
    # Procurar arquivo JSON para testar
    test_files = list(Path('/home/joaquim/workspace/dynamodb-viewer').glob('*.json'))
    
    if not test_files:
        print("❌ Nenhum arquivo JSON encontrado!")
        return
    
    test_file = test_files[0]
    print(f"\n📁 Testando com: {test_file}")
    print(f"📊 Tamanho: {os.path.getsize(test_file) / (1024*1024):.2f} MB\n")
    
    # Tentar importar
    stats = importer.import_file(
        str(test_file),
        table_name='test_table'
    )
    
    print(f"\n✅ Resultado da importação:")
    print(f"   Sucesso: {stats['successful']}")
    print(f"   Falhas: {stats['failed']}")
    print(f"   Total: {stats['total_items']}")

if __name__ == '__main__':
    test_import()
