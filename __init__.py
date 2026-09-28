"""
Binance Futures Trading Bot - Core Package
This package provides trading functionality for Binance Futures Testnet
"""

from bot.client import BinanceFuturesClient
from bot.orders import OrderManager
from bot.validators import OrderValidator
from bot.logging_config import setup_logging, logger
from bot.api_client import DirectAPIClient

__version__ = "1.0.0"
__author__ = "Trading Bot Team"
__description__ = "Professional trading bot for Binance Futures Testnet"

# Initialize logging when package is imported
setup_logging()

# Define what gets imported with "from bot import *"
__all__ = [
    'BinanceFuturesClient',
    'OrderManager', 
    'OrderValidator',
    'DirectAPIClient',
    'setup_logging',
    'logger'
]

# Package metadata
__all__.extend(['__version__', '__author__', '__description__'])