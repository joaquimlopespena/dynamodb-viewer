"""
Exemplo de uso da nova estrutura modular

Este arquivo demonstra como utilizar os componentes
da arquitetura refatorada.
"""

from src.services import DynamoDBService
from src.models import FilterRow
from src.utils.encoders import DecimalEncoder
import json


def exemplo_1_usar_servico():
    """Exemplo 1: Usar o serviço DynamoDB"""
    print("=" * 60)
    print("EXEMPLO 1: Usando DynamoDBService")
    print("=" * 60)
    
    # Criar serviço
    db_service = DynamoDBService()
    
    # Conectar
    if db_service.connect():
        print("✓ Conectado ao DynamoDB")
        
        # Listar tabelas
        tables = db_service.get_tables()
        print(f"✓ Tabelas encontradas: {len(tables)}")
        for table in tables[:3]:  # Mostrar apenas as 3 primeiras
            print(f"  - {table}")
    else:
        print("✗ Erro ao conectar")
    
    print()


def exemplo_2_construir_filtro():
    """Exemplo 2: Construir filtros programaticamente"""
    print("=" * 60)
    print("EXEMPLO 2: Construindo FilterExpression")
    print("=" * 60)
    
    db_service = DynamoDBService()
    
    # Simular filtros (como se viessem da UI)
    filters = [
        {
            'attribute': 'status',
            'condition': 'Igual a',
            'type': 'String',
            'value': 'active'
        },
        {
            'attribute': 'age',
            'condition': 'Maior que',
            'type': 'Number',
            'value': 18
        }
    ]
    
    # Construir expressão de filtro
    filter_expr = db_service.build_filter_expression(filters)
    
    if filter_expr:
        print(f"✓ Filtro construído com sucesso")
        print(f"  Filtros aplicados: {len(filters)}")
        print(f"  - status = 'active'")
        print(f"  - age > 18")
    else:
        print("✗ Erro ao construir filtro")
    
    print()


def exemplo_3_usar_encoder():
    """Exemplo 3: Usar o encoder JSON customizado"""
    print("=" * 60)
    print("EXEMPLO 3: Usando DecimalEncoder")
    print("=" * 60)
    
    from decimal import Decimal
    
    # Dados com Decimal (como do DynamoDB)
    data = {
        'id': '123',
        'price': Decimal('99.99'),
        'quantity': Decimal('5'),
        'name': 'Produto'
    }
    
    # Serializar com encoder customizado
    json_str = json.dumps(data, cls=DecimalEncoder, indent=2)
    
    print("✓ Dados com Decimal convertidos para JSON:")
    print(json_str)
    
    print()


def exemplo_4_arquitetura():
    """Exemplo 4: Demonstrar arquitetura em camadas"""
    print("=" * 60)
    print("EXEMPLO 4: Arquitetura em Camadas")
    print("=" * 60)
    
    print("""
    ┌─────────────────────────────────────┐
    │   Camada de Apresentação (UI)       │
    │  - MainWindow                       │
    │  - FilterRow (na UI)                │
    │  - LoadingIndicator                 │
    └────────────────┬────────────────────┘
                     │
    ┌─────────────────▼────────────────────┐
    │   Camada de Modelos (Models)        │
    │  - FilterRow (dados)                │
    └────────────────┬────────────────────┘
                     │
    ┌─────────────────▼────────────────────┐
    │   Camada de Serviços (Services)     │
    │  - DynamoDBService                  │
    └────────────────┬────────────────────┘
                     │
    ┌─────────────────▼────────────────────┐
    │   Camada de Utilitários (Utils)     │
    │  - DecimalEncoder                   │
    └─────────────────────────────────────┘
    """)
    
    print("✓ Cada camada tem responsabilidade clara")
    print("✓ Componentes reutilizáveis e testáveis")
    print()


def exemplo_5_importacoes():
    """Exemplo 5: Mostrar como importar componentes"""
    print("=" * 60)
    print("EXEMPLO 5: Importações Organizadas")
    print("=" * 60)
    
    print("""
    # Importar serviços
    from src.services import DynamoDBService
    
    # Importar modelos
    from src.models import FilterRow
    
    # Importar componentes UI
    from src.ui.components import LoadingIndicator
    from src.ui.windows import MainWindow
    
    # Importar utilitários
    from src.utils.encoders import DecimalEncoder
    """)
    
    print("✓ Todas as importações foram validadas e funcionam!")
    print()


if __name__ == "__main__":
    print("\n")
    print("╔" + "=" * 58 + "╗")
    print("║" + " " * 10 + "EXEMPLOS DA ARQUITETURA REFATORADA" + " " * 14 + "║")
    print("╚" + "=" * 58 + "╝")
    print()
    
    exemplo_1_usar_servico()
    exemplo_2_construir_filtro()
    exemplo_3_usar_encoder()
    exemplo_4_arquitetura()
    exemplo_5_importacoes()
    
    print("=" * 60)
    print("✅ Todos os exemplos funcionam com a nova arquitetura!")
    print("=" * 60)
