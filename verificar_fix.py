#!/usr/bin/env python3
"""
Script de Verificação Rápida - Performance Fix
Valida se todas as mudanças foram aplicadas corretamente
"""

import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

def check_imports():
    """Verifica se os imports funcionam"""
    try:
        from src.services.dynamodb_service import DynamoDBService
        print("✅ DynamoDBService importado com sucesso")
        return True
    except Exception as e:
        print(f"❌ Erro ao importar: {e}")
        return False

def check_function_exists():
    """Verifica se a nova função existe"""
    try:
        from src.services.dynamodb_service import DynamoDBService
        service = DynamoDBService()
        
        if hasattr(service, 'convert_filter_value'):
            print("✅ Função convert_filter_value existe")
            return True
        else:
            print("❌ Função convert_filter_value não encontrada")
            return False
    except Exception as e:
        print(f"❌ Erro ao verificar função: {e}")
        return False

def check_function_works():
    """Testa se a função funciona"""
    try:
        from src.services.dynamodb_service import DynamoDBService
        service = DynamoDBService()
        
        # Test case 1
        result = service.convert_filter_value("123", "Number")
        if result == 123 and isinstance(result, int):
            print("✅ Conversão de String para int funciona")
        else:
            print(f"❌ Conversão falhou: esperado 123 (int), recebido {result} ({type(result).__name__})")
            return False
        
        # Test case 2
        result = service.convert_filter_value("true", "Boolean")
        if result is True:
            print("✅ Conversão de String para Boolean funciona")
        else:
            print(f"❌ Conversão falhou: esperado True, recebido {result}")
            return False
        
        return True
    except Exception as e:
        print(f"❌ Erro ao testar função: {e}")
        return False

def check_schema_access():
    """Verifica se o schema é acessível (simulado)"""
    try:
        # Apenas verifica sintaxe
        from src.services.dynamodb_service import DynamoDBService
        
        # Procura pelo código que acessa key_schema
        import inspect
        source = inspect.getsource(DynamoDBService.query_with_filters)
        
        if "hasattr(self.current_table, 'key_schema')" in source:
            print("✅ Acesso correto ao key_schema usando hasattr")
            return True
        else:
            print("❌ Acesso ao key_schema não encontrado ou incorreto")
            return False
    except Exception as e:
        print(f"❌ Erro ao verificar schema access: {e}")
        return False

def check_logging():
    """Verifica se o logging foi adicionado"""
    try:
        import inspect
        from src.services.dynamodb_service import DynamoDBService
        
        source = inspect.getsource(DynamoDBService.query_with_filters)
        
        checks = [
            ("✓ Usando Primary Key shortcut", "Logging de PK shortcut"),
            ("→ Usando query()", "Logging de estratégia"),
            ("✓ query() retornou", "Logging de resultado de query"),
            ("Query concluída em", "Logging de tempo"),
        ]
        
        all_found = True
        for check_text, description in checks:
            if check_text in source:
                print(f"✅ {description}: encontrado")
            else:
                print(f"❌ {description}: NÃO encontrado")
                all_found = False
        
        return all_found
    except Exception as e:
        print(f"❌ Erro ao verificar logging: {e}")
        return False

def main():
    """Executa todas as verificações"""
    print("=" * 80)
    print("VERIFICAÇÃO DE PERFORMANCE FIX - DynamoDB Viewer")
    print("=" * 80)
    print()
    
    checks = [
        ("Imports", check_imports),
        ("Função Exists", check_function_exists),
        ("Função Works", check_function_works),
        ("Schema Access", check_schema_access),
        ("Logging", check_logging),
    ]
    
    results = []
    for name, check_func in checks:
        print(f"\n🔍 Verificando: {name}")
        print("-" * 80)
        result = check_func()
        results.append((name, result))
    
    print()
    print("=" * 80)
    print("RESULTADO FINAL")
    print("=" * 80)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✅ PASSOU" if result else "❌ FALHOU"
        print(f"{status:12} | {name}")
    
    print()
    print(f"Total: {passed}/{total} verificações passaram")
    
    if passed == total:
        print()
        print("🎉 TODAS AS VERIFICAÇÕES PASSARAM!")
        print("O fix está pronto para uso em produção.")
        return 0
    else:
        print()
        print("⚠️  ALGUMAS VERIFICAÇÕES FALHARAM")
        print("Consulte os erros acima e verifique o código.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
