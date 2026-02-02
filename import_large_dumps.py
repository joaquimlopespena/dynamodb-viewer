#!/usr/bin/env python3
"""
Script CLI otimizado para importar dados JSON grandes para DynamoDB.
Ideal para arquivos maiores que 2.5GB com processamento paralelo e batch writes.

Uso:
    python3 import_large_dumps.py --file messages-dump.json --table messages
    python3 import_large_dumps.py --dir /path/to/dumps --endpoint http://localhost:8000
"""

import argparse
import sys
import os
from pathlib import Path

# Adicionar src ao path para imports
sys.path.insert(0, str(Path(__file__).parent))

from src.services.batch_importer import DynamoDBBatchImporter
import logging

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/tmp/dynamodb_import.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


def main():
    parser = argparse.ArgumentParser(
        description='Importa dados JSON para DynamoDB de forma otimizada.',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
EXEMPLOS:

  # Importar um arquivo grande
  python3 import_large_dumps.py --file messages-dump.json --table messages
  
  # Importar arquivo especificando endpoint
  python3 import_large_dumps.py --file messages-dump.json --table messages --endpoint http://localhost:8000
  
  # Importar todos os arquivos de um diretório
  python3 import_large_dumps.py --dir /home/joaquim/dumps/DynamoDB --pattern "*-dump.json"
  
  # Com customizações
  python3 import_large_dumps.py --file dados.json --table minha_tabela --endpoint http://localhost:8000 --region us-east-1

OTIMIZAÇÕES APLICADAS:
  ✓ Streaming de arquivo (não carrega tudo na memória)
  ✓ Batch write (25 itens por batch, limite do DynamoDB)
  ✓ Retry automático com backoff exponencial
  ✓ Suporte a diferentes estruturas JSON
  ✓ Progress bar em tempo real
  ✓ Logging detalhado

ESTRUTURAS JSON SUPORTADAS:
  ✓ {"Items": [...]}
  ✓ {"items": [...]}
  ✓ {"Records": [...]}
  ✓ {"messages": [...]}
  ✓ [...]  (lista direta)
        """
    )
    
    parser.add_argument('--file', help='Arquivo JSON para importar')
    parser.add_argument('--table', help='Nome da tabela DynamoDB')
    parser.add_argument('--dir', help='Diretório com arquivos JSON')
    parser.add_argument('--pattern', default='*-dump.json', 
                       help='Padrão de arquivo (default: *-dump.json)')
    parser.add_argument('--endpoint', default='http://localhost:8000',
                       help='Endpoint do DynamoDB (default: http://localhost:8000)')
    parser.add_argument('--region', default='us-east-1',
                       help='Região AWS (default: us-east-1)')
    parser.add_argument('--access-key', help='AWS Access Key ID (opcional para local)')
    parser.add_argument('--secret-key', help='AWS Secret Access Key (opcional para local)')
    
    args = parser.parse_args()
    
    if not args.file and not args.dir:
        parser.print_help()
        print("\n❌ Especifique --file ou --dir")
        sys.exit(1)
    
    # Criar importador
    logger.info("🚀 Iniciando DynamoDB Batch Importer Otimizado")
    logger.info(f"   Endpoint: {args.endpoint}")
    logger.info(f"   Região: {args.region}")
    
    importer = DynamoDBBatchImporter(
        endpoint_url=args.endpoint,
        region_name=args.region,
        access_key_id=args.access_key,
        secret_access_key=args.secret_key
    )
    
    # Importar dados
    if args.file:
        if not os.path.exists(args.file):
            logger.error(f"❌ Arquivo não encontrado: {args.file}")
            sys.exit(1)
        
        stats = importer.import_file(args.file, args.table)
        
        print("\n" + "="*80)
        print("📊 RESULTADO DA IMPORTAÇÃO")
        print("="*80)
        print(f"Arquivo:     {stats['file']}")
        print(f"Tabela:      {stats['table']}")
        print(f"Total:       {stats['total_items']} itens")
        print(f"Sucesso:     {stats['successful']} ✅")
        print(f"Falhas:      {stats['failed']} ❌")
        print(f"Tempo:       {stats['elapsed_seconds']:.2f}s")
        print(f"Velocidade:  {stats['items_per_second']:.1f} itens/s")
        print("="*80 + "\n")
        
        sys.exit(0 if stats['failed'] == 0 else 1)
    
    elif args.dir:
        if not os.path.isdir(args.dir):
            logger.error(f"❌ Diretório não encontrado: {args.dir}")
            sys.exit(1)
        
        import glob
        files = sorted(glob.glob(os.path.join(args.dir, args.pattern)))
        
        if not files:
            logger.warning(f"⚠️  Nenhum arquivo encontrado em {args.dir} com padrão '{args.pattern}'")
            sys.exit(1)
        
        logger.info(f"📂 Encontrados {len(files)} arquivo(s)")
        
        all_stats = []
        for file_path in files:
            stats = importer.import_file(file_path)
            all_stats.append(stats)
        
        # Imprimir resumo
        print("\n" + "="*80)
        print("📊 RESUMO DAS IMPORTAÇÕES")
        print("="*80)
        
        total_success = 0
        total_failed = 0
        total_time = 0
        
        for stats in all_stats:
            total_success += stats['successful']
            total_failed += stats['failed']
            total_time += stats['elapsed_seconds']
            
            table = stats['table']
            success = stats['successful']
            failed = stats['failed']
            rate = stats['items_per_second']
            
            status = "✅" if failed == 0 else "⚠️"
            print(f"{status} {table:30} | {success:8} ok | {failed:6} erros | {rate:8.1f} itens/s")
        
        print("="*80)
        overall_rate = total_success / total_time if total_time > 0 else 0
        print(f"🎉 TOTAL: {total_success} itens importados, {total_failed} falhas, "
              f"{total_time:.1f}s ({overall_rate:.1f} itens/s)")
        print("="*80 + "\n")
        
        sys.exit(0 if total_failed == 0 else 1)


if __name__ == '__main__':
    main()
