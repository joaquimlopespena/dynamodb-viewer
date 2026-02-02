"""JSON Encoders for DynamoDB types"""

import json
from decimal import Decimal


class DecimalEncoder(json.JSONEncoder):
    """Encoder para lidar com Decimal do DynamoDB"""
    
    def default(self, obj):
        """Handle Decimal serialization"""
        if isinstance(obj, Decimal):
            return float(obj)
        return super(DecimalEncoder, self).default(obj)
