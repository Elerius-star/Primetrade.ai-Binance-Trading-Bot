import requests
import hashlib
import hmac
import time
import logging
from urllib.parse import urlencode
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

class DirectAPIClient:
    """Direct REST API client for Binance Futures"""
    
    def __init__(self, api_key: str, api_secret: str):
        self.api_key = api_key
        self.api_secret = api_secret
        self.base_url = "https://testnet.binancefuture.com"
        self.session = requests.Session()
        
    def _generate_signature(self, params: Dict) -> str:
        """Generate HMAC SHA256 signature"""
        query_string = urlencode(params)
        signature = hmac.new(
            self.api_secret.encode('utf-8'),
            query_string.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        return signature
    
    def _request(self, method: str, endpoint: str, params: Optional[Dict] = None) -> Dict:
        """Make authenticated request to Binance API"""
        timestamp = int(time.time() * 1000)
        
        if params is None:
            params = {}
        
        params['timestamp'] = timestamp
        params['recvWindow'] = 5000
        
        # Generate signature
        params['signature'] = self._generate_signature(params)
        
        headers = {
            'X-MBX-APIKEY': self.api_key,
            'Content-Type': 'application/json'
        }
        
        url = f"{self.base_url}{endpoint}"
        
        try:
            response = self.session.request(method, url, headers=headers, params=params)
            response.raise_for_status()
            logger.debug(f"API request successful: {method} {endpoint}")
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"API request failed: {e}")
            if hasattr(e, 'response') and e.response:
                logger.error(f"Response: {e.response.text}")
            raise