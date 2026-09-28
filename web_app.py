from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
import os
import logging
from bot.client import BinanceFuturesClient
from bot.orders import OrderManager
from bot.validators import OrderValidator
from bot.logging_config import logger

load_dotenv()

app = Flask(__name__, template_folder='web', static_folder='web')
CORS(app)

# Initialize bot components
try:
    client = BinanceFuturesClient()
    order_manager = OrderManager(client)
    validator = OrderValidator()
    logger.info("Web application initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize bot: {e}")
    client = None
    order_manager = None

@app.route('/')
def index():
    """Serve the dashboard"""
    return render_template('dashboard.html')

@app.route('/api/place_order', methods=['POST'])
def place_order():
    """API endpoint to place orders"""
    try:
        data = request.json
        
        # Validate inputs
        valid, symbol = validator.validate_symbol(data.get('symbol', ''))
        if not valid:
            return jsonify({'success': False, 'error': symbol}), 400
        
        valid, side = validator.validate_side(data.get('side', ''))
        if not valid:
            return jsonify({'success': False, 'error': side}), 400
        
        valid, order_type = validator.validate_order_type(data.get('orderType', ''))
        if not valid:
            return jsonify({'success': False, 'error': order_type}), 400
        
        valid, quantity = validator.validate_quantity(str(data.get('quantity', '')), symbol)
        if not valid:
            return jsonify({'success': False, 'error': quantity}), 400
        
        price = None
        if order_type == 'LIMIT':
            valid, price = validator.validate_price(str(data.get('price', '')))
            if not valid:
                return jsonify({'success': False, 'error': price}), 400
        
        # Place order
        if order_type == 'MARKET':
            result = order_manager.place_market_order(symbol, side, quantity)
        else:
            result = order_manager.place_limit_order(symbol, side, quantity, price)
        
        if result['success']:
            logger.info(f"Order placed successfully via web: {result}")
            return jsonify(result)
        else:
            logger.error(f"Order failed via web: {result}")
            return jsonify(result), 400
            
    except Exception as e:
        logger.error(f"API error: {e}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/account_info', methods=['GET'])
def get_account_info():
    """Get account information"""
    try:
        if not client:
            return jsonify({'success': False, 'error': 'Client not initialized'}), 500
        
        account_info = client.get_account_info()
        return jsonify({'success': True, 'data': account_info})
    except Exception as e:
        logger.error(f"Failed to get account info: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/price/<symbol>', methods=['GET'])
def get_price(symbol):
    """Get current price for symbol"""
    try:
        if not client:
            return jsonify({'success': False, 'error': 'Client not initialized'}), 500
        
        price = client.get_symbol_price(symbol)
        return jsonify({'success': True, 'price': price})
    except Exception as e:
        logger.error(f"Failed to get price: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)