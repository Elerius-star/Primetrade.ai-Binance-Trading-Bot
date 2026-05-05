from binance.client import Client
from binance.exceptions import BinanceAPIException, BinanceRequestException
from binance.enums import *
import logging
import os
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

class BinanceFuturesClient:
    """Wrapper for Binance Futures Testnet API"""
    
    def __init__(self, api_key: str = None, api_secret: str = None):
        """Initialize the Binance Futures client"""
        
        self.api_key = api_key or os.getenv('BINANCE_API_KEY')
        self.api_secret = api_secret or os.getenv('BINANCE_API_SECRET')
        
        # Check for mock mode
        self.use_mock = os.getenv('USE_MOCK_MODE', 'false').lower() == 'true'
        
        if self.use_mock:
            logger.warning("RUNNING IN MOCK MODE - No real API calls")
            self.client = None
            return
        
        if not self.api_key or not self.api_secret:
            raise ValueError("API credentials not found. Set BINANCE_API_KEY and BINANCE_API_SECRET")
        
        # Updated URLs for Binance Testnet
        try:
            # Initialize client with testnet=True
            self.client = Client(
                api_key=self.api_key,
                api_secret=self.api_secret,
                testnet=True
            )
            
            # Use the CORRECT testnet URLs
            self.client.API_URL = 'https://testnet.binancefuture.com/fapi/v1'
            self.client.WS_URL = 'wss://stream.binancefuture.com/ws'
            
            # Test connection with new URL
            self.test_connection()
            logger.info("Successfully connected to Binance Futures Testnet")
            
        except Exception as e:
            logger.error(f"Failed to connect: {e}")
            raise
    
    def test_connection(self) -> bool:
        """Test API connection"""
        if self.use_mock:
            return True
            
        try:
            # Try to get server time using futures endpoint
            response = self.client.futures_time()
            logger.debug(f"Connected. Server time: {response}")
            return True
        except Exception as e:
            logger.error(f"Connection test failed: {e}")
            raise
    
    def get_account_info(self):
        """Get futures account information"""
        if self.use_mock:
            return self._get_mock_account()
            
        try:
            account_info = self.client.futures_account()
            logger.debug(f"Account info retrieved successfully")
            return account_info
        except BinanceAPIException as e:
            logger.error(f"Binance API error: {e.message}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            raise
    
    def get_symbol_price(self, symbol: str) -> float:
        """Get current price for a symbol"""
        if self.use_mock:
            return self._get_mock_price(symbol)
            
        try:
            ticker = self.client.futures_symbol_ticker(symbol=symbol)
            price = float(ticker['price'])
            logger.debug(f"Current price for {symbol}: {price}")
            return price
        except Exception as e:
            logger.error(f"Failed to get price for {symbol}: {e}")
            raise
    
    def _get_mock_account(self):
        """Return mock account data for testing"""
        return {
            'assets': [
                {'asset': 'USDT', 'walletBalance': '10000', 'availableBalance': '10000', 'unrealizedProfit': '0'}
            ],
            'totalWalletBalance': '10000'
        }
    
    def _get_mock_price(self, symbol):
        """Return mock price for testing"""
        import random
        prices = {
            'BTCUSDT': 50000,
            'ETHUSDT': 3000,
            'BNBUSDT': 400,
            'SOLUSDT': 100,
            'XRPUSDT': 0.5
        }
        base_price = prices.get(symbol, 100)
        # Add small random variation
        return base_price + random.uniform(-base_price * 0.01, base_price * 0.01)