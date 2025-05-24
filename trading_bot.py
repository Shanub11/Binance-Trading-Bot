import logging
from binance import Client
from binance.exceptions import BinanceAPIException
import argparse
from datetime import datetime
import time
import sys

class BasicBot:
    def __init__(self, api_key, api_secret, testnet=True):
        """
        Initialize the trading bot with API credentials
        :param api_key: Binance API key
        :param api_secret: Binance API secret
        :param testnet: Boolean indicating whether to use testnet (default True)
        """
        self.api_key = api_key
        self.api_secret = api_secret
        self.testnet = testnet
        self.time_offset = 0
        
        # Configure logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('trading_bot.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger('BinanceTradingBot')
        
        try:
            self.client = Client(
                api_key, 
                api_secret,
                testnet=testnet,
                requests_params={
                    'timeout': 10
                    
                }
            )
            self.sync_time()  # Initial time synchronization
            self.logger.info("Successfully connected to Binance API")
        except Exception as e:
            self.logger.error(f"Failed to initialize client: {e}")
            raise

    def sync_time(self):
        """Synchronize local time with Binance server"""
        try:
            server_time = self.client.get_server_time()['serverTime']
            local_time = int(time.time() * 1000)
            self.time_offset = server_time - local_time
            self.logger.info(f"Time synchronized. Offset: {self.time_offset}ms")
        except Exception as e:
            self.logger.warning(f"Time sync failed: {e}")
            self.time_offset = 0

    def validate_symbol(self, symbol):
        """
        Validate that the symbol exists and is tradable
        :param symbol: Trading pair symbol (e.g., BTCUSDT)
        :return: Boolean indicating validity
        """
        try:
            info = self.client.futures_exchange_info()
            for s in info['symbols']:
                if s['symbol'] == symbol and s['status'] == 'TRADING':
                    return True
            return False
        except BinanceAPIException as e:
            self.logger.error(f"Error validating symbol: {e}")
            return False

    def validate_quantity(self, symbol, quantity):
        """
        Validate that the quantity meets the exchange requirements
        :param symbol: Trading pair symbol
        :param quantity: Quantity to trade
        :return: Boolean indicating validity
        """
        try:
            info = self.client.futures_exchange_info()
            for s in info['symbols']:
                if s['symbol'] == symbol:
                    filters = {f['filterType']: f for f in s['filters']}
                    lot_size = filters['LOT_SIZE']
                    min_qty = float(lot_size['minQty'])
                    max_qty = float(lot_size['maxQty'])
                    step_size = float(lot_size['stepSize'])
                    
                    if quantity < min_qty or quantity > max_qty:
                        return False
                    
                    # Check if quantity is a multiple of step size
                    if (quantity / step_size) % 1 != 0:
                        return False
                    
                    return True
            return False
        except BinanceAPIException as e:
            self.logger.error(f"Error validating quantity: {e}")
            return False

    def place_market_order(self, symbol, side, quantity, retries=3):
        """
        Place a market order with retry logic
        :param symbol: Trading pair symbol
        :param side: 'BUY' or 'SELL'
        :param quantity: Quantity to trade
        :param retries: Number of retry attempts
        :return: Order response or None if failed
        """
        for attempt in range(retries):
            try:
                self.sync_time()  # Sync time before each attempt
                self.logger.info(f"Placing market order (attempt {attempt + 1}): {side} {quantity} {symbol}")
                order = self.client.futures_create_order(
                    symbol=symbol,
                    side=side,
                    type='MARKET',
                    quantity=quantity,
                    timestamp=int(time.time() * 1000 + self.time_offset)
                )
                self.logger.info(f"Market order executed: {order}")
                return order
            except BinanceAPIException as e:
                if e.code == -1021 and attempt < retries - 1:  # Timestamp error
                    time.sleep(1)
                    continue
                self.logger.error(f"Market order failed: {e}")
                return None

    def place_limit_order(self, symbol, side, quantity, price, retries=3):
        """
        Place a limit order with retry logic
        :param symbol: Trading pair symbol
        :param side: 'BUY' or 'SELL'
        :param quantity: Quantity to trade
        :param price: Limit price
        :param retries: Number of retry attempts
        :return: Order response or None if failed
        """
        for attempt in range(retries):
            try:
                self.sync_time()  # Sync time before each attempt
                self.logger.info(f"Placing limit order (attempt {attempt + 1}): {side} {quantity} {symbol} @ {price}")
                order = self.client.futures_create_order(
                    symbol=symbol,
                    side=side,
                    type='LIMIT',
                    timeInForce='GTC',
                    quantity=quantity,
                    price=price
                )
                self.logger.info(f"Limit order placed: {order}")
                return order
            except BinanceAPIException as e:
                if e.code == -1021 and attempt < retries - 1:  # Timestamp error
                    time.sleep(1)
                    continue
                self.logger.error(f"Limit order failed: {e}")
                return None

    def place_stop_limit_order(self, symbol, side, quantity, price, stop_price, retries=3):
        """
        Place a stop-limit order with retry logic
        :param symbol: Trading pair symbol
        :param side: 'BUY' or 'SELL'
        :param quantity: Quantity to trade
        :param price: Limit price
        :param stop_price: Stop price
        :param retries: Number of retry attempts
        :return: Order response or None if failed
        """
        for attempt in range(retries):
            try:
                self.sync_time()  # Sync time before each attempt
                self.logger.info(f"Placing stop-limit order (attempt {attempt + 1}): {side} {quantity} {symbol} @ {price} (stop: {stop_price})")
                order = self.client.futures_create_order(
                    symbol=symbol,
                    side=side,
                    type='STOP',
                    timeInForce='GTC',
                    quantity=quantity,
                    price=price,
                    stopPrice=stop_price
                )
                self.logger.info(f"Stop-limit order placed: {order}")
                return order
            except BinanceAPIException as e:
                if e.code == -1021 and attempt < retries - 1:  # Timestamp error
                    time.sleep(1)
                    continue
                self.logger.error(f"Stop-limit order failed: {e}")
                return None

    def get_order_status(self, symbol, order_id):
        """
        Check the status of an order
        :param symbol: Trading pair symbol
        :param order_id: Order ID to check
        :return: Order status or None if failed
        """
        try:
            status = self.client.futures_get_order(symbol=symbol, orderId=order_id)
            self.logger.info(f"Order status: {status}")
            return status
        except BinanceAPIException as e:
            self.logger.error(f"Failed to get order status: {e}")
            return None

    def cancel_order(self, symbol, order_id):
        """
        Cancel an existing order
        :param symbol: Trading pair symbol
        :param order_id: Order ID to cancel
        :return: Cancellation response or None if failed
        """
        try:
            result = self.client.futures_cancel_order(symbol=symbol, orderId=order_id)
            self.logger.info(f"Order cancelled: {result}")
            return result
        except BinanceAPIException as e:
            self.logger.error(f"Failed to cancel order: {e}")
            return None
        
    def close_position(self, symbol, side=None, quantity=None, order_type='MARKET', price=None, retries=3):
        """
        Close a position (market or limit)
        :param symbol: Trading pair (e.g. BTCUSDT)
        :param side: Optional (auto-detects if None)
        :param quantity: Optional (uses full position if None)
        :param order_type: 'MARKET' or 'LIMIT'
        :param price: Required for limit orders
        """
        try:
            # Auto-detect position if side/quantity not provided
            if side is None or quantity is None:
                position = self.get_position(symbol)
                if not position:
                    raise ValueError("No open position found")
                
                if side is None:
                    side = 'SELL' if float(position['positionAmt']) > 0 else 'BUY'
                if quantity is None:
                    quantity = abs(float(position['positionAmt']))
            
            if order_type == 'MARKET':
                return self.place_market_order(symbol, side, quantity, retries)
            elif order_type == 'LIMIT':
                if price is None:
                    raise ValueError("Price required for limit orders")
                return self.place_limit_order(symbol, side, quantity, price, retries)
            else:
                raise ValueError("Invalid order type")
        
        except Exception as e:
            self.logger.error(f"Failed to close position: {e}")
            return None

    def get_position(self, symbol):
        """Get current position details"""
        try:
            positions = self.client.futures_position_information()
            for p in positions:
                if p['symbol'] == symbol and float(p['positionAmt']) != 0:
                    return p
            return None
        except Exception as e:
            self.logger.error(f"Error getting position: {e}")
            return None 

    def print_position_details(self, position):
        """Print formatted position information"""
        print(f"\n📊 Current Position:")
        print(f"Symbol: {position['symbol']}")
        print(f"Direction: {'LONG' if float(position['positionAmt']) > 0 else 'SHORT'}")
        print(f"Size: {abs(float(position['positionAmt']))}")
        print(f"Entry Price: {position['entryPrice']}")
        print(f"Mark Price: {position['markPrice']}")
        print(f"Unrealized PnL: {position['unRealizedProfit']}")       


