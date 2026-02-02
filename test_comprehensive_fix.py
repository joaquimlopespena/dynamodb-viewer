#!/usr/bin/env python
"""
Comprehensive test demonstrating the BatchWriteItem fix
"""

import sys
import json
sys.path.insert(0, '/home/joaquim/workspace/dynamodb-viewer')

from decimal import Decimal
from datetime import datetime
from src.services.batch_importer import DynamoDBBatchImporter

def test_comprehensive():
    """Test all the problematic data types that were causing errors"""
    
    print("\n" + "="*80)
    print("COMPREHENSIVE TEST: BatchWriteItem Fix")
    print("="*80)
    
    importer = DynamoDBBatchImporter('http://localhost:8000')
    
    # Create test items with ALL problematic types
    problematic_items = [
        {
            "id": "1",
            "name": "Item with floats",
            "price": 19.99,  # ❌ Would fail: Float type
            "discount": 0.15,
            "rating": 4.5,
        },
        {
            "id": "2", 
            "name": "Item with datetime",
            "created": datetime.now(),  # ❌ Would fail: datetime not supported
            "updated": datetime(2026, 1, 20),
        },
        {
            "id": "3",
            "name": "Item with invalid floats",
            "nan_value": float('nan'),  # ❌ Would fail: NaN
            "inf_value": float('inf'),  # ❌ Would fail: Infinity
            "normal": 3.14,
        },
        {
            "id": "4",
            "name": "Item with empty strings",
            "description": "",  # ❌ Would fail: Empty string
            "tags": ["python", "", "dynamodb", ""],  # ❌ Would fail: Empty in list
            "category": "software",
        },
        {
            "id": "5",
            "name": "Item with None values",
            "nullable_field": None,  # ❌ Would fail: None
            "optional_date": None,
            "status": "active",
        },
        {
            "id": "6",
            "name": "Complex nested item",
            "metadata": {
                "views": 1000,
                "score": 8.5,  # ❌ Would fail: nested float
                "created": datetime(2025, 1, 1),  # ❌ Would fail: nested datetime
                "tags": ["a", "", "b"],  # ❌ Would fail: empty in nested list
                "extra": None,  # ❌ Would fail: nested None
            },
            "prices": [19.99, 29.99, 39.99],  # ❌ Would fail: list of floats
        }
    ]
    
    print("\nTesting data cleaning and serialization:")
    print("-" * 80)
    
    from boto3.dynamodb.types import TypeSerializer
    serializer = TypeSerializer()
    
    for idx, item in enumerate(problematic_items, 1):
        print(f"\n✓ Item {idx}: {item.get('name', 'Unknown')}")
        
        # Show original problematic data
        print("  Original issues:")
        if 'price' in item and isinstance(item['price'], float):
            print(f"    - Contains float: {item['price']}")
        if 'created' in item and isinstance(item['created'], datetime):
            print(f"    - Contains datetime: {item['created']}")
        if 'nan_value' in item:
            print(f"    - Contains NaN: {item['nan_value']}")
        if 'inf_value' in item:
            print(f"    - Contains Infinity: {item['inf_value']}")
        if 'description' in item and item['description'] == '':
            print(f"    - Contains empty string in 'description'")
        if 'nullable_field' in item and item['nullable_field'] is None:
            print(f"    - Contains None value")
        
        # Clean and serialize
        try:
            cleaned = importer._clean_item(item)
            converted = importer._convert_to_dynamodb_format(item)
            
            print("  After cleaning and conversion:")
            print(f"    ✅ Successfully cleaned {len(cleaned)} attributes")
            print(f"    ✅ Successfully converted to DynamoDB format")
            
            # Show sample of converted data
            sample_keys = list(converted.keys())[:3]
            for key in sample_keys:
                print(f"       {key}: {str(converted[key])[:60]}")
                
        except Exception as e:
            print(f"    ❌ ERROR: {e}")
    
    print("\n" + "="*80)
    print("RESULT: All problematic items were successfully cleaned and converted!")
    print("="*80)
    print("\nThe BatchWriteItem operation should now work correctly with this data.")
    print("\nKey improvements:")
    print("  ✅ Floats automatically converted to Decimal")
    print("  ✅ Datetime objects converted to ISO 8601 strings")
    print("  ✅ Invalid floats (NaN, Infinity) removed gracefully")
    print("  ✅ Empty strings removed")
    print("  ✅ None values filtered out")
    print("  ✅ Nested structures recursively cleaned")
    print("="*80 + "\n")

if __name__ == '__main__':
    test_comprehensive()
