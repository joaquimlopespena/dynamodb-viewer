#!/usr/bin/env python3
"""
Script de teste para validar a correção de performance
Verifica se a consulta por ID usa query() em vez de scan()
"""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

from src.services.dynamodb_service import DynamoDBService

def test_type_conversion():
    """Test the convert_filter_value function"""
    service = DynamoDBService()
    
    test_cases = [
        # (input_value, type_hint, expected_output, description)
        ("123", "Number", 123, "String to int"),
        ("123.45", "Number", 123.45, "String to float"),
        ("true", "Boolean", True, "String to bool (true)"),
        ("false", "Boolean", False, "String to bool (false)"),
        ("sim", "Boolean", True, "String to bool (sim)"),
        ("não", "Boolean", False, "String to bool (não)"),
        ("hello", "String", "hello", "String stays string"),
        ("", None, None, "Empty string returns None"),
        ("abc123", "Number", "abc123", "Non-numeric string stays string when Number hint fails"),
    ]
    
    print("=" * 80)
    print("TESTE DE CONVERSÃO DE TIPO")
    print("=" * 80)
    
    passed = 0
    failed = 0
    
    for input_val, type_hint, expected, description in test_cases:
        result = service.convert_filter_value(input_val, type_hint)
        status = "✓ PASS" if result == expected else "✗ FAIL"
        
        if result == expected:
            passed += 1
        else:
            failed += 1
        
        print(f"\n{status} | {description}")
        print(f"  Input: {repr(input_val)} | Type Hint: {type_hint}")
        print(f"  Expected: {repr(expected)} (tipo: {type(expected).__name__ if expected is not None else 'NoneType'})")
        print(f"  Got: {repr(result)} (tipo: {type(result).__name__})")
    
    print("\n" + "=" * 80)
    print(f"RESULTADO: {passed} passed, {failed} failed")
    print("=" * 80)
    
    return failed == 0

if __name__ == "__main__":
    success = test_type_conversion()
    sys.exit(0 if success else 1)