def parse_args():
    """
    Parse command line arguments
    :return: Parsed arguments
    """
    parser = argparse.ArgumentParser(description='Binance Futures Trading Bot')

    # Required API credentials
    parser.add_argument('--api-key', required=True, help='Binance API key')
    parser.add_argument('--api-secret', required=True, help='Binance API secret')

    # Trading parameters
    parser.add_argument('--symbol', required=True, help='Trading pair symbol (e.g., BTCUSDT)')
    parser.add_argument('--side', choices=['BUY', 'SELL'], help='Order side (BUY or SELL)')
    parser.add_argument('--quantity', type=float, help='Quantity to trade')

    # Close position flag
    parser.add_argument('--close', action='store_true', help='Close existing position')
    parser.add_argument('--close-type', choices=['MARKET', 'LIMIT'], default='MARKET', help='Order type for closing position')
    parser.add_argument('--close-price', type=float, help='Price for limit close order')


    # Mutually exclusive order types
    order_type_group = parser.add_mutually_exclusive_group(required=False)
    order_type_group.add_argument('--market', action='store_true', help='Place a market order')
    order_type_group.add_argument('--limit', type=float, help='Place a limit order with specified price')
    order_type_group.add_argument('--stop-limit', nargs=2, type=float, metavar=('PRICE', 'STOP_PRICE'),
                                  help='Place a stop-limit order with specified price and stop price')

    args = parser.parse_args()

    # Enforce one of the order type flags unless --close is specified
    if not args.close and not (args.market or args.limit or args.stop_limit):
        parser.error("One of --market, --limit, or --stop-limit is required unless --close is specified.")

    return args

