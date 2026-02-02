"""Configuration module for DynamoDB Viewer"""

import os
from typing import Optional


class Config:
    """Application configuration"""
    
    # DynamoDB Connection Settings (padrão: local)
    DYNAMODB_LOCAL = os.getenv("DYNAMODB_LOCAL", "true").lower() == "true"
    DYNAMODB_ENDPOINT = os.getenv("DYNAMODB_ENDPOINT", "http://localhost:9000")
    DYNAMODB_REGION = os.getenv("DYNAMODB_REGION", "us-east-1")
    DYNAMODB_ACCESS_KEY = os.getenv("DYNAMODB_ACCESS_KEY", "local")
    DYNAMODB_SECRET_KEY = os.getenv("DYNAMODB_SECRET_KEY", "local")
    
    # UI Settings
    WINDOW_WIDTH = 1400
    WINDOW_HEIGHT = 800
    DEFAULT_LIMIT = 100
    DEFAULT_SCAN_LIMIT = 1000
    
    # Application Settings
    APP_TITLE = "DynamoDB Viewer - Local"
    APP_VERSION = "2.0.0"
    
    @classmethod
    def set_local(cls, endpoint: str = "http://localhost:9000"):
        """Configure to use DynamoDB Local
        
        Args:
            endpoint: Endpoint URL (default: http://localhost:9000)
        """
        cls.DYNAMODB_LOCAL = True
        cls.DYNAMODB_ENDPOINT = endpoint
        cls.DYNAMODB_REGION = "us-east-1"
        cls.DYNAMODB_ACCESS_KEY = "local"
        cls.DYNAMODB_SECRET_KEY = "local"
        cls.APP_TITLE = "DynamoDB Viewer - Local"
    
    @classmethod
    def set_production(cls, region: str = "us-east-1"):
        """Configure to use AWS Production
        
        Args:
            region: AWS region (default: us-east-1)
        """
        cls.DYNAMODB_LOCAL = False
        cls.DYNAMODB_ENDPOINT = None
        cls.DYNAMODB_REGION = region
        cls.DYNAMODB_ACCESS_KEY = None
        cls.DYNAMODB_SECRET_KEY = None
        cls.APP_TITLE = f"DynamoDB Viewer - AWS ({region})"
    
    @classmethod
    def get_dynamodb_config(cls) -> dict:
        """Get DynamoDB configuration dictionary
        
        Returns:
            dict: Configuration for boto3.resource('dynamodb')
        """
        config = {
            'region_name': cls.DYNAMODB_REGION,
        }
        
        if cls.DYNAMODB_LOCAL:
            config['endpoint_url'] = cls.DYNAMODB_ENDPOINT
            config['aws_access_key_id'] = cls.DYNAMODB_ACCESS_KEY
            config['aws_secret_access_key'] = cls.DYNAMODB_SECRET_KEY
        
        return config
    
    @classmethod
    def print_config(cls):
        """Print current configuration"""
        print("\n" + "="*60)
        print("DynamoDB Viewer - Configuração Atual")
        print("="*60)
        print(f"Modo: {'📱 LOCAL' if cls.DYNAMODB_LOCAL else '☁️ AWS PRODUCTION'}")
        if cls.DYNAMODB_LOCAL:
            print(f"Endpoint: {cls.DYNAMODB_ENDPOINT}")
        print(f"Região: {cls.DYNAMODB_REGION}")
        print(f"Janela: {cls.WINDOW_WIDTH}x{cls.WINDOW_HEIGHT}")
        print("="*60 + "\n")


# Create default config instance
config = Config()
