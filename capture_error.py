#!/usr/bin/env python
"""
Capture the ACTUAL error happening during batch import
Run this with: python capture_error.py <path_to_json_file> <table_name>
"""

import sys
import json
import logging

sys.path.insert(0, '/home/joaquim/workspace/dynamodb-viewer')

from src.services.batch_importer import DynamoDBBatchImporter
from boto3.dynamodb.types import TypeSerializer

# Setup detailed logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(levelname)-8s | %(name)s | %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('/tmp/batch_import_debug.log')
    ]
)

logger = logging.getLogger(__name__)

def analyze_json_file(file_path):
    """Analyze the JSON file structure"""
    print("\n" + "="*80)
    print("ANALYZING JSON FILE")
    print("="*80)
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            # Read first 10 items
            content = f.read(100000)  # First 100KB
            f.seek(0)
            
            # Try to parse
            if content.strip().startswith('['):
                data = json.loads(content[:content.rfind(']')+1])
            else:
                data = json.loads(content[:content.rfind('}')+1])
            
            if isinstance(data, list):
                items = data
            elif isinstance(data, dict):
                # Find items list
                for key in ['Items', 'items', 'Records', 'records', 'data']:
                    if key in data and isinstance(data[key], list):
                        items = data[key]
                        break
                else:
                    items = [data]
            
            print(f"File size: {f.seek(0, 2) / (1024*1024):.2f} MB")
            print(f"Items found: {len(items)}")
            print(f"\nFirst item structure:")
            print(json.dumps(items[0], indent=2, default=str)[:500])
            
            return items[:10]  # Return first 10
    
    except Exception as e:
        print(f"ERROR reading file: {e}")
        return None

def test_batch_import(file_path, table_name):
    """Test batch import with detailed error capture"""
    print("\n" + "="*80)
    print("TESTING BATCH IMPORT WITH DEBUG LOGGING")
    print("="*80 + "\n")
    
    importer = DynamoDBBatchImporter('http://localhost:8000')
    serializer = TypeSerializer()
    
    # Get items
    items = analyze_json_file(file_path)
    
    if not items:
        return
    
    print("\n" + "="*80)
    print("TESTING CONVERSION AND SERIALIZATION")
    print("="*80 + "\n")
    
    for idx, item in enumerate(items[:3]):  # Test first 3 items
        print(f"\n[ITEM {idx+1}]")
        print(f"  Type: {type(item).__name__}")
        
        if isinstance(item, dict):
            print(f"  Keys: {list(item.keys())}")
            print(f"  Original sample: {json.dumps(item, default=str, indent=2)[:300]}")
            
            try:
                # Step 1: Clean
                print(f"\n  STEP 1: Cleaning...")
                cleaned = importer._clean_item(item)
                print(f"  ✅ Cleaned: {len(cleaned)} attributes")
                if cleaned:
                    first_attr = next(iter(cleaned.items()))
                    print(f"     Sample: {first_attr[0]} = {str(first_attr[1])[:50]}")
                
                # Step 2: Convert
                print(f"\n  STEP 2: Converting to DynamoDB format...")
                converted = importer._convert_to_dynamodb_format(item)
                print(f"  ✅ Converted: {len(converted)} attributes")
                if converted:
                    first_attr = next(iter(converted.items()))
                    print(f"     Sample: {first_attr[0]} = {str(first_attr[1])[:80]}")
                
                # Step 3: Validate each attribute
                print(f"\n  STEP 3: Validating DynamoDB format...")
                for key, value in list(converted.items())[:3]:
                    try:
                        # Check if it's valid DynamoDB format
                        if not isinstance(value, dict):
                            print(f"     ❌ {key}: NOT a dict - {type(value).__name__}")
                        elif len(value) != 1:
                            print(f"     ❌ {key}: Multiple keys in dict - {list(value.keys())}")
                        else:
                            type_key = list(value.keys())[0]
                            if type_key not in ['S', 'N', 'B', 'SS', 'NS', 'BS', 'M', 'L', 'BOOL', 'NULL', 'MS']:
                                print(f"     ❌ {key}: Invalid type key - {type_key}")
                            else:
                                val_str = str(value[type_key])[:40]
                                print(f"     ✅ {key}: {type_key} = {val_str}")
                    except Exception as e:
                        print(f"     ❌ {key}: {e}")
            
            except Exception as e:
                print(f"  ❌ ERROR: {e}")
                import traceback
                traceback.print_exc()

def main():
    if len(sys.argv) < 2:
        print("Usage: python capture_error.py <json_file> [table_name]")
        print("\nExample:")
        print("  python capture_error.py messages-dump.json messages")
        sys.exit(1)
    
    file_path = sys.argv[1]
    table_name = sys.argv[2] if len(sys.argv) > 2 else 'test_table'
    
    test_batch_import(file_path, table_name)
    
    print("\n" + "="*80)
    print("Debug log saved to: /tmp/batch_import_debug.log")
    print("="*80 + "\n")

if __name__ == '__main__':
    main()