def main():
    """
    Main function to run the trading bot
    """
    args = parse_args()
    
    try:
        # Initialize the bot
        bot = BasicBot(args.api_key, args.api_secret)
        
        # Verify time synchronization
        server_time = bot.client.get_server_time()['serverTime']
        local_time = int(time.time() * 1000)
        print(f"Time synchronization check:")
        print(f"Server time: {server_time}")
        print(f"Local time: {local_time}")
        print(f"Difference: {server_time - local_time}ms (should be < 1000ms)")
        
        # Position Closing Flow
        if args.close:
            print("\n=== Closing Position ===")
            position = bot.get_position(args.symbol)
            
            if not position:
                print(f"No open position found for {args.symbol}")
                return
            
            bot.print_position_details(position)
            
            order = bot.close_position(
                symbol=args.symbol,
                order_type=args.close_type,
                price=args.close_price
            )
            
            if order:
                print(f"\nPosition closed successfully:")
                print(f"ID: {order['orderId']}")
                print(f"Executed Qty: {order.get('executedQty', '0')}")
                print(f"Status: {order['status']}")
            else:
                print("\nFailed to close position")
            return
        
        # Order Placement Flow
        print("\n=== Placing New Order ===")
        # Validate symbol
        if not bot.validate_symbol(args.symbol):
            print(f"Invalid or untradable symbol: {args.symbol}")
            return
        
        # Validate quantity
        if not bot.validate_quantity(args.symbol, args.quantity):
            print(f"Invalid quantity for symbol {args.symbol}")
            return
        
        # Place the appropriate order
        if args.market:
            order = bot.place_market_order(args.symbol, args.side, args.quantity)
        elif args.limit:
            order = bot.place_limit_order(args.symbol, args.side, args.quantity, args.limit)
        elif args.stop_limit:
            price, stop_price = args.stop_limit
            order = bot.place_stop_limit_order(args.symbol, args.side, args.quantity, price, stop_price)
        
        if order:
            print(f"\nOrder successfully placed:")
            print(f"ID: {order['orderId']}")
            print(f"Symbol: {order['symbol']}")
            print(f"Side: {order['side']}")
            print(f"Type: {order['type']}")
            print(f"Quantity: {order['origQty']}")
            if 'price' in order:
                print(f"Price: {order['price']}")
            if 'stopPrice' in order:
                print(f"Stop Price: {order['stopPrice']}")
            print(f"Status: {order['status']}")
        else:
            print("\nFailed to place order. Check logs for details.")
            
    except Exception as e:
        print(f"\nAn error occurred: {e}")

if __name__ == '__main__':
    main()
