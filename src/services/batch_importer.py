"""
Módulo otimizado para importar dados JSON grandes para DynamoDB em lote.
Ideal para arquivos maiores que 2.5GB com processamento eficiente e batch writes.
"""

import json
import boto3
import time
import os
from pathlib import Path
from typing import Iterator, List, Dict, Any, Callable, Optional, Tuple
from datetime import datetime
import logging
from decimal import Decimal
from boto3.dynamodb.types import TypeSerializer
import math

try:
    from tqdm import tqdm
    HAS_TQDM = True
except ImportError:
    HAS_TQDM = False

try:
    import ijson
    HAS_IJSON = True
except ImportError:
    HAS_IJSON = False


# Configuração de logging
logger = logging.getLogger('DynamoDBBatchImporter')


class DynamoDBBatchImporter:
    """Importador otimizado de dados para DynamoDB com suporte a arquivos grandes."""
    
    BATCH_SIZE = 25  # Limite do DynamoDB
    MAX_RETRIES = 3
    INITIAL_BACKOFF = 0.5  # segundos
    
    def __init__(self, endpoint_url: str, region_name: str = 'us-east-1',
                 access_key_id: str = None, secret_access_key: str = None,
                 num_workers: int = 1):
        """
        Inicializa o importador.
        
        Args:
            endpoint_url: URL do DynamoDB (ex: http://localhost:8000)
            region_name: Região AWS
            access_key_id: AWS Access Key ID (opcional para local)
            secret_access_key: AWS Secret Access Key (opcional para local)
            num_workers: Número de workers (não implementado ainda)
        """
        dynamodb_kwargs = {
            'endpoint_url': endpoint_url,
            'region_name': region_name,
        }
        
        if access_key_id and secret_access_key:
            dynamodb_kwargs['aws_access_key_id'] = access_key_id
            dynamodb_kwargs['aws_secret_access_key'] = secret_access_key
        
        self.dynamodb = boto3.client('dynamodb', **dynamodb_kwargs)
        self.resource = boto3.resource('dynamodb', **dynamodb_kwargs)
        self.num_workers = num_workers
        
        self.stats = {
            'total_items': 0,
            'successful_items': 0,
            'failed_items': 0,
            'start_time': None,
            'end_time': None
        }
    
    def stream_json_items(self, file_path: str) -> Iterator[Dict[str, Any]]:
        """
        Lê arquivo JSON de forma eficiente usando streaming.
        Suporta diferentes estruturas: {Items: []}, {items: []}, {Records: []}, etc.
        
        Args:
            file_path: Caminho do arquivo JSON
            
        Yields:
            Itens do JSON um por um
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                # Detectar estrutura lendo o primeiro caractere
                content = f.read(10000)
                f.seek(0)
                
                if content.strip().startswith('['):
                    # É um array direto
                    yield from self._stream_json_array(f)
                else:
                    # É um objeto - extrair lista de itens
                    f.seek(0)
                    try:
                        full_data = json.load(f)
                        yield from self._extract_items(full_data)
                    except json.JSONDecodeError as e:
                        logger.error(f"❌ Erro ao decodificar JSON em {file_path}: {e}")
                        return
                    
        except FileNotFoundError:
            logger.error(f"❌ Arquivo não encontrado: {file_path}")
            return
        except Exception as e:
            logger.error(f"❌ Erro ao ler arquivo {file_path}: {e}")
            return
    
    def _stream_json_array(self, f) -> Iterator[Dict[str, Any]]:
        """Faz streaming de um array JSON sem carregar tudo na memória."""
        if HAS_IJSON:
            try:
                for item in ijson.items(f, 'item'):
                    yield item
                return
            except Exception:
                pass
        
        # Fallback: carregar array inteiro (menos ideal mas funciona)
        logger.warning("⚠️  Usando fallback para streaming de array (mais lento com arquivos grandes)...")
        f.seek(0)
        try:
            data = json.load(f)
            if isinstance(data, list):
                for item in data:
                    yield item
        except json.JSONDecodeError as e:
            logger.error(f"❌ Erro ao decodificar array JSON: {e}")
    
    def _extract_items(self, data: Any) -> Iterator[Dict[str, Any]]:
        """Extrai itens de uma estrutura JSON."""
        items = []
        
        if isinstance(data, dict):
            # Tenta chaves comuns
            for key in ['Items', 'items', 'Records', 'records', 'data', 'Data', 
                       'MessageGroup', 'messages', 'Messages', 'Rows', 'rows']:
                if key in data and isinstance(data[key], list):
                    items = data[key]
                    break
            
            # Se não encontrou lista, trata como item único
            if not items:
                items = [data]
        elif isinstance(data, list):
            items = data
        else:
            items = [data]
        
        # Yield itens
        for item in items:
            yield item
    
    def batch_write_items(self, table_name: str, items: List[Dict[str, Any]], 
                         key_schema: Optional[Dict[str, str]] = None) -> Tuple[int, int]:
        """
        Escreve itens em lote com retry automático.
        
        Args:
            table_name: Nome da tabela DynamoDB
            items: Lista de itens para inserir
            key_schema: Dicionário com schema de chaves da tabela {attr_name: 'HASH'|'RANGE'}
            
        Returns:
            (quantidade de itens inseridos, quantidade de falhas)
        """
        if not items:
            return 0, 0
        
        total_items = len(items)
        request_items = {
            table_name: []
        }
        
        # Converter todos os itens e construir requisição
        for idx, item in enumerate(items):
            try:
                converted = self._convert_to_dynamodb_format(item)
                if converted:  # Só adicionar se não estiver vazio
                    # Limpar atributos inválidos (strings vazias, NULL, etc) em vez de rejeitar
                    cleaned = self._clean_dynamodb_item(converted, idx)
                    if not cleaned:
                        logger.warning(f"⚠️  Item {idx} ficou vazio após limpeza, pulando")
                        continue
                    
                    # Validar que item tem as chaves obrigatórias
                    if key_schema:
                        missing_keys = []
                        for key_attr, key_type in key_schema.items():
                            if key_attr not in cleaned:
                                missing_keys.append(f"'{key_attr}' ({key_type})")
                        if missing_keys:
                            logger.error(f"❌ Item {idx}: falta chave(s) obrigatória(s): {', '.join(missing_keys)}")
                            continue
                    
                    request_items[table_name].append({
                        'PutRequest': {'Item': cleaned}
                    })
            except Exception as e:
                logger.error(f"❌ Erro ao converter item {idx}: {e}")
                if logger.isEnabledFor(logging.DEBUG):
                    logger.debug(f"   Item problemático: {json.dumps(item, default=str)[:500]}")
                continue
        
        if not request_items[table_name]:
            logger.warning(f"⚠️  Nenhum item válido para inserir em {table_name}")
            return 0, len(items)
        
        successful = 0
        failed = 0
        retries = 0
        
        while request_items.get(table_name) and retries < self.MAX_RETRIES:
            try:
                response = self.dynamodb.batch_write_item(RequestItems=request_items)
                
                # Itens que falharam (não processados)
                unprocessed = response.get('UnprocessedItems', {}).get(table_name, [])
                
                # Itens que foram processados com sucesso nesta rodada
                current_batch_size = len(request_items[table_name])
                processed_this_round = current_batch_size - len(unprocessed)
                successful += processed_this_round
                
                # Se houver itens não processados, tentar novamente
                if unprocessed:
                    request_items[table_name] = unprocessed
                    retries += 1
                    backoff = self.INITIAL_BACKOFF * (2 ** retries)
                    logger.debug(
                        f"⚠️  {len(unprocessed)} itens não processados. "
                        f"Tentando novamente em {backoff}s..."
                    )
                    time.sleep(backoff)
                else:
                    # Todos foram processados com sucesso
                    break
            
            except Exception as e:
                # Verificar se é throttling
                if 'ProvisionedThroughputExceededException' in str(type(e)):
                    backoff = self.INITIAL_BACKOFF * (2 ** retries)
                    logger.warning(f"⚠️  Limite de throughput atingido. Aguardando {backoff}s...")
                    time.sleep(backoff)
                    retries += 1
                else:
                    error_str = str(e)
                    logger.error(f"❌ Erro ao fazer batch write: {e}")
                    
                    # Log detailed information about the request that failed
                    if request_items.get(table_name):
                        batch = request_items[table_name]
                        logger.error(f"   Batch size: {len(batch)} items")
                        
                        # Tentar identificar qual item/atributo está causando problema
                        # Se o erro menciona um atributo específico, tentar encontrá-lo
                        if 'Invalid attribute value type' in error_str:
                            logger.error("   ⚠️  Erro de tipo de atributo inválido detectado")
                            logger.error("   Validando cada item do batch individualmente...")
                            
                            # Validar cada item individualmente para encontrar o problemático
                            for batch_idx, batch_item in enumerate(batch[:5]):  # Verificar apenas os 5 primeiros
                                item = batch_item.get('PutRequest', {}).get('Item', {})
                                if not self._validate_dynamodb_item(item, batch_idx):
                                    logger.error(f"   ❌ Item {batch_idx} no batch falhou na validação!")
                                
                                # Tentar escrever item individualmente para ver qual falha
                                try:
                                    self.dynamodb.put_item(
                                        TableName=table_name,
                                        Item=item
                                    )
                                    logger.debug(f"   ✓ Item {batch_idx} válido individualmente")
                                except Exception as individual_error:
                                    logger.error(f"   ❌ Item {batch_idx} falhou individualmente: {individual_error}")
                                    logger.error(f"   Atributos do item {batch_idx}:")
                                    for key, value in item.items():
                                        try:
                                            value_str = json.dumps(value, default=str)
                                            if len(value_str) > 150:
                                                value_str = value_str[:150] + "..."
                                            logger.error(f"     - {key}: {value_str}")
                                        except:
                                            logger.error(f"     - {key}: {str(value)[:150]}")
                        
                        # Show ALL attributes of the first item for debugging
                        if batch:
                            first_item = batch[0].get('PutRequest', {}).get('Item', {})
                            logger.error(f"   First item has {len(first_item)} attributes:")
                            for key, value in first_item.items():
                                try:
                                    value_str = json.dumps(value, default=str)
                                    if len(value_str) > 100:
                                        value_str = value_str[:100] + "..."
                                    logger.error(f"     - {key}: {value_str}")
                                except:
                                    logger.error(f"     - {key}: {str(value)[:100]}")
                    
                    failed += len(request_items.get(table_name, []))
                    break
        
        # Itens que ainda não foram processados após retries
        remaining = len(request_items.get(table_name, []))
        if remaining > 0:
            failed += remaining
        
        return successful, failed
    
    def _convert_to_dynamodb_format(self, item: Dict[str, Any]) -> Dict[str, Any]:
        """
        Converte item do formato Python para formato DynamoDB nativo.
        
        Args:
            item: Item em formato Python
            
        Returns:
            Item em formato DynamoDB
        """
        if not isinstance(item, dict):
            logger.warning(f"⚠️  Item não é dict: {type(item).__name__}")
            return {}
        
        if not item:  # Item vazio
            return item
        
        # Verificar se já está no formato DynamoDB (tem tipos como 'S', 'N', etc)
        # Formato DynamoDB tem estrutura: {'field1': {'S': 'value'}, 'field2': {'N': '123'}}
        if self._is_dynamodb_format(item):
            logger.debug("ℹ️  Item já está em formato DynamoDB, validando e limpando...")
            # Validar e limpar atributos problemáticos
            cleaned = {}
            for key, value in item.items():
                if not isinstance(value, dict):
                    continue  # Pular valores inválidos
                
                # Remover atributos NULL (DynamoDB pode rejeitar em alguns contextos)
                if 'NULL' in value:
                    logger.debug(f"   Removendo atributo NULL: {key}")
                    continue
                
                # Remover strings vazias (DynamoDB não aceita)
                if 'S' in value and value['S'] == '':
                    logger.debug(f"   Removendo string vazia: {key}")
                    continue
                
                # Remover sets vazios
                if any(t in value for t in ['SS', 'NS', 'BS']) and len(value.get(list(value.keys())[0], [])) == 0:
                    logger.debug(f"   Removendo set vazio: {key}")
                    continue
                
                cleaned[key] = value
            return cleaned if cleaned else {}
        
        # Limpar e validar item antes de serializar
        cleaned_item = self._clean_item(item)
        
        if not cleaned_item:
            logger.warning(f"⚠️  Item ficou vazio após limpeza")
            return {}
        
        # Usar TypeSerializer do boto3 para conversão correta
        serializer = TypeSerializer()
        converted_item = {}
        
        for key, value in cleaned_item.items():
            try:
                # TypeSerializer converte tipos Python para DynamoDB
                converted_item[key] = serializer.serialize(value)
            except Exception as e:
                logger.warning(f"⚠️  Erro ao converter atributo '{key}' (tipo {type(value).__name__}): {e}")
                continue  # Pular atributos que não podem ser serializados
        
        if not converted_item:
            logger.warning(f"⚠️  Item sem atributos válidos após conversão")
            return {}
        
        return converted_item
    
    def _clean_dynamodb_item(self, item: Dict[str, Any], item_index: int = 0) -> Dict[str, Any]:
        """
        Remove atributos inválidos de um item em formato DynamoDB.
        Remove strings vazias, NULL, sets vazios, etc.
        
        Args:
            item: Item em formato DynamoDB
            item_index: Índice do item para logs
            
        Returns:
            Item limpo ou {} se ficou vazio
        """
        if not isinstance(item, dict):
            return {}
        
        cleaned = {}
        removed_count = 0
        
        def _clean_av(av: Dict[str, Any], path: str) -> Optional[Dict[str, Any]]:
            """Limpa recursivamente um AttributeValue, retornando None se inválido."""
            if not isinstance(av, dict) or len(av) != 1:
                return None
            
            type_key = next(iter(av.keys()))
            type_value = av[type_key]
            
            # Remover NULL
            if type_key == 'NULL':
                return None
            
            # Remover strings vazias
            if type_key == 'S' and (not isinstance(type_value, str) or type_value == ''):
                return None
            
            # Remover sets vazios
            if type_key in ('SS', 'NS', 'BS'):
                if not isinstance(type_value, list) or len(type_value) == 0:
                    return None
                # Limpar elementos vazios do set
                cleaned_set = []
                for v in type_value:
                    if type_key == 'SS' and isinstance(v, str) and v != '':
                        cleaned_set.append(v)
                    elif type_key == 'NS' and isinstance(v, str):
                        try:
                            float(v)
                            cleaned_set.append(v)
                        except (TypeError, ValueError):
                            pass
                    elif type_key == 'BS' and isinstance(v, (str, bytes, bytearray)):
                        cleaned_set.append(v)
                if not cleaned_set:
                    return None
                return {type_key: cleaned_set}
            
            # Limpar listas recursivamente
            if type_key == 'L':
                if not isinstance(type_value, list):
                    return None
                cleaned_list = []
                for inner_av in type_value:
                    cleaned_inner = _clean_av(inner_av, f"{path}[]")
                    if cleaned_inner is not None:
                        cleaned_list.append(cleaned_inner)
                if not cleaned_list:
                    return None
                return {type_key: cleaned_list}
            
            # Limpar mapas recursivamente
            if type_key == 'M':
                if not isinstance(type_value, dict):
                    return None
                cleaned_map = {}
                for nested_key, nested_av in type_value.items():
                    if not isinstance(nested_key, str) or not nested_key:
                        continue
                    cleaned_nested = _clean_av(nested_av, f"{path}.{nested_key}")
                    if cleaned_nested is not None:
                        cleaned_map[nested_key] = cleaned_nested
                if not cleaned_map:
                    return None
                return {type_key: cleaned_map}
            
            # Outros tipos válidos (N, B, BOOL)
            return av
        
        for key, value in item.items():
            if not isinstance(key, str) or not key:
                continue
            
            cleaned_value = _clean_av(value, key)
            if cleaned_value is not None:
                cleaned[key] = cleaned_value
            else:
                removed_count += 1
        
        if removed_count > 0:
            logger.debug(f"   Item {item_index}: removidos {removed_count} atributo(s) inválido(s)")
        
        return cleaned
    
    def _validate_dynamodb_item(self, item: Dict[str, Any], item_index: int = 0) -> bool:
        """
        Valida se um item convertido está em formato válido para DynamoDB.
        
        Args:
            item: Item em formato DynamoDB (AttributeValue)
            item_index: Índice do item para logs
            
        Returns:
            True se válido, False caso contrário
        """
        if not isinstance(item, dict):
            logger.warning(f"⚠️  Item {item_index} não é dict: {type(item).__name__}")
            return False
        
        def _validate_av(attr_key: str, av: Dict[str, Any], path: str) -> bool:
            """Valida recursivamente um AttributeValue."""
            # Valor deve ser um dict com exatamente 1 chave
            if not isinstance(av, dict):
                logger.error(f"❌ {path}: valor não é dict - {type(av).__name__}")
                return False
            if len(av) != 1:
                logger.error(f"❌ {path}: dict com múltiplas chaves - {list(av.keys())}")
                return False
            
            type_key = next(iter(av.keys()))
            type_value = av[type_key]
            
            valid_types = ['S', 'N', 'B', 'SS', 'NS', 'BS', 'M', 'L', 'BOOL', 'NULL']
            if type_key not in valid_types:
                logger.error(f"❌ {path}: tipo inválido - {type_key}")
                return False
            
            # Tipos escalares simples
            if type_key == 'S':
                if not isinstance(type_value, str):
                    logger.error(f"❌ {path}: S deve ser string, got {type(type_value).__name__}")
                    return False
                if type_value == '':
                    logger.error(f"❌ {path}: string vazia não permitida")
                    return False
            
            elif type_key == 'N':
                if not isinstance(type_value, str):
                    logger.error(f"❌ {path}: N deve ser string, got {type(type_value).__name__}")
                    return False
                try:
                    float(type_value)
                except (TypeError, ValueError):
                    logger.error(f"❌ {path}: N valor inválido - {type_value}")
                    return False
            
            elif type_key == 'BOOL':
                if not isinstance(type_value, bool):
                    logger.error(f"❌ {path}: BOOL deve ser bool, got {type(type_value).__name__}")
                    return False
            
            elif type_key == 'NULL':
                # DynamoDB espera literalmente true
                if type_value is not True:
                    logger.error(f"❌ {path}: NULL deve ser true, got {type_value}")
                    return False
            
            # Sets (SS/NS/BS)
            elif type_key in ('SS', 'NS', 'BS'):
                if not isinstance(type_value, list):
                    logger.error(f"❌ {path}: {type_key} deve ser list, got {type(type_value).__name__}")
                    return False
                if len(type_value) == 0:
                    logger.error(f"❌ {path}: {type_key} não pode ser lista vazia")
                    return False
                
                for i, v in enumerate(type_value):
                    elem_path = f"{path}[{i}]"
                    if type_key == 'SS':
                        if not isinstance(v, str) or v == '':
                            logger.error(f"❌ {elem_path}: SS deve conter strings não vazias, got {repr(v)}")
                            return False
                    elif type_key == 'NS':
                        if not isinstance(v, str):
                            logger.error(f"❌ {elem_path}: NS deve conter strings numéricas, got {type(v).__name__}")
                            return False
                        try:
                            float(v)
                        except (TypeError, ValueError):
                            logger.error(f"❌ {elem_path}: NS valor inválido - {v}")
                            return False
                    elif type_key == 'BS':
                        # Em JSON normalmente vem como base64 string
                        if not isinstance(v, (str, bytes, bytearray)):
                            logger.error(f"❌ {elem_path}: BS deve conter strings/bytes, got {type(v).__name__}")
                            return False
            
            # Lista
            elif type_key == 'L':
                if not isinstance(type_value, list):
                    logger.error(f"❌ {path}: L deve ser list, got {type(type_value).__name__}")
                    return False
                for i, inner_av in enumerate(type_value):
                    if not _validate_av(attr_key, inner_av, f"{path}[{i}]"):
                        return False
            
            # Mapa
            elif type_key == 'M':
                if not isinstance(type_value, dict):
                    logger.error(f"❌ {path}: M deve ser dict, got {type(type_value).__name__}")
                    return False
                for nested_key, nested_av in type_value.items():
                    if not isinstance(nested_key, str) or not nested_key:
                        logger.error(f"❌ {path}: chave de M inválida - {repr(nested_key)}")
                        return False
                    if not _validate_av(nested_key, nested_av, f"{path}.{nested_key}"):
                        return False
            
            return True
        
        # Validação de cada atributo na raiz
        for key, value in item.items():
            # Validar chave
            if not isinstance(key, str) or not key:
                logger.error(f"❌ Item {item_index}: chave inválida - {repr(key)}")
                return False
            
            if not _validate_av(key, value, f"Item {item_index}.{key}"):
                return False
        
        return True
    
    def _is_dynamodb_format(self, item: Dict[str, Any]) -> bool:
        """
        Verifica se um item já está em formato DynamoDB.
        
        Formato DynamoDB: cada valor é um dict com EXATAMENTE uma chave de tipo
        Ex: {'field': {'S': 'string'}} ou {'count': {'N': '42'}}
        
        Vs Python dict: {'nested': {'field1': 'value', 'field2': 123}}
        """
        if not item:
            return False
        
        # Verificar os primeiros valores para determinar o formato
        checked = 0
        for value in item.values():
            if not isinstance(value, dict):
                # Se qualquer valor não é dict, não é DynamoDB format
                return False
            
            # DynamoDB format tem exatamente 1 chave de tipo
            if len(value) != 1:
                return False
            
            # Verificar se tem uma chave de tipo DynamoDB (S, N, B, SS, NS, BS, M, L, BOOL, NULL)
            has_type_key = any(k in value for k in ['S', 'N', 'B', 'SS', 'NS', 'BS', 'M', 'L', 'BOOL', 'NULL'])
            
            if not has_type_key:
                return False
            
            checked += 1
            if checked >= 3:  # Verificar apenas os 3 primeiros
                break
        
        return checked > 0
    
    def _clean_item(self, item: Dict[str, Any]) -> Dict[str, Any]:
        """
        Limpa e valida um item para garantir compatibilidade com DynamoDB.
        Remove valores inválidos (strings vazias, NaN, Infinity, None, datetime, floats).
        
        Args:
            item: Item a limpar
            
        Returns:
            Item limpo e validado
        """
        cleaned = {}
        
        for key, value in item.items():
            if value is None:
                # DynamoDB exige NULL explícito, mas vamos pular None por segurança
                continue
            
            # Validar key (não pode ser vazio)
            if not key or not isinstance(key, str):
                logger.warning(f"⚠️  Chave inválida: {key}, pulando")
                continue
            
            # Processar strings
            if isinstance(value, str):
                if value == '':
                    continue  # Skip empty strings
                cleaned[key] = value
            
            # Processar números
            elif isinstance(value, bool):
                # bool deve vir ANTES de int/float check, pois bool é subclass de int
                cleaned[key] = value
            
            elif isinstance(value, int):
                cleaned[key] = value
            
            elif isinstance(value, float):
                # Float não é suportado - converter para Decimal ou remover
                if math.isnan(value) or math.isinf(value):
                    # Valores inválidos - pular
                    logger.warning(f"⚠️  Valor inválido em '{key}': {value}, pulando")
                    continue
                else:
                    # Converter float para Decimal para DynamoDB
                    cleaned[key] = Decimal(str(value))
            
            elif isinstance(value, Decimal):
                cleaned[key] = value
            
            elif isinstance(value, datetime):
                # datetime -> ISO 8601 string
                cleaned[key] = value.isoformat()
            
            elif isinstance(value, (bytes, bytearray)):
                # Bytes ficam como base64 automaticamente pelo TypeSerializer
                if len(value) > 0:  # Não permitir bytes vazios
                    cleaned[key] = value
            
            # Processar listas recursivamente
            elif isinstance(value, list):
                cleaned_list = []
                for item_in_list in value:
                    cleaned_item_value = self._clean_value(item_in_list)
                    if cleaned_item_value is not None:
                        cleaned_list.append(cleaned_item_value)
                
                if cleaned_list:  # Só adicionar se não vazio
                    cleaned[key] = cleaned_list
            
            # Processar dicts recursivamente
            elif isinstance(value, dict):
                cleaned_dict = self._clean_item(value)
                if cleaned_dict:  # Só adicionar se não vazio
                    cleaned[key] = cleaned_dict
            
            else:
                # Tipo desconhecido - converter para string
                str_value = str(value).strip()
                if str_value:
                    logger.warning(f"⚠️  Tipo desconhecido em '{key}': {type(value).__name__}, convertendo para string")
                    cleaned[key] = str_value
        
        return cleaned
    
    def _clean_value(self, value: Any) -> Any:
        """
        Limpa um valor individual (usado em listas).
        
        Args:
            value: Valor a limpar
            
        Returns:
            Valor limpo ou None se deve ser descartado
        """
        if value is None:
            return None
        
        if isinstance(value, str):
            return value if value != '' else None
        
        if isinstance(value, bool):
            return value
        
        if isinstance(value, int):
            return value
        
        if isinstance(value, float):
            if math.isnan(value) or math.isinf(value):
                return None
            return Decimal(str(value))
        
        if isinstance(value, Decimal):
            return value
        
        if isinstance(value, datetime):
            return value.isoformat()
        
        if isinstance(value, (bytes, bytearray)):
            return value
        
        if isinstance(value, list):
            cleaned_list = []
            for item in value:
                cleaned_item = self._clean_value(item)
                if cleaned_item is not None:
                    cleaned_list.append(cleaned_item)
            return cleaned_list if cleaned_list else None
        
        if isinstance(value, dict):
            cleaned_dict = self._clean_item(value)
            return cleaned_dict if cleaned_dict else None
        
        # Tipo desconhecido - converter para string
        return str(value)
    
    def import_file(self, file_path: str, table_name: str = None,
                   progress_callback: Optional[Callable[[int, int, Optional[str]], None]] = None) -> Dict[str, Any]:
        """
        Importa um arquivo JSON para uma tabela DynamoDB.
        
        Args:
            file_path: Caminho do arquivo
            table_name: Nome da tabela (se None, extrai do nome do arquivo)
            progress_callback: Função para reportar progresso: callback(imported, total, error)
            
        Returns:
            Dicionário com estatísticas
        """
        # Determinar nome da tabela
        if not table_name:
            filename = Path(file_path).name
            table_name = filename.replace('-dump.json', '').replace('.json', '')
        
        logger.info(f"📥 Iniciando importação de {file_path} para tabela '{table_name}'")
        
        # Validar informações da tabela
        logger.info(f"   Validando tabela '{table_name}'...")
        try:
            table = self.resource.Table(table_name)
            table.reload()
            
            # Obter schema da tabela
            key_schema = table.key_schema
            key_attrs = {key['AttributeName']: key['KeyType'] for key in key_schema}
            logger.info(f"   Chaves da tabela: {key_attrs}")
        except Exception as e:
            logger.warning(f"   ⚠️  Não foi possível validar tabela: {e}")
            key_attrs = None
        
        try:
            file_size_mb = os.path.getsize(file_path) / (1024 * 1024)
            logger.info(f"   Tamanho do arquivo: {file_size_mb:.2f} MB")
        except:
            file_size_mb = 0
        
        stats = {
            'file': file_path,
            'table': table_name,
            'successful': 0,
            'failed': 0,
            'total_items': 0,
            'start_time': datetime.now(),
            'end_time': None,
            'elapsed_seconds': 0,
            'items_per_second': 0,
            'key_schema': key_attrs
        }
        
        try:
            # Processar em lotes SEM contar antecipadamente (evita travamento)
            batch = []
            processed_count = 0
            
            # Setup progress bar
            if HAS_TQDM:
                pbar = tqdm(desc=f"Importando {table_name}", unit="items", ncols=100, disable=False)
            else:
                pbar = None
            
            for item in self.stream_json_items(file_path):
                batch.append(item)
                processed_count += 1
                
                if len(batch) >= self.BATCH_SIZE:
                    success, failed = self.batch_write_items(table_name, batch, key_attrs)
                    stats['successful'] += success
                    stats['failed'] += failed
                    
                    if pbar:
                        pbar.update(len(batch))
                    
                    if progress_callback:
                        progress_callback(stats['successful'], None, None)
                    
                    batch = []
            
            # Processar lote final
            if batch:
                success, failed = self.batch_write_items(table_name, batch, key_attrs)
                stats['successful'] += success
                stats['failed'] += failed
                
                if pbar:
                    pbar.update(len(batch))
                
                if progress_callback:
                    progress_callback(stats['successful'], None, None)
            
            if pbar:
                pbar.close()
            
            stats['total_items'] = processed_count
            
            if processed_count == 0:
                logger.warning(f"⚠️  Nenhum item encontrado em {file_path}")
                if progress_callback:
                    progress_callback(0, 0, "Nenhum item encontrado")
                return stats
            
            stats['end_time'] = datetime.now()
            stats['elapsed_seconds'] = (stats['end_time'] - stats['start_time']).total_seconds()
            stats['items_per_second'] = stats['successful'] / stats['elapsed_seconds'] if stats['elapsed_seconds'] > 0 else 0
            
            logger.info(f"✅ Importação concluída para '{table_name}'")
            logger.info(f"   Itens: {stats['successful']} sucesso, {stats['failed']} falhas")
            logger.info(f"   Tempo: {stats['elapsed_seconds']:.2f}s ({stats['items_per_second']:.1f} itens/s)")
            
            return stats
        
        except Exception as e:
            logger.error(f"❌ Erro crítico ao importar {file_path}: {e}")
            stats['end_time'] = datetime.now()
            if progress_callback:
                progress_callback(stats['successful'], None, str(e))
            return stats
