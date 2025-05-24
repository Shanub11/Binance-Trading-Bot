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

# Run with testnet API keys
python src/trading_bot.py --api-key YOUR_KEY --api-secret YOUR_SECRET --symbol BTCUSDT --side BUY --quantity 0.001 --market
