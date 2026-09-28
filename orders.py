from binance.exceptions import BinanceAPIException, BinanceRequestException
from binance.enums import *
import logging
from typing import Dict, Any
import time

logger = logging.getLogger(__name__)

class OrderManager:
    """Handle order placement and management"""
    
    def __init__(self, client):
        self.client = client
        self.client_obj = client.client
    
    def place_market_order(self, symbol: str, side: str, quantity: float) -> Dict[str, Any]:
        """Place a market order"""
        try:
            logger.info(f"Placing MARKET {side} order for {quantity} {symbol}")
            
            order = self.client_obj.futures_create_order(
                symbol=symbol,
                side=side,
                type=ORDER_TYPE_MARKET,
                quantity=quantity
            )
            
            logger.info(f"Market order placed successfully - Order ID: {order['orderId']}")
            
            # Get order details
            order_details = self.get_order_details(symbol, order['orderId'])
            
            return {
                'success': True,
                'order_id': order['orderId'],
                'status': order['status'],
                'executed_qty': order.get('executedQty', '0'),
                'avg_price': order_details.get('avgPrice', '0'),
                'raw_response': order
            }
            
        except BinanceAPIException as e:
            logger.error(f"Binance API error placing market order: {e.message}")
            return {'success': False, 'error': e.message}
        except BinanceRequestException as e:
            logger.error(f"Network error placing market order: {e}")
            return {'success': False, 'error': f"Network error: {str(e)}"}
        except Exception as e:
            logger.error(f"Unexpected error placing market order: {e}")
            return {'success': False, 'error': str(e)}
    
    def place_limit_order(self, symbol: str, side: str, quantity: float, price: float) -> Dict[str, Any]:
        """Place a limit order"""
        try:
            logger.info(f"Placing LIMIT {side} order for {quantity} {symbol} at ${price}")
            
            order = self.client_obj.futures_create_order(
                symbol=symbol,
                side=side,
                type=ORDER_TYPE_LIMIT,
                quantity=quantity,
                price=price,
                timeInForce='GTC'
            )
            
            logger.info(f"Limit order placed successfully - Order ID: {order['orderId']}")
            
            return {
                'success': True,
                'order_id': order['orderId'],
                'status': order['status'],
                'executed_qty': order.get('executedQty', '0'),
                'price': order.get('price', price),
                'raw_response': order
            }
            
        except BinanceAPIException as e:
            logger.error(f"Binance API error placing limit order: {e.message}")
            return {'success': False, 'error': e.message}
        except BinanceRequestException as e:
            logger.error(f"Network error placing limit order: {e}")
            return {'success': False, 'error': f"Network error: {str(e)}"}
        except Exception as e:
            logger.error(f"Unexpected error placing limit order: {e}")
            return {'success': False, 'error': str(e)}
    
    def get_order_details(self, symbol: str, order_id: int) -> Dict[str, Any]:
        """Get detailed order information"""
        try:
            order = self.client_obj.futures_get_order(symbol=symbol, orderId=order_id)
            return order
        except Exception as e:
            logger.warning(f"Failed to get order details: {e}")
            return {}
    
    def cancel_order(self, symbol: str, order_id: int) -> bool:
        """Cancel an existing order"""
        try:
            result = self.client_obj.futures_cancel_order(symbol=symbol, orderId=order_id)
            logger.info(f"Order {order_id} cancelled successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to cancel order {order_id}: {e}")
            return False,