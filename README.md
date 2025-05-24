# Binance Futures Trading Bot

A Python trading bot for Binance Futures Testnet with market, limit, and stop-limit order capabilities.

## Features
- Place market/limit/stop-limit orders
- Close existing positions
- Automatic time synchronization
- Comprehensive error handling
- Detailed logging

## Quick Start
```bash
git clone https://github.com/Shanub11/Binance-Trading-Bot.git
cd Binance-Trading-Bot
pip install -r requirements.txt
```
# Run with testnet API keys
python src/trading_bot.py --api-key YOUR_KEY --api-secret YOUR_SECRET --symbol BTCUSDT --side BUY --quantity 0.001 --market

Usage:

Place Market Order
python main.py --api-key YOUR_API_KEY --api-secret YOUR_API_SECRET --symbol BTCUSDT --side BUY --quantity 0.001 --market

Place Limit Order
python main.py --api-key YOUR_API_KEY --api-secret YOUR_API_SECRET --symbol BTCUSDT --side SELL --quantity 0.001 --limit 110000

Place Stop-Limit Order
python main.py --api-key YOUR_API_KEY --api-secret YOUR_API_SECRET --symbol BTCUSDT --side BUY --quantity 0.001 --stop-limit 109000 108500

Close Position
python main.py --api-key YOUR_API_KEY --api-secret YOUR_API_SECRET --symbol BTCUSDT --close

Logging
Logs are saved in the logs/trading_bot.log file.
