import re
from typing import Tuple, Optional
from decimal import Decimal, InvalidOperation
import logging

logger = logging.getLogger(__name__)

class OrderValidator:
    """Validate order parameters"""
    
    VALID_SYMBOLS = ['BTCUSDT', 'ETHUSDT', 'BNBUSDT', 'SOLUSDT', 'XRPUSDT']
    VALID_SIDES = ['BUY', 'SELL']
    VALID_ORDER_TYPES = ['MARKET', 'LIMIT']
    
    @staticmethod
    def validate_symbol(symbol: str) -> Tuple[bool, str]:
        """Validate trading symbol"""
        if not symbol or not isinstance(symbol, str):
            return False, "Symbol must be a non-empty string"
        
        symbol_upper = symbol.upper()
        if symbol_upper not in OrderValidator.VALID_SYMBOLS:
            return False, f"Invalid symbol. Valid symbols: {', '.join(OrderValidator.VALID_SYMBOLS)}"
        
        return True, symbol_upper
    
    @staticmethod
    def validate_side(side: str) -> Tuple[bool, str]:
        """Validate order side"""
        if not side:
            return False, "Side cannot be empty"
        
        side_upper = side.upper()
        if side_upper not in OrderValidator.VALID_SIDES:
            return False, f"Invalid side. Must be BUY or SELL"
        
        return True, side_upper
    
    @staticmethod
    def validate_order_type(order_type: str) -> Tuple[bool, str]:
        """Validate order type"""
        if not order_type:
            return False, "Order type cannot be empty"
        
        type_upper = order_type.upper()
        if type_upper not in OrderValidator.VALID_ORDER_TYPES:
            return False, f"Invalid order type. Must be MARKET or LIMIT"
        
        return True, type_upper
    
    @staticmethod
    def validate_quantity(quantity: str, symbol: str = "BTCUSDT") -> Tuple[bool, float]:
        """Validate order quantity"""
        try:
            qty = float(quantity)
            if qty <= 0:
                return False, "Quantity must be greater than 0"
            
            # Minimum quantity checks per symbol
            min_qty = {
                'BTCUSDT': 0.001,
                'ETHUSDT': 0.01,
                'BNBUSDT': 0.01,
                'SOLUSDT': 0.1,
                'XRPUSDT': 1.0
            }.get(symbol, 0.001)
            
            if qty < min_qty:
                return False, f"Minimum quantity for {symbol} is {min_qty}"
            
            return True, round(qty, 3)
            
        except (ValueError, TypeError):
            return False, "Quantity must be a valid number"
    
    @staticmethod
    def validate_price(price: str) -> Tuple[bool, float]:
        """Validate limit price"""
        try:
            price_float = float(price)
            if price_float <= 0:
                return False, "Price must be greater than 0"
            return True, round(price_float, 2)
        except (ValueError, TypeError):
            return False, "Price must be a valid number"