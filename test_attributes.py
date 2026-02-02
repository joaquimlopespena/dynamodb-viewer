#!/usr/bin/env python
"""
Identify the exact attribute causing 'Invalid attribute value type' error
"""

import sys
import json
sys.path.insert(0, '/home/joaquim/workspace/dynamodb-viewer')

from src.services.batch_importer import DynamoDBBatchImporter

def test_batch_write_one_by_one():
    """Test each item individually to find which one fails"""
    
    print("\n" + "="*80)
    print("TESTING BATCH WRITE - ONE BY ONE")
    print("="*80)
    
    importer = DynamoDBBatchImporter('http://localhost:8000')
    
    # Sample items from the logs
    sample_items = [
        {
            "updated_at": {"S": "2025-09-15 23:58:39"},
            "wa_id": {"S": "5511932340180"},
            "blocked": {"BOOL": False},
            "created_at": {"S": "2025-09-15 23:58:39"},
            "id": {"S": "dba4f8d6-22d2-4e1a-999e-fd35e82fddeb"}
        },
        {
            "updated_at": {"S": "2026-01-07 12:00:38"},
            "wa_id": {"S": "553497747030"},
            "created_at": {"S": "2026-01-06 15:29:59"},
            "id": {"S": "331037d4-463d-42a5-96a1-d4c1c749e7f1"},
            "email": {"NULL": True}
        }
    ]
    
    print("\nTesting individual attributes:")
    print("-" * 80)
    
    for item_idx, item in enumerate(sample_items):
        print(f"\n[Item {item_idx + 1}]")
        
        # Validate the item
        is_valid = importer._validate_dynamodb_item(item, item_idx)
        print(f"  Validation: {'✅ PASS' if is_valid else '❌ FAIL'}")
        
        if is_valid:
            # Try to send to DynamoDB (this is where the error occurs)
            print(f"  Trying batch write...")
            success, failed = importer.batch_write_items('contacts', [item])
            print(f"  Result: {success} success, {failed} failed")
            if failed > 0:
                print(f"  ❌ FAILED AT DYNAMODB LAYER!")
                print(f"  Item: {json.dumps(item, indent=2)}")

def test_attribute_by_attribute():
    """Test each attribute individually"""
    
    print("\n" + "="*80)
    print("TESTING ATTRIBUTES ONE BY ONE")
    print("="*80)
    
    importer = DynamoDBBatchImporter('http://localhost:8000')
    
    # Template item with one attribute at a time
    base_id = {"id": {"S": "test-id"}}
    
    attributes_to_test = [
        ("String", {"S": "test"}),
        ("Number", {"N": "123"}),
        ("Number as float string", {"N": "123.45"}),
        ("Boolean true", {"BOOL": True}),
        ("Boolean false", {"BOOL": False}),
        ("Null", {"NULL": True}),
        ("Empty string", {"S": ""}),
        ("Datetime string", {"S": "2025-09-15 23:58:39"}),
        ("ISO datetime", {"S": "2025-09-15T23:58:39"}),
    ]
    
    print("\nAttribute type testing:")
    print("-" * 80)
    
    for attr_name, attr_value in attributes_to_test:
        test_item = {"id": {"S": f"test-{attr_name.lower()}"}, "value": attr_value}
        
        print(f"\n{attr_name}:")
        print(f"  Value: {json.dumps(attr_value)}")
        
        is_valid = importer._validate_dynamodb_item(test_item, 0)
        print(f"  Validation: {'✅ PASS' if is_valid else '❌ FAIL'}")
        
        if is_valid:
            try:
                success, failed = importer.batch_write_items('contacts', [test_item])
                status = "✅ Success" if failed == 0 else "❌ Failed"
                print(f"  Batch write: {status}")
            except Exception as e:
                print(f"  Batch write: ❌ Exception - {e}")

if __name__ == '__main__':
    test_batch_write_one_by_one()
    test_attribute_by_attribute()
    
    print("\n" + "="*80)
    print("Check output above to identify the problematic attribute type")
    print("="*80 + "\n")
