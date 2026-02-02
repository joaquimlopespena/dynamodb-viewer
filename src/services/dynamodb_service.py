"""DynamoDB Service for database operations"""

import json
import time
import boto3
import os
from boto3.dynamodb.conditions import Key, Attr
from botocore.exceptions import ClientError
from src.utils.encoders import DecimalEncoder
from src.config import config
from src.services.batch_importer import DynamoDBBatchImporter


class DynamoDBService:
    """Service class for DynamoDB operations"""
    
    def __init__(self):
        """Initialize DynamoDB service"""
        self.dynamodb = None
        self.current_table = None
        self.last_index_error = None
        # Cache key_schema per table (avoids repeated DescribeTable; None = no permission)
        self._key_schema_cache = {}
    
    def connect(self):
        """Connect to DynamoDB using AWS CLI credentials or Local DynamoDB
        
        Returns:
            bool: True if connection successful, False otherwise
        """
        try:
            dynamodb_config = config.get_dynamodb_config()
            print(f"[DynamoDBService.connect] Configuração: {dynamodb_config}")
            self.dynamodb = boto3.resource('dynamodb', **dynamodb_config)
            print(f"[DynamoDBService.connect] Testando conexão...")
            list(self.dynamodb.tables.limit(1))
            print(f"[DynamoDBService.connect] ✓ Conexão bem-sucedida!")
            return True
        except Exception as e:
            print(f"[DynamoDBService.connect] ✗ ERRO: {str(e)}")
            return False
    
    def is_connected(self):
        """Check if connected to DynamoDB
        
        Returns:
            bool: True if connected
        """
        return self.dynamodb is not None
    
    def get_tables(self):
        """Get list of all tables
        
        Returns:
            list: List of table names
        """
        if not self.is_connected():
            return []
        
        try:
            tables = list(self.dynamodb.tables.all())
            return [table.name for table in tables]
        except Exception:
            return []
    
    def select_table(self, table_name):
        """Select a table to work with
        
        Args:
            table_name: Name of the table
        """
        if self.is_connected():
            self.current_table = self.dynamodb.Table(table_name)
    
    def _get_key_schema_safe(self):
        """
        Obtém PK/SK da tabela via DescribeTable, sem lançar exceção.
        Se o usuário não tiver dynamodb:DescribeTable, retorna (None, None) e
        loga mensagem clara (sem traceback).
        
        Returns:
            tuple: (pk_key, sk_key) ou (None, None) se sem permissão/erro
        """
        if not self.current_table:
            return None, None
        
        table_name = self.current_table.name
        if table_name in self._key_schema_cache:
            cached = self._key_schema_cache[table_name]
            return cached if cached else (None, None)
        
        try:
            client = self.dynamodb.meta.client
            resp = client.describe_table(TableName=table_name)
            key_schema = resp.get('Table', {}).get('KeySchema', []) or []
            pk_key = None
            sk_key = None
            for k in key_schema:
                if k.get('KeyType') == 'HASH':
                    pk_key = k.get('AttributeName')
                elif k.get('KeyType') == 'RANGE':
                    sk_key = k.get('AttributeName')
            self._key_schema_cache[table_name] = (pk_key, sk_key)
            return pk_key, sk_key
        except ClientError as e:
            if e.response.get('Error', {}).get('Code') == 'AccessDeniedException':
                self._key_schema_cache[table_name] = None
                print(
                    "[DynamoDB] ⚠ Sem permissão dynamodb:DescribeTable. "
                    "Consultas usam scan (lento). Adicione essa permissão na IAM para consultas rápidas."
                )
                return None, None
            self._key_schema_cache[table_name] = None
            print(f"[DynamoDB] Erro ao obter schema: {e}")
            return None, None
        except Exception as e:
            self._key_schema_cache[table_name] = None
            print(f"[DynamoDB] Erro ao obter schema: {e}")
            return None, None
    
    def get_table_attributes(self, limit=50):
        """Get all attributes from a table
        
        Args:
            limit: Number of items to scan for attribute discovery
            
        Returns:
            list: Sorted list of unique attribute names
        """
        if not self.current_table:
            return []
        
        try:
            response = self.current_table.scan(Limit=limit)
            items = response.get('Items', [])
            
            all_keys = set()
            for item in items:
                all_keys.update(item.keys())
            
            return sorted(list(all_keys))
        except Exception:
            return []
    
    def convert_filter_value(self, value, type_hint=None):
        """Convert filter value to appropriate Python type
        
        Args:
            value: Value from filter (usually string from UI)
            type_hint: Optional type hint ('Number', 'Boolean', 'String')
            
        Returns:
            Converted value or original if conversion fails
        """
        if value is None or value == "":
            return None
            
        # Try to convert based on type hint
        if type_hint == 'Number':
            try:
                if '.' in str(value):
                    return float(value)
                else:
                    return int(value)
            except (ValueError, TypeError):
                return value
        elif type_hint == 'Boolean':
            if isinstance(value, str):
                return value.lower() in ['true', '1', 'sim', 'yes', 'verdadeiro']
            return bool(value)
        
        # Try to auto-detect type
        if isinstance(value, str):
            # Try number
            try:
                if '.' in value:
                    return float(value)
                else:
                    return int(value)
            except (ValueError, TypeError):
                pass
            
            # Try boolean
            if value.lower() in ['true', '1', 'sim', 'yes', 'verdadeiro']:
                return True
            if value.lower() in ['false', '0', 'não', 'no', 'falso']:
                return False
        
        return value
    
    def get_table_indexes(self):
        """Get all available indexes (GSI and LSI) for current table
        
        Returns:
            dict: Dictionary with 'gsi' and 'lsi' lists containing index names
        """
        if not self.current_table:
            return {"gsi": [], "lsi": []}

        try:
            # Use low-level client to describe table (more reliable across boto3 versions/endpoints)
            client = getattr(self.dynamodb, 'meta').client
            resp = client.describe_table(TableName=self.current_table.name)
            table_desc = resp.get('Table', {})

            gsi_defs = table_desc.get('GlobalSecondaryIndexes') or []
            lsi_defs = table_desc.get('LocalSecondaryIndexes') or []

            gsi_indexes = [idx.get('IndexName') for idx in gsi_defs if idx.get('IndexName')]
            lsi_indexes = [idx.get('IndexName') for idx in lsi_defs if idx.get('IndexName')]
            self.last_index_error = None

            return {"gsi": gsi_indexes, "lsi": lsi_indexes}
        except Exception as e:
            err = str(e)
            print(f"[DynamoDBService.get_table_indexes] Erro ao obter índices: {err}")
            # Save last error so UI can display a helpful message
            self.last_index_error = err
            return {"gsi": [], "lsi": []}
    
    def get_table_info(self):
        """Get information about current table
        
        Returns:
            dict: Table information
        """
        if not self.current_table:
            return {}
        
        try:
            self.current_table.reload()
            
            return {
                "Nome": self.current_table.name,
                "Status": self.current_table.table_status,
                "Item Count": self.current_table.item_count,
                "Tamanho (bytes)": self.current_table.table_size_bytes,
                "Criação": str(self.current_table.creation_date_time),
                "Chave Primária": self.current_table.key_schema,
                "Atributos": self.current_table.attribute_definitions,
                "Global Secondary Indexes": (
                    self.current_table.global_secondary_indexes or "Nenhum"
                ),
                "Local Secondary Indexes": (
                    self.current_table.local_secondary_indexes or "Nenhum"
                ),
            }
        except Exception:
            return {}
    
    def build_filter_expression(self, filters):
        """Build DynamoDB FilterExpression from filter list
        
        Args:
            filters: List of filter dictionaries with keys: attribute, condition, value
            
        Returns:
            FilterExpression or None: Combined filter expression
        """
        filter_expressions = []
        
        for filter_data in filters:
            if not filter_data:
                continue
            
            attr = filter_data.get('attribute')
            condition = filter_data.get('condition')
            value = filter_data.get('value')
            
            if not attr:
                continue
            
            # Constrói a condição usando boto3.dynamodb.conditions
            if condition == "Igual a":
                filter_expressions.append(Attr(attr).eq(value))
            elif condition == "Diferente de":
                filter_expressions.append(Attr(attr).ne(value))
            elif condition == "Menor que":
                filter_expressions.append(Attr(attr).lt(value))
            elif condition == "Menor que ou igual a":
                filter_expressions.append(Attr(attr).lte(value))
            elif condition == "Maior que":
                filter_expressions.append(Attr(attr).gt(value))
            elif condition == "Maior que ou igual a":
                filter_expressions.append(Attr(attr).gte(value))
            elif condition == "Contém":
                filter_expressions.append(Attr(attr).contains(value))
            elif condition == "Começa com":
                filter_expressions.append(Attr(attr).begins_with(value))
            elif condition == "Existe":
                filter_expressions.append(Attr(attr).exists())
            elif condition == "Não existe":
                filter_expressions.append(Attr(attr).not_exists())
        
        if not filter_expressions:
            return None
        
        combined_filter = filter_expressions[0]
        for f in filter_expressions[1:]:
            combined_filter = combined_filter & f
        
        return combined_filter
    
    def query_with_filters(self, filters, limit=100, index_name=None, known_attributes=None):
        """Execute query with filters, optionally using an index
        
        Args:
            filters: List of filter dictionaries
            limit: Maximum number of items to return
            index_name: Optional index name to use (GSI or LSI)
            known_attributes: Optional list of attribute names to include in projection
            
        Returns:
            tuple: (items list, scanned_count, elapsed_time_seconds)
        """
        if not self.current_table:
            return [], 0, 0.0
        
        start_time = time.time()
        
        try:
            filter_expr = self.build_filter_expression(filters)
            items = []
            scanned_count = 0
            
            # Verifica se podemos usar atalho por chave primária
            pk_key = None
            sk_key = None
            pk_value = None
            sk_value = None
            pk_type = None
            sk_type = None
            
            # Obter schema da tabela (sem lançar se faltar permissão DescribeTable)
            pk_key, sk_key = self._get_key_schema_safe()
            if pk_key:
                print(f"[DynamoDB] Chave Primária (PK): {pk_key}")
            if sk_key:
                print(f"[DynamoDB] Chave Secundária (SK): {sk_key}")
            
            try:
                # Detecta equality filters on PK/SK com conversão de tipo
                for filter_data in filters:
                    if not filter_data:
                        continue
                    if filter_data.get('condition') == 'Igual a':
                        if pk_key and filter_data.get('attribute') == pk_key:
                            pk_value = self.convert_filter_value(
                                filter_data.get('value'), 
                                filter_data.get('type')
                            )
                            print(f"[DynamoDB] Filtro de PK detectado: {pk_key}={pk_value} (tipo: {type(pk_value).__name__})")
                        if sk_key and filter_data.get('attribute') == sk_key:
                            sk_value = self.convert_filter_value(
                                filter_data.get('value'),
                                filter_data.get('type')
                            )
                            print(f"[DynamoDB] Filtro de SK detectado: {sk_key}={sk_value} (tipo: {type(sk_value).__name__})")
            except Exception as e:
                print(f"[DynamoDB] Erro ao processar filtros: {e}")
            
            # Try primary key shortcut (fastest)
            if pk_key and pk_value is not None:
                print(f"[DynamoDB] ✓ Usando Primary Key shortcut: {pk_key}={pk_value}")
                if sk_key and sk_value is not None:
                    # get_item (instantaneous) - O MAIS RÁPIDO
                    print(f"[DynamoDB] → Usando get_item() com PK+SK (INSTANTÂNEO)")
                    key = {pk_key: pk_value, sk_key: sk_value}
                    try:
                        resp = self.current_table.get_item(Key=key)
                        item = resp.get('Item')
                        if item:
                            items = [item]
                            scanned_count = 1
                            print(f"[DynamoDB] ✓ get_item() retornou 1 item")
                        else:
                            print(f"[DynamoDB] ⚠ get_item() não encontrou item com PK+SK")
                    except Exception as e:
                        print(f"[DynamoDB] ✗ Erro em get_item(): {e}")
                else:
                    # query (very fast) - MUITO RÁPIDO PARA TABELAS COM PK SIMPLES
                    print(f"[DynamoDB] → Usando query() com PK (MUITO RÁPIDO)")
                    try:
                        q_kwargs = {
                            'KeyConditionExpression': Key(pk_key).eq(pk_value),
                            'Limit': limit
                        }
                        resp = self.current_table.query(**q_kwargs)
                        items = resp.get('Items', [])
                        scanned_count = resp.get('ScannedCount', len(items))
                        print(f"[DynamoDB] ✓ query() retornou {len(items)} itens, verificados: {scanned_count}")
                    except Exception as e:
                        print(f"[DynamoDB] ✗ Erro em query(): {e}, caindo para scan...")
                        # Fallback to scan
                        page_size = 500
                        last_evaluated_key = None
                        
                        while len(items) < limit:
                            scan_kwargs = {'Limit': page_size}
                            if filter_expr is not None:
                                scan_kwargs['FilterExpression'] = filter_expr
                            if last_evaluated_key:
                                scan_kwargs['ExclusiveStartKey'] = last_evaluated_key
                            
                            page = self.current_table.scan(**scan_kwargs)
                            page_items = page.get('Items', [])
                            scanned_count += page.get('ScannedCount', 0)
                            
                            items.extend(page_items)
                            
                            if len(items) >= limit:
                                items = items[:limit]
                                break
                            
                            last_evaluated_key = page.get('LastEvaluatedKey')
                            if not last_evaluated_key:
                                break
            elif index_name and index_name != "(Nenhum)":
                # Try using index if specified (fast) - quando não há PK
                print(f"[DynamoDB] Tentando usar índice: {index_name}")
                try:
                    # Determine index key schema so we can build KeyConditionExpression when possible
                    index_key_hash = None
                    index_key_range = None
                    try:
                        idx_defs = (self.current_table.global_secondary_indexes or []) + (self.current_table.local_secondary_indexes or [])
                        for idx in idx_defs:
                            if idx.get('IndexName') == index_name:
                                for k in idx.get('KeySchema', []):
                                    if k.get('KeyType') == 'HASH':
                                        index_key_hash = k.get('AttributeName')
                                    elif k.get('KeyType') == 'RANGE':
                                        index_key_range = k.get('AttributeName')
                                break
                    except Exception:
                        index_key_hash = None
                        index_key_range = None

                    # Build projection attributes: include all known attributes if provided, otherwise include key + filter attributes
                    if known_attributes:
                        # Use all known attributes from the table
                        projection_attrs = set(known_attributes)
                    else:
                        # Fallback: include only PK/SK, index keys and filter attributes
                        projection_attrs = set()
                        if pk_key:
                            projection_attrs.add(pk_key)
                        if sk_key:
                            projection_attrs.add(sk_key)
                        if index_key_hash:
                            projection_attrs.add(index_key_hash)
                        if index_key_range:
                            projection_attrs.add(index_key_range)
                        for f in filters:
                            if f and f.get('attribute'):
                                projection_attrs.add(f.get('attribute'))

                    expression_attribute_names = {}
                    projection_expression = None
                    if projection_attrs:
                        parts = []
                        for i, attr in enumerate(sorted(projection_attrs)):
                            placeholder = f"#p{i}"
                            expression_attribute_names[placeholder] = attr
                            parts.append(placeholder)
                        projection_expression = ', '.join(parts)

                    q_kwargs = {'IndexName': index_name, 'Limit': limit}
                    if projection_expression:
                        q_kwargs['ProjectionExpression'] = projection_expression
                        q_kwargs['ExpressionAttributeNames'] = expression_attribute_names

                    # Separate filters: key-condition filters vs post-filter-only
                    index_hash_value = None
                    index_range_value = None
                    remaining_filters = []
                    
                    for f in filters:
                        if not f:
                            continue
                        if f.get('condition') == 'Igual a':
                            if index_key_hash and f.get('attribute') == index_key_hash:
                                index_hash_value = f.get('value')
                                continue  # Skip this filter, will be in KeyCondition
                            if index_key_range and f.get('attribute') == index_key_range:
                                index_range_value = f.get('value')
                                continue  # Skip this filter, will be in KeyCondition
                        remaining_filters.append(f)  # All other filters are post-filter only

                    # Build filter expression only for non-key attributes
                    remaining_filter_expr = None
                    if remaining_filters:
                        remaining_filter_expr = self.build_filter_expression(remaining_filters)

                    if index_hash_value is not None:
                        # Build key condition expression for index keys
                        if index_range_value is not None:
                            keycond = Key(index_key_hash).eq(index_hash_value) & Key(index_key_range).eq(index_range_value)
                        else:
                            keycond = Key(index_key_hash).eq(index_hash_value)
                        q_kwargs['KeyConditionExpression'] = keycond
                        
                        # Add remaining filter expression (for non-key attributes only)
                        if remaining_filter_expr is not None:
                            q_kwargs['FilterExpression'] = remaining_filter_expr

                        # Execute query using index + key condition (fast)
                        resp = self.current_table.query(**q_kwargs)
                        items = resp.get('Items', [])
                        scanned_count = resp.get('ScannedCount', len(items))
                        print(f"[DynamoDB] Query via índice retornou {len(items)} itens, verificados: {scanned_count}")
                    else:
                        # No equality on index hash key: fall back to scanning the index (still better than full table scan)
                        print(f"[DynamoDB] Nenhuma igualdade encontrada para a chave do índice; fazendo scan no índice {index_name}")
                        page_size = 500
                        last_evaluated_key = None

                        while len(items) < limit:
                            scan_kwargs = {'Limit': page_size, 'IndexName': index_name}
                            if projection_expression:
                                scan_kwargs['ProjectionExpression'] = projection_expression
                                scan_kwargs['ExpressionAttributeNames'] = expression_attribute_names
                            if remaining_filter_expr is not None:
                                scan_kwargs['FilterExpression'] = remaining_filter_expr
                            if last_evaluated_key:
                                scan_kwargs['ExclusiveStartKey'] = last_evaluated_key

                            page = self.current_table.scan(**scan_kwargs)
                            page_items = page.get('Items', [])
                            scanned_count += page.get('ScannedCount', 0)

                            items.extend(page_items)

                            if len(items) >= limit:
                                items = items[:limit]
                                break

                            last_evaluated_key = page.get('LastEvaluatedKey')
                            if not last_evaluated_key:
                                break
                    
                    print(f"[DynamoDB] Índice operado, resultados atuais: {len(items)}, verificados: {scanned_count}")
                except Exception as e:
                    print(f"[DynamoDB] Erro ao usar índice: {e}, usando scan...")
                    # Fallback to scan (full table)
                    page_size = 500
                    last_evaluated_key = None
                    
                    while len(items) < limit:
                        scan_kwargs = {'Limit': page_size}
                        if filter_expr is not None:
                            scan_kwargs['FilterExpression'] = filter_expr
                        if last_evaluated_key:
                            scan_kwargs['ExclusiveStartKey'] = last_evaluated_key
                        
                        page = self.current_table.scan(**scan_kwargs)
                        page_items = page.get('Items', [])
                        scanned_count += page.get('ScannedCount', 0)
                        
                        items.extend(page_items)
                        
                        if len(items) >= limit:
                            items = items[:limit]
                            break
                        
                        last_evaluated_key = page.get('LastEvaluatedKey')
                        if not last_evaluated_key:
                            break
            else:
                # Full table scan with pagination - otimizado (lento)
                print(f"[DynamoDB] Usando scan completo (mais lento)")
                page_size = 500
                last_evaluated_key = None
                
                while len(items) < limit:
                    scan_kwargs = {'Limit': page_size}
                    if filter_expr is not None:
                        scan_kwargs['FilterExpression'] = filter_expr
                    if last_evaluated_key:
                        scan_kwargs['ExclusiveStartKey'] = last_evaluated_key
                    
                    page = self.current_table.scan(**scan_kwargs)
                    page_items = page.get('Items', [])
                    scanned_count += page.get('ScannedCount', 0)
                    
                    items.extend(page_items)
                    
                    if len(items) >= limit:
                        items = items[:limit]
                        break
                    
                    last_evaluated_key = page.get('LastEvaluatedKey')
                    if not last_evaluated_key:
                        break
            
            # Convert Decimals to floats
            items_json = json.loads(json.dumps(items, cls=DecimalEncoder))
            
            elapsed = time.time() - start_time
            print(f"[DynamoDB] Query concluída em {elapsed:.2f}s | Itens: {len(items_json)} | Verificados: {scanned_count}")
            
            return items_json, scanned_count, elapsed
        
        except Exception as e:
            elapsed = time.time() - start_time
            print(f"Erro ao executar query: {e}")
            return [], 0, elapsed
    
    def import_data_from_file(self, file_path, table_name=None, progress_callback=None):
        """Import data from JSON file to DynamoDB table - OTIMIZADO para arquivos grandes
        
        IMPORTANTE: Esta função SÓ funciona em modo LOCAL.
        NUNCA será executada em produção para evitar conexões acidentais.
        
        Otimizações aplicadas:
        - Streaming de arquivo (não carrega tudo na memória)
        - Batch write (25 itens por batch)
        - Retry automático com backoff exponencial
        - Suporte a diferentes estruturas JSON
        
        Args:
            file_path: Path to JSON file containing items
            table_name: Name of the table to import to (if None, uses current_table)
            progress_callback: Optional callback function(imported_count, total_count, error)
            
        Returns:
            tuple: (success: bool, imported_count: int, error_message: str)
        """
        # SEGURANÇA: Verificar se está em modo local
        if not config.DYNAMODB_LOCAL:
            error_msg = "❌ ERRO DE SEGURANÇA: Importação só é permitida em modo LOCAL!"
            print(f"[DynamoDBService.import_data_from_file] {error_msg}")
            if progress_callback:
                progress_callback(0, 0, error_msg)
            return False, 0, error_msg
        
        # SEGURANÇA: Verificar se endpoint é local (não pode ser AWS)
        endpoint_lower = (config.DYNAMODB_ENDPOINT or "").lower()
        
        # Verificar se é endpoint AWS (bloquear)
        if 'amazonaws.com' in endpoint_lower or 'dynamodb' in endpoint_lower and 'aws' in endpoint_lower:
            error_msg = "❌ ERRO DE SEGURANÇA: Endpoint parece ser AWS! Importação bloqueada."
            print(f"[DynamoDBService.import_data_from_file] {error_msg}")
            if progress_callback:
                progress_callback(0, 0, error_msg)
            return False, 0, error_msg
        
        # Verificar se é endpoint local válido
        is_local_endpoint = (
            config.DYNAMODB_ENDPOINT and
            ('localhost' in endpoint_lower or '127.0.0.1' in endpoint_lower)
        )
        
        if not is_local_endpoint:
            error_msg = "❌ ERRO DE SEGURANÇA: Endpoint não é local (localhost ou 127.0.0.1)!"
            print(f"[DynamoDBService.import_data_from_file] {error_msg}")
            if progress_callback:
                progress_callback(0, 0, error_msg)
            return False, 0, error_msg
        
        try:
            # Determinar nome da tabela
            if not table_name:
                if self.current_table:
                    table_name = self.current_table.name
                else:
                    error_msg = "Nenhuma tabela selecionada ou especificada"
                    if progress_callback:
                        progress_callback(0, 0, error_msg)
                    return False, 0, error_msg
            
            # Criar importador otimizado
            importer = DynamoDBBatchImporter(
                endpoint_url=config.DYNAMODB_ENDPOINT,
                region_name=config.DYNAMODB_REGION,
                access_key_id=config.DYNAMODB_ACCESS_KEY,
                secret_access_key=config.DYNAMODB_SECRET_KEY
            )
            
            # Importar com callback de progresso
            def progress_wrapper(imported_count, total_count, error):
                if progress_callback:
                    progress_callback(imported_count, total_count, error)
            
            stats = importer.import_file(file_path, table_name, progress_wrapper)
            
            # Retornar resultado no formato antigo para compatibilidade
            success = stats['successful'] > 0
            imported_count = stats['successful']
            error_msg = None
            
            if stats['failed'] > 0:
                error_msg = f"Importados {imported_count} itens com {stats['failed']} falhas em {stats['elapsed_seconds']:.1f}s"
            elif success:
                error_msg = f"✅ Importados {imported_count} itens em {stats['elapsed_seconds']:.1f}s ({stats['items_per_second']:.1f} itens/s)"
            else:
                error_msg = "Nenhum item foi importado"
            
            print(f"[DynamoDBService.import_data_from_file] {error_msg}")
            
            return success, imported_count, error_msg
        
        except Exception as e:
            error_msg = f"Erro inesperado: {str(e)}"
            print(f"[DynamoDBService.import_data_from_file] ❌ {error_msg}")
            if progress_callback:
                progress_callback(0, 0, error_msg)
            return False, 0, error_msg
    
    def delete_item(self, key):
        """Delete an item from the current table
        
        Args:
            key: Dictionary containing the primary key of the item to delete
                Example: {'id': '123'} or {'pk': '123', 'sk': '456'}
        
        Returns:
            tuple: (success: bool, message: str)
        """
        if not self.current_table:
            return False, "Nenhuma tabela selecionada"
        
        try:
            self.current_table.delete_item(Key=key)
            return True, "Item deletado com sucesso"
        except Exception as e:
            error_msg = f"Erro ao deletar item: {str(e)}"
            print(f"[DynamoDBService.delete_item] {error_msg}")
            return False, error_msg