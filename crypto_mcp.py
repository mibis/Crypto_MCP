from fastmcp import FastMCP
import requests
import logging
import time
from typing import Optional, Dict, Any
from datetime import datetime
import pandas as pd
import numpy as np
import sqlite3
import json
import matplotlib.pyplot as plt
import io
import base64
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from rich.progress import Progress, SpinnerColumn, TextColumn
import argparse
import sys
from flask import Flask, jsonify, request, send_file
from flask_cors import CORS
import threading

# Global variables
alerts = []

# Logging yapılandırması
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('crypto_mcp.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('Crypto_MCP')

# Cache configuration
CACHE_EXPIRY_SECONDS = 300  # 5 minutes
price_cache: Dict[str, Dict[str, Any]] = {}

def get_cached_data(key: str) -> Optional[Any]:
    """Get data from cache if not expired."""
    if key in price_cache:
        cached_item = price_cache[key]
        if time.time() - cached_item['timestamp'] < CACHE_EXPIRY_SECONDS:
            logger.info(f"Cache hit for {key}")
            return cached_item['data']
        else:
            # Remove expired cache entry
            del price_cache[key]
            logger.info(f"Cache expired for {key}")
    return None

def set_cached_data(key: str, data: Any) -> None:
    """Store data in cache with timestamp."""
    price_cache[key] = {
        'data': data,
        'timestamp': time.time()
    }
    logger.info(f"Cached data for {key}")

def clear_expired_cache() -> None:
    """Remove all expired cache entries."""
    current_time = time.time()
    expired_keys = [
        key for key, item in price_cache.items()
        if current_time - item['timestamp'] >= CACHE_EXPIRY_SECONDS
    ]
    for key in expired_keys:
        del price_cache[key]
        logger.info(f"Removed expired cache entry: {key}")

# Özel exception sınıfları
class CryptoAPIError(Exception):
    """Crypto API ile ilgili hatalar için temel exception"""
    def __init__(self, message: str, api_name: str, status_code: Optional[int] = None):
        self.api_name = api_name
        self.status_code = status_code
        super().__init__(f"{api_name}: {message}")

class APIRateLimitError(CryptoAPIError):
    """API rate limit hatası"""
    pass

class APINetworkError(CryptoAPIError):
    """API network hatası"""
    pass

class APIDataError(CryptoAPIError):
    """API veri hatası"""
    pass

mcp = FastMCP("Crypto_MCP")

# API çağrısı için güvenli wrapper
def safe_api_call(url: str, api_name: str, timeout: int = 10, use_cache: bool = True) -> Dict[str, Any]:
    """
    API çağrısı yapan güvenli wrapper fonksiyon.

    Args:
        url: API endpoint URL'i
        api_name: API adı (logging için)
        timeout: Timeout süresi (saniye)
        use_cache: Cache kullanılıp kullanılmayacağı

    Returns:
        API response JSON

    Raises:
        CryptoAPIError: API hatası durumunda
    """
    # Check cache first if enabled
    if use_cache:
        cached_data = get_cached_data(url)
        if cached_data is not None:
            return cached_data

    try:
        logger.info(f"Calling {api_name} API: {url}")
        response = requests.get(url, timeout=timeout)

        if response.status_code == 429:
            logger.warning(f"Rate limit exceeded for {api_name}")
            raise APIRateLimitError("Rate limit exceeded", api_name, response.status_code)

        response.raise_for_status()  # HTTP hatalarını yakala

        data = response.json()
        logger.info(f"Successfully received data from {api_name}")

        # Cache the successful response
        if use_cache:
            set_cached_data(url, data)

        return data

    except APIRateLimitError:
        # Re-raise rate limit errors
        raise
    except APINetworkError:
        # Re-raise network errors
        raise
    except APIDataError:
        # Re-raise data errors
        raise
    except CryptoAPIError:
        # Re-raise general API errors
        raise
    except requests.exceptions.Timeout:
        logger.error(f"Timeout error for {api_name}")
        raise APINetworkError("Request timeout", api_name)

    except requests.exceptions.ConnectionError:
        logger.error(f"Connection error for {api_name}")
        raise APINetworkError("Connection failed", api_name)

    except requests.exceptions.HTTPError as e:
        logger.error(f"HTTP error for {api_name}: {e}")
        raise CryptoAPIError(f"HTTP {e.response.status_code}: {e.response.text}", api_name, e.response.status_code)

    except ValueError as e:
        logger.error(f"JSON parsing error for {api_name}: {e}")
        raise APIDataError("Invalid JSON response", api_name)

    except Exception as e:
        logger.error(f"Unexpected error for {api_name}: {e}")
        raise CryptoAPIError(f"Unexpected error: {str(e)}", api_name)

# Graceful degradation için alternatif API'ler
def get_crypto_price_with_fallback(coin_name: str) -> str:
    """
    Birden fazla API'yi deneyerek kripto para fiyatını alır.
    İlk çalışan API'yi kullanır.
    """
    apis = [
        {
            "name": "CoinGecko",
            "url": f"https://api.coingecko.com/api/v3/simple/price?ids={coin_name}&vs_currencies=usd",
            "parser": lambda data: data.get(coin_name, {}).get('usd')
        },
        {
            "name": "CoinStats",
            "url": f"https://api.coinstats.app/public/v1/coins/{coin_name}",
            "parser": lambda data: data.get('coin', {}).get('price')
        },
        {
            "name": "CoinPaprika",
            "url": f"https://api.coinpaprika.com/v1/tickers/{coin_name}-bitcoin",
            "parser": lambda data: data.get('quotes', {}).get('USD', {}).get('price')
        }
    ]

    last_error = None

    for api in apis:
        try:
            data = safe_api_call(api["url"], api["name"])
            price = api["parser"](data)

            if price is not None:
                logger.info(f"Successfully got price from {api['name']}: ${price}")
                return f"{coin_name.capitalize()} price: ${price} (via {api['name']})"

        except CryptoAPIError as e:
            logger.warning(f"Failed to get price from {api['name']}: {e}")
            last_error = e
            continue

    # Tüm API'ler başarısız olursa
    error_msg = f"Unable to fetch price for {coin_name}. All APIs failed."
    if last_error:
        error_msg += f" Last error: {last_error}"
    logger.error(error_msg)
    return error_msg

@mcp.tool()
def list_available_tools():
    """Lists all available cryptocurrency tools and their descriptions."""
    tools = {
        "get_crypto_price": "Get price from CoinGecko API (default)",
        "get_price_binance": "Get price from Binance exchange",
        "get_price_kraken": "Get price from Kraken exchange",
        "get_price_coinpaprika": "Get detailed price from CoinPaprika",
        "get_price_coinstats": "Get price from CoinStats",
        "get_crypto_news_cryptocompare": "Get latest crypto news",
        "market_analysis": "Get top 10 cryptocurrencies overview",
        "get_latest_news": "Get basic news placeholder",
        "clear_cache": "Clear all cached API responses",
        "get_cache_status": "Show current cache status and statistics",
        "technical_analysis": "Comprehensive technical analysis (RSI, MACD, BB, trend)",
        "rsi_indicator": "RSI analysis with buy/sell signals",
        "macd_analysis": "MACD analysis with crossover signals",
        "bollinger_bands_analysis": "Bollinger Bands analysis for volatility",
        "trend_analysis": "Trend analysis with moving averages and S/R levels",
        "portfolio_tracker": "Track portfolio performance and P&L",
        "risk_analysis": "Analyze risk metrics (volatility, Sharpe ratio, drawdown)",
        "correlation_analysis": "Analyze correlations between cryptocurrencies"
    }
    result = "Available Crypto_MCP Tools:\n"
    for name, desc in tools.items():
        result += f"- {name}: {desc}\n"
    return result

@mcp.tool()
def get_crypto_price(coin_name: str = "bitcoin"):
    """Gets the current price of a specific cryptocurrency in USD from CoinGecko."""
    try:
        return get_crypto_price_with_fallback(coin_name)
    except Exception as e:
        logger.error(f"Unexpected error in get_crypto_price: {e}")
        return f"Error fetching price for {coin_name}: {str(e)}"

@mcp.tool()
def get_price_binance(symbol: str = "BTCUSDT"):
    """Gets real-time cryptocurrency price from Binance exchange. Use symbols like BTCUSDT, ETHUSDT."""
    try:
        url = f"https://api.binance.com/api/v3/ticker/price?symbol={symbol}"
        data = safe_api_call(url, "Binance")
        price = data.get('price')

        if price is None:
            raise APIDataError("Price not found in response", "Binance")

        return f"{symbol} price (Binance): ${price}"

    except CryptoAPIError as e:
        logger.error(f"Binance API error: {e}")
        return f"Error fetching {symbol} from Binance: {e}"
    except Exception as e:
        logger.error(f"Unexpected error in get_price_binance: {e}")
        return f"Unexpected error fetching {symbol} from Binance: {str(e)}"

@mcp.tool()
def get_price_kraken(pair: str = "XBTUSD"):
    """Gets cryptocurrency price from Kraken exchange. Use pairs like XBTUSD (BTC), ETHUSD."""
    try:
        url = f"https://api.kraken.com/0/public/Ticker?pair={pair}"
        data = safe_api_call(url, "Kraken")

        result = data.get('result', {})
        if pair not in result:
            raise APIDataError(f"Pair {pair} not found in response", "Kraken")

        price_data = result[pair].get('c', [])
        if not price_data:
            raise APIDataError("Price data not available", "Kraken")

        price = price_data[0]
        return f"{pair} price (Kraken): ${price}"

    except CryptoAPIError as e:
        logger.error(f"Kraken API error: {e}")
        return f"Error fetching {pair} from Kraken: {e}"
    except Exception as e:
        logger.error(f"Unexpected error in get_price_kraken: {e}")
        return f"Unexpected error fetching {pair} from Kraken: {str(e)}"

@mcp.tool()
def get_price_coinpaprika(coin_id: str = "btc-bitcoin"):
    """Gets detailed cryptocurrency information from CoinPaprika. Use coin IDs like btc-bitcoin, eth-ethereum."""
    try:
        url = f"https://api.coinpaprika.com/v1/tickers/{coin_id}"
        data = safe_api_call(url, "CoinPaprika")

        quotes = data.get('quotes', {})
        usd_data = quotes.get('USD', {})
        price = usd_data.get('price')

        if price is None:
            raise APIDataError("Price not found in USD quotes", "CoinPaprika")

        return f"{coin_id} price (CoinPaprika): ${price}"

    except CryptoAPIError as e:
        logger.error(f"CoinPaprika API error: {e}")
        return f"Error fetching {coin_id} from CoinPaprika: {e}"
    except Exception as e:
        logger.error(f"Unexpected error in get_price_coinpaprika: {e}")
        return f"Unexpected error fetching {coin_id} from CoinPaprika: {str(e)}"

@mcp.tool()
def get_price_coinstats(coin: str = "bitcoin"):
    """Gets cryptocurrency price from CoinStats. Use coin names like bitcoin, ethereum."""
    try:
        url = f"https://api.coinstats.app/public/v1/coins/{coin}"
        data = safe_api_call(url, "CoinStats")

        coin_data = data.get('coin', {})
        price = coin_data.get('price')

        if price is None:
            raise APIDataError("Price not found in coin data", "CoinStats")

        return f"{coin} price (CoinStats): ${price}"

    except CryptoAPIError as e:
        logger.error(f"CoinStats API error: {e}")
        return f"Error fetching {coin} from CoinStats: {e}"
    except Exception as e:
        logger.error(f"Unexpected error in get_price_coinstats: {e}")
        return f"Unexpected error fetching {coin} from CoinStats: {str(e)}"

@mcp.tool()
def clear_cache():
    """Clears all cached API responses. Useful if you want fresh data."""
    try:
        global price_cache
        cache_size = len(price_cache)
        price_cache.clear()
        logger.info(f"Cache cleared. Removed {cache_size} entries.")
        return f"Cache cleared successfully. Removed {cache_size} cached entries."
    except Exception as e:
        logger.error(f"Error clearing cache: {e}")
        return f"Error clearing cache: {str(e)}"

@mcp.tool()
def get_price_bybit(symbol: str = "BTCUSDT"):
    """Gets cryptocurrency price from Bybit exchange. Use symbols like BTCUSDT, ETHUSDT."""
    try:
        url = f"https://api.bybit.com/v5/market/tickers?category=spot&symbol={symbol}"
        data = safe_api_call(url, "Bybit")

        if not data.get('result') or not data['result'].get('list'):
            raise APIDataError("No ticker data found", "Bybit")

        ticker = data['result']['list'][0]
        price = ticker.get('lastPrice')

        if price is None:
            raise APIDataError("Price not found in ticker data", "Bybit")

        return f"{symbol} price (Bybit): ${price}"

    except CryptoAPIError as e:
        logger.error(f"Bybit API error: {e}")
        return f"Error fetching {symbol} from Bybit: {e}"
    except Exception as e:
        logger.error(f"Unexpected error in get_price_bybit: {e}")
        return f"Unexpected error fetching {symbol} from Bybit: {str(e)}"

@mcp.tool()
def get_price_kucoin(symbol: str = "BTC-USDT"):
    """Gets cryptocurrency price from KuCoin exchange. Use symbols like BTC-USDT, ETH-USDT."""
    try:
        url = f"https://api.kucoin.com/api/v1/market/orderbook/level1?symbol={symbol}"
        data = safe_api_call(url, "KuCoin")

        if not data.get('data'):
            raise APIDataError("No orderbook data found", "KuCoin")

        price = data['data'].get('price')

        if price is None:
            raise APIDataError("Price not found in orderbook data", "KuCoin")

        return f"{symbol} price (KuCoin): ${price}"

    except CryptoAPIError as e:
        logger.error(f"KuCoin API error: {e}")
        return f"Error fetching {symbol} from KuCoin: {e}"
    except Exception as e:
        logger.error(f"Unexpected error in get_price_kucoin: {e}")
        return f"Unexpected error fetching {symbol} from KuCoin: {str(e)}"

@mcp.tool()
def get_uniswap_token_price(token_address: str = "0x1f9840a85d5af5bf1d1762f925bdaddc4201f984"):  # UNI token
    """Gets token price from Uniswap v3. Use token contract addresses."""
    try:
        # Using Uniswap v3 subgraph
        query = """
        {
          token(id: "%s") {
            symbol
            name
            derivedETH
          }
          bundle(id: "1") {
            ethPriceUSD
          }
        }
        """ % token_address.lower()

        url = "https://api.thegraph.com/subgraphs/name/uniswap/uniswap-v3"
        response = requests.post(url, json={'query': query}, timeout=10)

        if response.status_code != 200:
            raise APIDataError(f"HTTP {response.status_code}", "Uniswap")

        data = response.json()

        if data.get('errors'):
            raise APIDataError(f"GraphQL errors: {data['errors']}", "Uniswap")

        token_data = data.get('data', {}).get('token')
        bundle_data = data.get('data', {}).get('bundle')

        if not token_data or not bundle_data:
            raise APIDataError("Token or bundle data not found", "Uniswap")

        eth_price = float(bundle_data['ethPriceUSD'])
        token_eth_price = float(token_data['derivedETH'])
        usd_price = eth_price * token_eth_price

        return f"{token_data['symbol']} ({token_data['name']}) price (Uniswap): ${usd_price:.4f}"

    except CryptoAPIError as e:
        logger.error(f"Uniswap API error: {e}")
        return f"Error fetching token {token_address} from Uniswap: {e}"
    except Exception as e:
        logger.error(f"Unexpected error in get_uniswap_token_price: {e}")
        return f"Unexpected error fetching token {token_address} from Uniswap: {str(e)}"

@mcp.tool()
def get_cache_status():
    """Shows current cache status including number of entries and memory usage."""
    try:
        cache_size = len(price_cache)
        total_memory = sum(len(str(item['data'])) for item in price_cache.values())

        # Clear expired entries
        clear_expired_cache()
        active_size = len(price_cache)

        expired_count = cache_size - active_size

        return f"Cache Status:\n- Active entries: {active_size}\n- Expired entries cleared: {expired_count}\n- Approximate memory usage: {total_memory} characters\n- Cache expiry: {CACHE_EXPIRY_SECONDS} seconds"

    except Exception as e:
        logger.error(f"Error getting cache status: {e}")
        return f"Error getting cache status: {str(e)}"

@mcp.tool()
def get_crypto_news_cryptocompare(coin: str = "BTC"):
    """Gets latest crypto news from CryptoCompare. Use coin symbols like BTC, ETH."""
    try:
        url = f"https://min-api.cryptocompare.com/data/v2/news/?categories={coin}"
        data = safe_api_call(url, "CryptoCompare")

        news_list = data.get('Data', [])
        if not news_list:
            return f"No news found for {coin}"

        # Get first 3 news items
        news_items = []
        for item in news_list[:3]:
            title = item.get('title', 'No title')
            url = item.get('url', 'No URL')
            source = item.get('source', 'Unknown source')
            news_items.append(f"- {title} ({source}): {url}")

        return f"Latest {coin} news from CryptoCompare:\n" + "\n".join(news_items)

    except CryptoAPIError as e:
        logger.error(f"CryptoCompare API error: {e}")
        return f"Error fetching news for {coin} from CryptoCompare: {e}"
    except Exception as e:
        logger.error(f"Unexpected error in get_crypto_news_cryptocompare: {e}")
        return f"Unexpected error fetching news for {coin} from CryptoCompare: {str(e)}"

@mcp.tool()
def market_analysis():
    """Returns a summary table of the top 10 cryptocurrencies by market cap, including current price and 24h change percentage."""
    try:
        url = "https://api.coingecko.com/api/v3/coins/markets?vs_currency=usd&order=market_cap_desc&per_page=10&page=1"
        data = safe_api_call(url, "CoinGecko")

        if not data:
            raise APIDataError("No market data received", "CoinGecko")

        result = "Top 10 cryptocurrencies (CoinGecko):\n"
        for coin in data:
            name = coin.get('name', 'Unknown')
            symbol = coin.get('symbol', '').upper()
            price = coin.get('current_price')
            change_24h = coin.get('price_change_percentage_24h')

            if price is None or change_24h is None:
                result += f"{name} ({symbol}): Data unavailable\n"
            else:
                result += f"{name} ({symbol}): ${price} | 24h: {change_24h:.2f}%\n"

        return result

    except CryptoAPIError as e:
        logger.error(f"CoinGecko API error in market_analysis: {e}")
        return f"Error fetching market analysis from CoinGecko: {e}"
    except Exception as e:
        logger.error(f"Unexpected error in market_analysis: {e}")
        return f"Unexpected error fetching market analysis: {str(e)}"


# Teknik Analiz Fonksiyonları

def get_historical_prices(coin_id: str, days: int = 30) -> pd.DataFrame:
    """
    CoinGecko'dan historical price data çeker.

    Args:
        coin_id: CoinGecko coin ID (bitcoin, ethereum, etc.)
        days: Kaç günlük veri (max 365)

    Returns:
        DataFrame with timestamp, price, volume columns
    """
    try:
        url = f"https://api.coingecko.com/api/v3/coins/{coin_id}/market_chart?vs_currency=usd&days={days}&interval=daily"
        data = safe_api_call(url, "CoinGecko")

        prices = data.get('prices', [])
        volumes = data.get('total_volumes', [])

        if not prices:
            raise APIDataError("No price data available", "CoinGecko")

        # Create DataFrame
        df = pd.DataFrame(prices, columns=['timestamp', 'price'])
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        df['date'] = df['timestamp'].dt.date

        # Add volume data if available
        if volumes:
            volume_df = pd.DataFrame(volumes, columns=['timestamp', 'volume'])
            volume_df['timestamp'] = pd.to_datetime(volume_df['timestamp'], unit='ms')
            volume_df['date'] = volume_df['timestamp'].dt.date
            df = df.merge(volume_df[['date', 'volume']], on='date', how='left')

        df = df.sort_values('timestamp').reset_index(drop=True)
        return df

    except CryptoAPIError as e:
        logger.error(f"Error fetching historical data for {coin_id}: {e}")
        raise


def calculate_rsi(prices: pd.Series, period: int = 14) -> pd.Series:
    """Calculate Relative Strength Index (RSI)"""
    delta = prices.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    return rsi


def calculate_macd(prices: pd.Series, fast_period: int = 12, slow_period: int = 26, signal_period: int = 9):
    """Calculate MACD (Moving Average Convergence Divergence)"""
    fast_ema = prices.ewm(span=fast_period, adjust=False).mean()
    slow_ema = prices.ewm(span=slow_period, adjust=False).mean()
    macd = fast_ema - slow_ema
    signal = macd.ewm(span=signal_period, adjust=False).mean()
    histogram = macd - signal
    return macd, signal, histogram


def calculate_bollinger_bands(prices: pd.Series, period: int = 20, std_dev: float = 2.0):
    """Calculate Bollinger Bands"""
    sma = prices.rolling(window=period).mean()
    std = prices.rolling(window=period).std()
    upper_band = sma + (std * std_dev)
    lower_band = sma - (std * std_dev)
    return sma, upper_band, lower_band


def calculate_moving_averages(prices: pd.Series, periods: list = [20, 50, 200]):
    """Calculate multiple moving averages"""
    mas = {}
    for period in periods:
        mas[f'ma_{period}'] = prices.rolling(window=period).mean()
    return mas


def analyze_trend(mas: dict) -> str:
    """Analyze trend based on moving averages"""
    if 'ma_20' not in mas or 'ma_50' not in mas:
        return "Insufficient data for trend analysis"

    ma20 = mas['ma_20']
    ma50 = mas['ma_50']

    if len(ma20) < 2 or len(ma50) < 2:
        return "Insufficient data for trend analysis"

    # Get latest values
    current_ma20 = ma20.iloc[-1]
    current_ma50 = ma50.iloc[-1]
    prev_ma20 = ma20.iloc[-2]
    prev_ma50 = ma50.iloc[-2]

    # Trend analysis
    if current_ma20 > current_ma50 and prev_ma20 <= prev_ma50:
        return "Bullish crossover (MA20 crossed above MA50)"
    elif current_ma20 < current_ma50 and prev_ma20 >= prev_ma50:
        return "Bearish crossover (MA20 crossed below MA50)"
    elif current_ma20 > current_ma50:
        return "Bullish trend (MA20 above MA50)"
    elif current_ma20 < current_ma50:
        return "Bearish trend (MA20 below MA50)"
    else:
        return "Neutral (MA20 = MA50)"


def find_support_resistance(prices: pd.Series, window: int = 20) -> dict:
    """Find support and resistance levels"""
    if len(prices) < window:
        return {"support": None, "resistance": None}

    # Find local minima (support) and maxima (resistance)
    support_levels = []
    resistance_levels = []

    for i in range(window, len(prices) - window):
        window_data = prices.iloc[i-window:i+window+1]

        if prices.iloc[i] == window_data.min():
            support_levels.append(prices.iloc[i])
        elif prices.iloc[i] == window_data.max():
            resistance_levels.append(prices.iloc[i])

    # Get most recent levels
    support = support_levels[-1] if support_levels else None
    resistance = resistance_levels[-1] if resistance_levels else None

    return {
        "support": support,
        "resistance": resistance,
        "support_levels_found": len(support_levels),
        "resistance_levels_found": len(resistance_levels)
    }


@mcp.tool()
def technical_analysis(coin_id: str = "bitcoin", days: int = 30):
    """Perform comprehensive technical analysis on a cryptocurrency. Includes RSI, MACD, Bollinger Bands, moving averages, and trend analysis."""
    try:
        # Get historical data
        df = get_historical_prices(coin_id, days)

        if df.empty or len(df) < 20:
            return f"Insufficient data for {coin_id}. Need at least 20 days of data."

        prices = df['price']

        # Calculate indicators
        rsi = calculate_rsi(prices)
        macd, signal, histogram = calculate_macd(prices)
        sma, upper_bb, lower_bb = calculate_bollinger_bands(prices)
        mas = calculate_moving_averages(prices)

        # Trend analysis
        trend = analyze_trend(mas)

        # Support/Resistance
        sr_levels = find_support_resistance(prices)

        # Current values
        current_price = prices.iloc[-1]
        current_rsi = rsi.iloc[-1] if not pd.isna(rsi.iloc[-1]) else None
        current_macd = macd.iloc[-1] if not pd.isna(macd.iloc[-1]) else None
        current_signal = signal.iloc[-1] if not pd.isna(signal.iloc[-1]) else None
        current_sma = sma.iloc[-1] if not pd.isna(sma.iloc[-1]) else None
        current_upper = upper_bb.iloc[-1] if not pd.isna(upper_bb.iloc[-1]) else None
        current_lower = lower_bb.iloc[-1] if not pd.isna(lower_bb.iloc[-1]) else None

        # Generate analysis
        result = f"📊 Technical Analysis for {coin_id.upper()} (Last {days} days)\n\n"

        result += f"💰 Current Price: ${current_price:.2f}\n\n"

        # RSI Analysis
        if current_rsi:
            rsi_signal = "Overbought (Sell)" if current_rsi > 70 else "Oversold (Buy)" if current_rsi < 30 else "Neutral"
            result += f"📈 RSI (14): {current_rsi:.2f} - {rsi_signal}\n"

        # MACD Analysis
        if current_macd and current_signal:
            macd_signal = "Bullish" if current_macd > current_signal else "Bearish"
            result += f"📊 MACD: {current_macd:.4f} | Signal: {current_signal:.4f} - {macd_signal}\n"

        # Bollinger Bands
        if current_sma and current_upper and current_lower:
            bb_position = "Upper Band (Overbought)" if current_price > current_upper else "Lower Band (Oversold)" if current_price < current_lower else "Middle (Neutral)"
            result += f"📊 Bollinger Bands - SMA: ${current_sma:.2f}, Upper: ${current_upper:.2f}, Lower: ${current_lower:.2f}\n"
            result += f"   Position: {bb_position}\n"

        # Trend Analysis
        result += f"📈 Trend Analysis: {trend}\n"

        # Support/Resistance
        if sr_levels['support'] and sr_levels['resistance']:
            result += f"🎯 Support: ${sr_levels['support']:.2f} | Resistance: ${sr_levels['resistance']:.2f}\n"

        # Moving Averages
        ma_summary = []
        for period, ma_values in mas.items():
            if not pd.isna(ma_values.iloc[-1]):
                ma_summary.append(f"{period.upper()}: ${ma_values.iloc[-1]:.2f}")
        if ma_summary:
            result += f"📊 Moving Averages: {' | '.join(ma_summary)}\n"

        return result

    except CryptoAPIError as e:
        logger.error(f"Error in technical_analysis for {coin_id}: {e}")
        return f"Error performing technical analysis for {coin_id}: {e}"
    except Exception as e:
        logger.error(f"Unexpected error in technical_analysis: {e}")
        return f"Unexpected error in technical analysis: {str(e)}"


@mcp.tool()
def rsi_indicator(coin_id: str = "bitcoin", days: int = 30, period: int = 14):
    """Calculate and analyze RSI (Relative Strength Index) for a cryptocurrency."""
    try:
        df = get_historical_prices(coin_id, days)
        if df.empty or len(df) < period + 1:
            return f"Insufficient data for RSI calculation. Need at least {period + 1} days."

        prices = df['price']
        rsi = calculate_rsi(prices, period)

        current_rsi = rsi.iloc[-1]
        prev_rsi = rsi.iloc[-2] if len(rsi) > 1 else None

        # RSI Analysis
        if pd.isna(current_rsi):
            return f"Unable to calculate RSI for {coin_id}"

        if current_rsi > 70:
            signal = "OVERBOUGHT - Consider selling"
            strength = "Strong sell signal"
        elif current_rsi > 60:
            signal = "Bullish momentum weakening"
            strength = "Weak sell signal"
        elif current_rsi < 30:
            signal = "OVERSOLD - Consider buying"
            strength = "Strong buy signal"
        elif current_rsi < 40:
            signal = "Bearish momentum weakening"
            strength = "Weak buy signal"
        else:
            signal = "NEUTRAL - Sideways momentum"
            strength = "Neutral"

        trend = ""
        if prev_rsi and not pd.isna(prev_rsi):
            if current_rsi > prev_rsi:
                trend = "Rising 📈"
            elif current_rsi < prev_rsi:
                trend = "Falling 📉"
            else:
                trend = "Stable ➡️"

        result = f"📈 RSI Analysis for {coin_id.upper()}\n"
        result += f"RSI ({period}): {current_rsi:.2f}\n"
        result += f"Signal: {signal}\n"
        result += f"Trend: {trend}\n"
        result += f"Analysis: {strength}"

        return result

    except CryptoAPIError as e:
        logger.error(f"Error in rsi_indicator for {coin_id}: {e}")
        return f"Error calculating RSI for {coin_id}: {e}"
    except Exception as e:
        logger.error(f"Unexpected error in rsi_indicator: {e}")
        return f"Unexpected error in RSI calculation: {str(e)}"


@mcp.tool()
def macd_analysis(coin_id: str = "bitcoin", days: int = 30):
    """Calculate and analyze MACD (Moving Average Convergence Divergence) for a cryptocurrency."""
    try:
        df = get_historical_prices(coin_id, days)
        if df.empty or len(df) < 35:  # Need enough data for MACD calculation
            return f"Insufficient data for MACD analysis. Need at least 35 days."

        prices = df['price']
        macd, signal, histogram = calculate_macd(prices)

        current_macd = macd.iloc[-1]
        current_signal = signal.iloc[-1]
        current_hist = histogram.iloc[-1]

        prev_macd = macd.iloc[-2] if len(macd) > 1 else None
        prev_signal = signal.iloc[-2] if len(signal) > 1 else None
        prev_hist = histogram.iloc[-2] if len(histogram) > 1 else None

        # MACD Analysis
        if pd.isna(current_macd) or pd.isna(current_signal):
            return f"Unable to calculate MACD for {coin_id}"

        # Signal generation
        if current_macd > current_signal and (prev_macd and prev_signal and prev_macd <= prev_signal):
            signal_type = "BULLISH CROSSOVER 📈"
            strength = "Strong buy signal"
        elif current_macd < current_signal and (prev_macd and prev_signal and prev_macd >= prev_signal):
            signal_type = "BEARISH CROSSOVER 📉"
            strength = "Strong sell signal"
        elif current_macd > current_signal:
            signal_type = "Bullish (MACD > Signal)"
            strength = "Bullish momentum"
        elif current_macd < current_signal:
            signal_type = "Bearish (MACD < Signal)"
            strength = "Bearish momentum"
        else:
            signal_type = "Neutral (MACD = Signal)"
            strength = "Neutral momentum"

        # Histogram analysis
        hist_trend = ""
        if prev_hist and not pd.isna(prev_hist):
            if current_hist > prev_hist:
                hist_trend = "Strengthening 📊"
            elif current_hist < prev_hist:
                hist_trend = "Weakening 📊"
            else:
                hist_trend = "Stable 📊"

        result = f"📊 MACD Analysis for {coin_id.upper()}\n"
        result += f"MACD: {current_macd:.6f}\n"
        result += f"Signal Line: {current_signal:.6f}\n"
        result += f"Histogram: {current_hist:.6f}\n"
        result += f"Signal: {signal_type}\n"
        result += f"Momentum: {hist_trend}\n"
        result += f"Analysis: {strength}"

        return result

    except CryptoAPIError as e:
        logger.error(f"Error in macd_analysis for {coin_id}: {e}")
        return f"Error calculating MACD for {coin_id}: {e}"
    except Exception as e:
        logger.error(f"Unexpected error in macd_analysis: {e}")
        return f"Unexpected error in MACD analysis: {str(e)}"


@mcp.tool()
def bollinger_bands_analysis(coin_id: str = "bitcoin", days: int = 30):
    """Analyze Bollinger Bands for a cryptocurrency to identify volatility and potential reversal points."""
    try:
        df = get_historical_prices(coin_id, days)
        if df.empty or len(df) < 25:  # Need enough data for BB calculation
            return f"Insufficient data for Bollinger Bands analysis. Need at least 25 days."

        prices = df['price']
        sma, upper_bb, lower_bb = calculate_bollinger_bands(prices)

        current_price = prices.iloc[-1]
        current_sma = sma.iloc[-1]
        current_upper = upper_bb.iloc[-1]
        current_lower = lower_bb.iloc[-1]

        # Calculate position within bands
        if pd.isna(current_sma) or pd.isna(current_upper) or pd.isna(current_lower):
            return f"Unable to calculate Bollinger Bands for {coin_id}"

        band_width = (current_upper - current_lower) / current_sma * 100  # Bandwidth percentage

        if current_price >= current_upper:
            position = "ABOVE UPPER BAND - Overbought 📈"
            signal = "Potential reversal or strong uptrend"
        elif current_price <= current_lower:
            position = "BELOW LOWER BAND - Oversold 📉"
            signal = "Potential reversal or strong downtrend"
        elif current_price > current_sma:
            position = "ABOVE MIDDLE LINE - Bullish"
            signal = "Price in upper half of band"
        else:
            position = "BELOW MIDDLE LINE - Bearish"
            signal = "Price in lower half of band"

        # Volatility analysis
        if band_width > 5:
            volatility = "High volatility - Large price swings"
        elif band_width > 2:
            volatility = "Moderate volatility - Normal market conditions"
        else:
            volatility = "Low volatility - Price consolidation"

        result = f"📊 Bollinger Bands Analysis for {coin_id.upper()}\n"
        result += f"Current Price: ${current_price:.2f}\n"
        result += f"Middle Band (SMA): ${current_sma:.2f}\n"
        result += f"Upper Band: ${current_upper:.2f}\n"
        result += f"Lower Band: ${current_lower:.2f}\n"
        result += f"Band Width: {band_width:.2f}%\n"
        result += f"Position: {position}\n"
        result += f"Volatility: {volatility}\n"
        result += f"Signal: {signal}"

        return result

    except CryptoAPIError as e:
        logger.error(f"Error in bollinger_bands_analysis for {coin_id}: {e}")
        return f"Error calculating Bollinger Bands for {coin_id}: {e}"
    except Exception as e:
        logger.error(f"Unexpected error in bollinger_bands_analysis: {e}")
        return f"Unexpected error in Bollinger Bands analysis: {str(e)}"


@mcp.tool()
def trend_analysis(coin_id: str = "bitcoin", days: int = 60):
    """Analyze price trends using moving averages and identify support/resistance levels."""
    try:
        df = get_historical_prices(coin_id, days)
        if df.empty or len(df) < 50:  # Need enough data for trend analysis
            return f"Insufficient data for trend analysis. Need at least 50 days."

        prices = df['price']
        mas = calculate_moving_averages(prices, [20, 50, 100])

        # Trend analysis
        trend = analyze_trend(mas)

        # Support/Resistance analysis
        sr_levels = find_support_resistance(prices)

        # Current price vs moving averages
        current_price = prices.iloc[-1]
        ma_comparison = []

        for period, ma_values in mas.items():
            if not pd.isna(ma_values.iloc[-1]):
                ma_price = ma_values.iloc[-1]
                if current_price > ma_price:
                    ma_comparison.append(f"{period.upper()}: Above (${ma_price:.2f}) 📈")
                else:
                    ma_comparison.append(f"{period.upper()}: Below (${ma_price:.2f}) 📉")

        result = f"📈 Trend Analysis for {coin_id.upper()} (Last {days} days)\n\n"
        result += f"💰 Current Price: ${current_price:.2f}\n\n"
        result += f"📊 Overall Trend: {trend}\n\n"

        if ma_comparison:
            result += "Moving Average Analysis:\n"
            for comp in ma_comparison:
                result += f"• {comp}\n"
            result += "\n"

        if sr_levels['support'] or sr_levels['resistance']:
            result += "Support & Resistance Levels:\n"
            if sr_levels['support']:
                result += f"• Support: ${sr_levels['support']:.2f}\n"
            if sr_levels['resistance']:
                result += f"• Resistance: ${sr_levels['resistance']:.2f}\n"
            result += f"• Levels Found: {sr_levels['support_levels_found']} support, {sr_levels['resistance_levels_found']} resistance\n"

        # Price momentum (recent performance)
        if len(prices) >= 7:
            week_ago = prices.iloc[-8] if len(prices) > 7 else prices.iloc[0]
            weekly_change = (current_price - week_ago) / week_ago * 100
            momentum = "Strong Uptrend" if weekly_change > 5 else "Weak Uptrend" if weekly_change > 0 else "Downtrend" if weekly_change < -5 else "Sideways"
            result += f"\n📊 Weekly Momentum: {weekly_change:+.2f}% ({momentum})"

        return result

    except CryptoAPIError as e:
        logger.error(f"Error in trend_analysis for {coin_id}: {e}")
        return f"Error performing trend analysis for {coin_id}: {e}"
    except Exception as e:
        logger.error(f"Unexpected error in trend_analysis: {e}")
        return f"Unexpected error in trend analysis: {str(e)}"


# Portföy Analizi Fonksiyonları

def calculate_portfolio_returns(portfolio: dict, days: int = 30) -> dict:
    """
    Calculate portfolio returns and performance metrics.

    Args:
        portfolio: Dict of {coin_id: amount} or {coin_id: {'amount': x, 'cost_basis': y}}
        days: Number of days to look back

    Returns:
        Dict with performance metrics
    """
    try:
        total_value = 0
        total_cost = 0
        holdings = []

        for coin_id, holding in portfolio.items():
            if isinstance(holding, dict):
                amount = holding.get('amount', 0)
                cost_basis = holding.get('cost_basis', 0)
            else:
                amount = holding
                cost_basis = 0  # Unknown cost basis

            # Get current price
            try:
                current_price = get_crypto_price_with_fallback(coin_id)
                if isinstance(current_price, str) and current_price.startswith("Error"):
                    logger.warning(f"Could not get price for {coin_id}")
                    continue

                # Extract price from string response
                if isinstance(current_price, str):
                    import re
                    price_match = re.search(r'\$([0-9,]+\.?[0-9]*)', current_price)
                    if price_match:
                        current_price = float(price_match.group(1).replace(',', ''))
                    else:
                        continue

                current_value = amount * current_price
                total_value += current_value

                if cost_basis > 0:
                    total_cost += cost_basis
                else:
                    total_cost += current_value  # Assume current value as cost if unknown

                holdings.append({
                    'coin': coin_id,
                    'amount': amount,
                    'current_price': current_price,
                    'current_value': current_value,
                    'cost_basis': cost_basis
                })

            except Exception as e:
                logger.warning(f"Error processing {coin_id}: {e}")
                continue

        if not holdings:
            return {"error": "No valid holdings found"}

        # Calculate metrics
        total_return = ((total_value - total_cost) / total_cost * 100) if total_cost > 0 else 0

        return {
            'total_value': total_value,
            'total_cost': total_cost,
            'total_return_pct': total_return,
            'holdings': holdings,
            'num_holdings': len(holdings)
        }

    except Exception as e:
        logger.error(f"Error calculating portfolio returns: {e}")
        return {"error": str(e)}


@mcp.tool()
def portfolio_tracker(portfolio: str):
    """
    Track portfolio performance. Input format: 'bitcoin:0.5,ethereum:2.1' (coin:amount pairs separated by commas)
    Or use detailed format: 'bitcoin:amount=0.5,cost_basis=30000;ethereum:amount=2.1,cost_basis=4000'
    """
    try:
        # Parse portfolio input
        portfolio_dict = {}

        if ';' in portfolio:
            # Detailed format: coin:amount=X,cost_basis=Y
            holdings = portfolio.split(';')
            for holding in holdings:
                if ':' in holding:
                    coin_part, params_part = holding.split(':', 1)
                    coin_id = coin_part.strip().lower()

                    params = {}
                    param_pairs = params_part.split(',')
                    for pair in param_pairs:
                        if '=' in pair:
                            key, value = pair.split('=', 1)
                            key = key.strip()
                            try:
                                params[key] = float(value.strip())
                            except ValueError:
                                params[key] = value.strip()

                    portfolio_dict[coin_id] = params
        else:
            # Simple format: coin:amount
            holdings = portfolio.split(',')
            for holding in holdings:
                if ':' in holding:
                    coin_id, amount_str = holding.split(':', 1)
                    coin_id = coin_id.strip().lower()
                    try:
                        amount = float(amount_str.strip())
                        portfolio_dict[coin_id] = amount
                    except ValueError:
                        continue

        if not portfolio_dict:
            return "Invalid portfolio format. Use: 'bitcoin:0.5,ethereum:2.1' or 'bitcoin:amount=0.5,cost_basis=30000;ethereum:amount=2.1,cost_basis=4000'"

        # Calculate portfolio performance
        portfolio_data = calculate_portfolio_returns(portfolio_dict)

        if 'error' in portfolio_data:
            return f"Error calculating portfolio: {portfolio_data['error']}"

        result = f"📊 Portfolio Analysis\n\n"
        result += f"💰 Total Value: ${portfolio_data['total_value']:.2f}\n"
        result += f"💵 Total Cost Basis: ${portfolio_data['total_cost']:.2f}\n"
        result += f"📈 Total Return: {portfolio_data['total_return_pct']:+.2f}%\n"
        result += f"🪙 Holdings: {portfolio_data['num_holdings']}\n\n"

        result += "Detailed Holdings:\n"
        for holding in portfolio_data['holdings']:
            pnl = ""
            if holding['cost_basis'] > 0:
                pnl_pct = (holding['current_value'] - holding['cost_basis']) / holding['cost_basis'] * 100
                pnl = f" | P&L: {pnl_pct:+.2f}%"

            result += f"• {holding['coin'].upper()}: {holding['amount']} @ ${holding['current_price']:.2f} = ${holding['current_value']:.2f}{pnl}\n"

        return result

    except Exception as e:
        logger.error(f"Error in portfolio_tracker: {e}")
        return f"Error tracking portfolio: {str(e)}"


@mcp.tool()
def risk_analysis(coin_ids: str, days: int = 30):
    """
    Analyze risk metrics for cryptocurrencies. Input format: 'bitcoin,ethereum,cardano' (comma-separated coin IDs)
    """
    try:
        coin_list = [coin.strip().lower() for coin in coin_ids.split(',') if coin.strip()]

        if not coin_list:
            return "No valid coin IDs provided. Use format: 'bitcoin,ethereum,cardano'"

        if len(coin_list) > 5:
            return "Maximum 5 coins allowed for risk analysis"

        result = f"📊 Risk Analysis ({days} days)\n\n"

        # Individual risk metrics
        for coin_id in coin_list:
            try:
                df = get_historical_prices(coin_id, days)
                if df.empty or len(df) < 10:
                    result += f"⚠️ {coin_id.upper()}: Insufficient data\n"
                    continue

                prices = df['price']
                returns = prices.pct_change().dropna()

                volatility = calculate_volatility(prices)
                sharpe = calculate_sharpe_ratio(returns)

                max_drawdown = 0
                peak = prices.iloc[0]
                for price in prices:
                    if price > peak:
                        peak = price
                    drawdown = (peak - price) / peak
                    max_drawdown = max(max_drawdown, drawdown)

                result += f"🪙 {coin_id.upper()}:\n"
                result += f"  • Volatility: {volatility:.2%}\n"
                result += f"  • Sharpe Ratio: {sharpe:.2f}\n"
                result += f"  • Max Drawdown: {max_drawdown:.2%}\n"
                result += f"  • Risk Level: {'High' if volatility > 0.8 else 'Medium' if volatility > 0.5 else 'Low'}\n\n"

            except Exception as e:
                logger.warning(f"Error analyzing {coin_id}: {e}")
                result += f"⚠️ {coin_id.upper()}: Error - {str(e)}\n\n"

        return result

    except Exception as e:
        logger.error(f"Error in risk_analysis: {e}")
        return f"Error performing risk analysis: {str(e)}"


@mcp.tool()
def correlation_analysis(coin_ids: str, days: int = 30):
    """
    Analyze correlations between cryptocurrencies. Input format: 'bitcoin,ethereum,cardano' (comma-separated coin IDs)
    """
    try:
        coin_list = [coin.strip().lower() for coin in coin_ids.split(',') if coin.strip()]

        if len(coin_list) < 2:
            return "Need at least 2 coins for correlation analysis. Use format: 'bitcoin,ethereum,cardano'"

        if len(coin_list) > 8:
            return "Maximum 8 coins allowed for correlation analysis"

        corr_matrix = calculate_correlation_matrix(coin_list, days)

        if corr_matrix.empty:
            return "Unable to calculate correlation matrix - check coin IDs and try again"

        result = f"📊 Correlation Analysis ({days} days)\n\n"

        # Correlation matrix
        result += "Correlation Matrix:\n"
        result += "```\n"
        result += f"{'':<12}" + "".join([f"{coin[:10]:<12}" for coin in coin_list]) + "\n"
        result += "-" * (12 + 12 * len(coin_list)) + "\n"

        for coin1 in coin_list:
            result += f"{coin1[:10]:<12}"
            for coin2 in coin_list:
                corr = corr_matrix.loc[coin1, coin2]
                result += f"{corr:>10.2f}  "
            result += "\n"
        result += "```\n\n"

        # Key insights
        result += "Key Insights:\n"

        # Find highest and lowest correlations
        correlations = []
        for i, coin1 in enumerate(coin_list):
            for j, coin2 in enumerate(coin_list):
                if i < j:
                    corr = corr_matrix.loc[coin1, coin2]
                    correlations.append((abs(corr), corr, coin1, coin2))

        correlations.sort(reverse=True)

        if correlations:
            # Most correlated pair
            _, corr_val, coin1, coin2 = correlations[0]
            strength = "Very Strong" if abs(corr_val) > 0.8 else "Strong" if abs(corr_val) > 0.6 else "Moderate"
            result += f"• Most Correlated: {coin1.upper()} & {coin2.upper()} ({corr_val:.2f} - {strength})\n"

            # Least correlated pair
            _, corr_val, coin1, coin2 = correlations[-1]
            strength = "Weak" if abs(corr_val) < 0.3 else "Moderate"
            result += f"• Least Correlated: {coin1.upper()} & {coin2.upper()} ({corr_val:.2f} - {strength})\n"

        # Diversification advice
        avg_corr = corr_matrix.values.mean()
        if avg_corr > 0.7:
            advice = "High correlation - Limited diversification benefits"
        elif avg_corr > 0.4:
            advice = "Moderate correlation - Some diversification benefits"
        else:
            advice = "Low correlation - Good diversification potential"

        result += f"• Portfolio Diversification: {advice} (Avg correlation: {avg_corr:.2f})\n"

        return result

    except Exception as e:
        logger.error(f"Error in correlation_analysis: {e}")
        return f"Error performing correlation analysis: {str(e)}"

# Database functions
def init_database():
    """Initialize SQLite database for storing crypto data."""
    conn = sqlite3.connect('crypto_data.db')
    cursor = conn.cursor()

    # Create price history table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS price_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            coin_id TEXT NOT NULL,
            price REAL NOT NULL,
            volume REAL,
            market_cap REAL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            source TEXT NOT NULL
        )
    ''')

    # Create portfolio table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS portfolio (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            coin_id TEXT NOT NULL,
            amount REAL NOT NULL,
            purchase_price REAL NOT NULL,
            purchase_date DATETIME DEFAULT CURRENT_TIMESTAMP,
            notes TEXT
        )
    ''')

    conn.commit()
    conn.close()

def save_price_to_db(coin_id: str, price: float, volume: float = None, market_cap: float = None, source: str = "unknown"):
    """Save price data to database."""
    try:
        init_database()
        conn = sqlite3.connect('crypto_data.db')
        cursor = conn.cursor()

        cursor.execute('''
            INSERT INTO price_history (coin_id, price, volume, market_cap, source)
            VALUES (?, ?, ?, ?, ?)
        ''', (coin_id, price, volume, market_cap, source))

        conn.commit()
        conn.close()
        return True
    except Exception as e:
        logger.error(f"Error saving price to database: {e}")
        return False

def get_price_history_from_db(coin_id: str, days: int = 30) -> pd.DataFrame:
    """Get price history from database."""
    try:
        init_database()
        conn = sqlite3.connect('crypto_data.db')
        cursor = conn.cursor()

        # Calculate date threshold
        from datetime import datetime, timedelta
        threshold_date = datetime.now() - timedelta(days=days)

        cursor.execute('''
            SELECT price, volume, market_cap, timestamp, source
            FROM price_history
            WHERE coin_id = ? AND timestamp >= ?
            ORDER BY timestamp ASC
        ''', (coin_id, threshold_date.strftime('%Y-%m-%d %H:%M:%S')))

        rows = cursor.fetchall()
        conn.close()

        if not rows:
            return pd.DataFrame()

        df = pd.DataFrame(rows, columns=['price', 'volume', 'market_cap', 'timestamp', 'source'])
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df.set_index('timestamp', inplace=True)

        return df

    except Exception as e:
        logger.error(f"Error getting price history from database: {e}")
        return pd.DataFrame()

@mcp.tool()
def save_portfolio_to_db(coin_id: str, amount: float, purchase_price: float, notes: str = ""):
    """Save portfolio entry to database. Use coin IDs like 'bitcoin', 'ethereum'."""
    try:
        init_database()
        conn = sqlite3.connect('crypto_data.db')
        cursor = conn.cursor()

        cursor.execute('''
            INSERT INTO portfolio (coin_id, amount, purchase_price, notes)
            VALUES (?, ?, ?, ?)
        ''', (coin_id, amount, purchase_price, notes))

        conn.commit()
        conn.close()

        return f"Portfolio entry saved: {amount} {coin_id} at ${purchase_price}"

    except Exception as e:
        logger.error(f"Error saving portfolio to database: {e}")
        return f"Error saving portfolio entry: {str(e)}"

@mcp.tool()
def get_portfolio_from_db():
    """Get all portfolio entries from database."""
    try:
        init_database()
        conn = sqlite3.connect('crypto_data.db')
        cursor = conn.cursor()

        cursor.execute('SELECT * FROM portfolio ORDER BY purchase_date DESC')
        rows = cursor.fetchall()
        conn.close()

        if not rows:
            return "No portfolio entries found."

        result = "Portfolio Entries:\n"
        for row in rows:
            result += f"- {row[2]} {row[1]} purchased at ${row[3]} on {row[4]}"
            if row[5]:
                result += f" (Notes: {row[5]})"
            result += "\n"

        return result

    except Exception as e:
        logger.error(f"Error getting portfolio from database: {e}")
        return f"Error retrieving portfolio: {str(e)}"

@mcp.tool()
def get_stored_price_history(coin_id: str, days: int = 30):
    """Get stored price history from database for analysis."""
    try:
        df = get_price_history_from_db(coin_id, days)

        if df.empty:
            return f"No stored price history found for {coin_id} in the last {days} days."

        result = f"Price History for {coin_id} (last {days} days):\n"
        result += f"Records: {len(df)}\n"
        result += f"Average Price: ${df['price'].mean():.2f}\n"
        result += f"Min Price: ${df['price'].min():.2f}\n"
        result += f"Max Price: ${df['price'].max():.2f}\n"
        result += f"Latest Price: ${df['price'].iloc[-1]:.2f}\n"

        return result

    except Exception as e:
        logger.error(f"Error getting stored price history: {e}")
        return f"Error retrieving price history: {str(e)}"

@mcp.tool()
def create_price_chart(coin_id: str, days: int = 30):
    """Create a price chart for the specified cryptocurrency."""
    try:
        # Get historical data
        df = get_historical_prices(coin_id, days)

        if df.empty:
            return f"No historical data available for {coin_id}"

        # Create the plot
        plt.figure(figsize=(12, 6))
        plt.plot(df.index, df['price'], label=f'{coin_id.upper()} Price', color='blue', linewidth=2)

        # Add moving averages
        if len(df) > 20:
            ma20 = df['price'].rolling(window=20).mean()
            plt.plot(df.index, ma20, label='20-day MA', color='orange', linestyle='--')

        if len(df) > 50:
            ma50 = df['price'].rolling(window=50).mean()
            plt.plot(df.index, ma50, label='50-day MA', color='red', linestyle='--')

        plt.title(f'{coin_id.upper()} Price Chart (Last {days} Days)')
        plt.xlabel('Date')
        plt.ylabel('Price (USD)')
        plt.legend()
        plt.grid(True, alpha=0.3)
        plt.xticks(rotation=45)

        # Save plot to base64 string
        buffer = io.BytesIO()
        plt.savefig(buffer, format='png', dpi=100, bbox_inches='tight')
        buffer.seek(0)
        image_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
        plt.close()

        return f"Price chart created for {coin_id}. Chart data: data:image/png;base64,{image_base64}"

    except Exception as e:
        logger.error(f"Error creating price chart: {e}")
        return f"Error creating price chart: {str(e)}"

@mcp.tool()
def create_technical_analysis_chart(coin_id: str, days: int = 30):
    """Create a technical analysis chart with RSI and MACD indicators."""
    try:
        # Get historical data
        df = get_historical_prices(coin_id, days)

        if df.empty or len(df) < 26:
            return f"Insufficient historical data for {coin_id} technical analysis"

        prices = df['price']

        # Calculate indicators
        rsi = calculate_rsi(prices)
        macd_data = calculate_macd(prices)
        macd_line = macd_data['macd']
        signal_line = macd_data['signal']
        histogram = macd_data['histogram']

        # Create subplots
        fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(14, 10), gridspec_kw={'height_ratios': [3, 1, 1]})

        # Price chart
        ax1.plot(df.index, prices, label='Price', color='blue', linewidth=1.5)
        ax1.set_title(f'{coin_id.upper()} Technical Analysis (Last {days} Days)')
        ax1.set_ylabel('Price (USD)')
        ax1.legend()
        ax1.grid(True, alpha=0.3)

        # RSI chart
        ax2.plot(df.index, rsi, label='RSI', color='purple', linewidth=1.5)
        ax2.axhline(y=70, color='red', linestyle='--', alpha=0.7, label='Overbought (70)')
        ax2.axhline(y=30, color='green', linestyle='--', alpha=0.7, label='Oversold (30)')
        ax2.set_ylabel('RSI')
        ax2.set_ylim(0, 100)
        ax2.legend()
        ax2.grid(True, alpha=0.3)

        # MACD chart
        ax3.plot(df.index, macd_line, label='MACD', color='blue', linewidth=1.5)
        ax3.plot(df.index, signal_line, label='Signal', color='red', linewidth=1.5)
        ax3.bar(df.index, histogram, label='Histogram', color='gray', alpha=0.7)
        ax3.set_ylabel('MACD')
        ax3.legend()
        ax3.grid(True, alpha=0.3)

        plt.xticks(rotation=45)
        plt.tight_layout()

        # Save plot to base64 string
        buffer = io.BytesIO()
        plt.savefig(buffer, format='png', dpi=100, bbox_inches='tight')
        buffer.seek(0)
        image_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
        plt.close()

        return f"Technical analysis chart created for {coin_id}. Chart data: data:image/png;base64,{image_base64}"

    except Exception as e:
        logger.error(f"Error creating technical analysis chart: {e}")
        return f"Error creating technical analysis chart: {str(e)}"

@mcp.tool()
def start_price_monitoring(coin_id: str, interval_seconds: int = 60, duration_minutes: int = 5):
    """Monitor cryptocurrency price in real-time for a specified duration."""
    try:
        import time

        end_time = time.time() + (duration_minutes * 60)
        prices = []

        print(f"Starting price monitoring for {coin_id}...")

        while time.time() < end_time:
            try:
                # Get current price
                price_data = get_crypto_price_with_fallback(coin_id)

                # Extract numeric price from response
                import re
                price_match = re.search(r'\$([0-9,]+\.?[0-9]*)', price_data)
                if price_match:
                    price = float(price_match.group(1).replace(',', ''))
                    timestamp = datetime.now().strftime('%H:%M:%S')
                    prices.append((timestamp, price))
                    print(f"[{timestamp}] {coin_id}: ${price}")

                    # Save to database
                    save_price_to_db(coin_id, price, source="realtime_monitor")

                time.sleep(interval_seconds)

            except KeyboardInterrupt:
                break
            except Exception as e:
                print(f"Error during monitoring: {e}")
                time.sleep(interval_seconds)

        # Summary
        if prices:
            prices_only = [p[1] for p in prices]
            result = f"Monitoring completed for {coin_id}:\n"
            result += f"Duration: {duration_minutes} minutes\n"
            result += f"Readings: {len(prices)}\n"
            result += f"Start Price: ${prices[0][1]:.2f}\n"
            result += f"End Price: ${prices[-1][1]:.2f}\n"
            result += f"Min Price: ${min(prices_only):.2f}\n"
            result += f"Max Price: ${max(prices_only):.2f}\n"
            result += f"Price Change: ${prices[-1][1] - prices[0][1]:.2f} ({((prices[-1][1] - prices[0][1]) / prices[0][1] * 100):.2f}%)"

            return result
        else:
            return f"No price data collected for {coin_id}"

    except Exception as e:
        logger.error(f"Error in price monitoring: {e}")
        return f"Error monitoring price: {str(e)}"

# CLI Interface functions
console = Console()

def display_price_table(coin_data: dict):
    """Display cryptocurrency prices in a rich table format."""
    table = Table(title="📊 Cryptocurrency Prices")
    table.add_column("Coin", style="cyan", no_wrap=True)
    table.add_column("Price (USD)", style="green", justify="right")
    table.add_column("Source", style="yellow")
    table.add_column("Time", style="magenta")

    for coin, data in coin_data.items():
        if isinstance(data, str):
            # Parse price from string response
            import re
            price_match = re.search(r'\$([0-9,]+\.?[0-9]*)', data)
            if price_match:
                price = f"${price_match.group(1)}"
                source_match = re.search(r'\(([^)]+)\)', data)
                source = source_match.group(1) if source_match else "Unknown"
                table.add_row(coin.upper(), price, source, datetime.now().strftime("%H:%M:%S"))
        else:
            table.add_row(coin.upper(), f"${data.get('price', 'N/A')}", data.get('source', 'Unknown'), datetime.now().strftime("%H:%M:%S"))

    console.print(table)

def display_portfolio_table():
    """Display portfolio in a rich table format."""
    try:
        init_database()
        conn = sqlite3.connect('crypto_data.db')
        cursor = conn.cursor()

        cursor.execute('SELECT * FROM portfolio ORDER BY purchase_date DESC')
        rows = cursor.fetchall()
        conn.close()

        if not rows:
            console.print("[yellow]No portfolio entries found.[/yellow]")
            return

        table = Table(title="💼 Portfolio Summary")
        table.add_column("Coin", style="cyan", no_wrap=True)
        table.add_column("Amount", style="green", justify="right")
        table.add_column("Purchase Price", style="yellow", justify="right")
        table.add_column("Current Value", style="blue", justify="right")
        table.add_column("P&L", style="red", justify="right")
        table.add_column("Date", style="magenta")

        total_value = 0
        total_pnl = 0

        for row in rows:
            coin_id, amount, purchase_price, purchase_date = row[1], row[2], row[3], row[4]

            # Get current price
            try:
                current_price_data = get_crypto_price_with_fallback(coin_id)
                import re
                price_match = re.search(r'\$([0-9,]+\.?[0-9]*)', current_price_data)
                current_price = float(price_match.group(1).replace(',', '')) if price_match else purchase_price
            except:
                current_price = purchase_price

            current_value = amount * current_price
            pnl = current_value - (amount * purchase_price)
            pnl_percent = (pnl / (amount * purchase_price)) * 100

            total_value += current_value
            total_pnl += pnl

            pnl_color = "green" if pnl >= 0 else "red"
            table.add_row(
                coin_id.upper(),
                f"{amount:.4f}",
                f"${purchase_price:.2f}",
                f"${current_value:.2f}",
                f"{'+' if pnl >= 0 else ''}${pnl:.2f} ({'+' if pnl >= 0 else ''}{pnl_percent:.1f}%)",
                purchase_date.split()[0]
            )

        console.print(table)

        # Summary panel
        summary = Panel.fit(
            f"[bold green]Total Value: ${total_value:.2f}[/bold green]\n"
            f"[bold {'green' if total_pnl >= 0 else 'red'}]Total P&L: {'+' if total_pnl >= 0 else ''}${total_pnl:.2f}[/bold {'green' if total_pnl >= 0 else 'red'}]",
            title="📈 Portfolio Summary"
        )
        console.print(summary)

    except Exception as e:
        console.print(f"[red]Error displaying portfolio: {e}[/red]")

def display_market_overview():
    """Display market overview with top coins."""
    try:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("Fetching market data...", total=None)

            # Get market analysis
            market_data = market_analysis()

            progress.update(task, completed=True)

        console.print(Panel.fit(market_data, title="🌍 Market Overview"))

    except Exception as e:
        console.print(f"[red]Error fetching market overview: {e}[/red]")

def cli_price_command(args):
    """Handle price command in CLI."""
    coins = args.coins if args.coins else ["bitcoin"]

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task(f"Fetching prices for {', '.join(coins)}...", total=len(coins))

        price_data = {}
        for coin in coins:
            try:
                price = get_crypto_price_with_fallback(coin)
                price_data[coin] = price
            except Exception as e:
                price_data[coin] = f"Error: {e}"
            progress.advance(task)

    display_price_table(price_data)

def cli_portfolio_command(args):
    """Handle portfolio command in CLI."""
    if args.add:
        coin, amount, price = args.add
        try:
            result = save_portfolio_to_db(coin, float(amount), float(price))
            console.print(f"[green]✓ {result}[/green]")
        except Exception as e:
            console.print(f"[red]Error adding to portfolio: {e}[/red]")
    else:
        display_portfolio_table()

def cli_market_command(args):
    """Handle market command in CLI."""
    display_market_overview()

def cli_monitor_command(args):
    """Handle monitor command in CLI."""
    coin = args.coin
    interval = args.interval
    duration = args.duration

    console.print(f"[yellow]Starting price monitoring for {coin}...[/yellow]")
    console.print(f"[dim]Interval: {interval}s, Duration: {duration}min[/dim]")

    try:
        result = start_price_monitoring(coin, interval, duration)
        console.print(Panel.fit(result, title=f"📊 Monitoring Results for {coin.upper()}"))
    except Exception as e:
        console.print(f"[red]Error during monitoring: {e}[/red]")

def cli_alert_command(args):
    """Handle alert command in CLI."""
    if args.create:
        coin, price, condition = args.create
        try:
            alert = {
                'id': len(alerts) + 1,
                'coin_id': coin,
                'target_price': float(price),
                'condition': condition,
                'alert_type': 'price',
                'created_at': datetime.now(),
                'active': True
            }
            alerts.append(alert)
            console.print(f"[green]✓ Alert created: {coin.upper()} {condition} ${price}[/green]")
        except Exception as e:
            console.print(f"[red]Error creating alert: {e}[/red]")
    elif args.list:
        active_alerts = [alert for alert in alerts if alert['active']]
        if not active_alerts:
            console.print("[yellow]No active alerts.[/yellow]")
        else:
            table = Table(title="📊 Active Alerts")
            table.add_column("ID", style="cyan", justify="right")
            table.add_column("Coin", style="yellow")
            table.add_column("Condition", style="green")
            table.add_column("Target Price", style="red", justify="right")
            table.add_column("Created", style="magenta")

            for alert in active_alerts:
                table.add_row(
                    str(alert['id']),
                    alert['coin_id'].upper(),
                    alert['condition'],
                    f"${alert['target_price']}",
                    alert['created_at'].strftime('%Y-%m-%d %H:%M')
                )
            console.print(table)
    elif args.check:
        triggered = []
        for alert in alerts:
            if not alert['active']:
                continue

            try:
                price_data = get_crypto_price_with_fallback(alert['coin_id'])
                import re
                price_match = re.search(r'\$([0-9,]+\.?[0-9]*)', price_data)
                if price_match:
                    current_price = float(price_match.group(1).replace(',', ''))

                    triggered_condition = False
                    if alert['condition'] == 'above' and current_price >= alert['target_price']:
                        triggered_condition = True
                    elif alert['condition'] == 'below' and current_price <= alert['target_price']:
                        triggered_condition = True

                    if triggered_condition:
                        alert['triggered_at'] = datetime.now()
                        alert['trigger_price'] = current_price
                        alert['active'] = False
                        triggered.append(alert)

            except Exception as e:
                console.print(f"[red]Error checking alert for {alert['coin_id']}: {e}[/red]")

        if not triggered:
            console.print("[green]No alerts triggered. All active alerts are still monitoring.[/green]")
        else:
            table = Table(title="🚨 Triggered Alerts")
            table.add_column("Coin", style="cyan")
            table.add_column("Condition", style="yellow")
            table.add_column("Target", style="red", justify="right")
            table.add_column("Current", style="green", justify="right")
            table.add_column("Triggered", style="magenta")

            for alert in triggered:
                table.add_row(
                    alert['coin_id'].upper(),
                    alert['condition'],
                    f"${alert['target_price']}",
                    f"${alert['trigger_price']:.2f}",
                    alert['triggered_at'].strftime('%H:%M:%S')
                )
            console.print(table)

def create_cli_parser():
    """Create command line argument parser."""
    parser = argparse.ArgumentParser(
        description="Crypto_MCP - Cryptocurrency Analysis Tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python crypto_mcp.py price bitcoin ethereum
  python crypto_mcp.py portfolio --add bitcoin 1.5 45000
  python crypto_mcp.py market
  python crypto_mcp.py monitor bitcoin --interval 30 --duration 2
  python crypto_mcp.py alert --create bitcoin 50000 above
  python crypto_mcp.py alert --list
  python crypto_mcp.py alert --check
        """
    )

    subparsers = parser.add_subparsers(dest='command', help='Available commands')

    # Price command
    price_parser = subparsers.add_parser('price', help='Get cryptocurrency prices')
    price_parser.add_argument('coins', nargs='*', help='Coin names (default: bitcoin)')
    price_parser.set_defaults(func=cli_price_command)

    # Portfolio command
    portfolio_parser = subparsers.add_parser('portfolio', help='Manage portfolio')
    portfolio_parser.add_argument('--add', nargs=3, metavar=('COIN', 'AMOUNT', 'PRICE'),
                                 help='Add to portfolio: COIN AMOUNT PRICE')
    portfolio_parser.set_defaults(func=cli_portfolio_command)

    # Market command
    market_parser = subparsers.add_parser('market', help='Show market overview')
    market_parser.set_defaults(func=cli_market_command)

    # Monitor command
    monitor_parser = subparsers.add_parser('monitor', help='Monitor price in real-time')
    monitor_parser.add_argument('coin', help='Coin to monitor')
    monitor_parser.add_argument('--interval', type=int, default=60,
                               help='Monitoring interval in seconds (default: 60)')
    monitor_parser.add_argument('--duration', type=int, default=5,
                               help='Monitoring duration in minutes (default: 5)')
    monitor_parser.set_defaults(func=cli_monitor_command)

    # Alert command
    alert_parser = subparsers.add_parser('alert', help='Manage price alerts')
    alert_group = alert_parser.add_mutually_exclusive_group(required=True)
    alert_group.add_argument('--create', nargs=3, metavar=('COIN', 'PRICE', 'CONDITION'),
                            help='Create alert: COIN PRICE CONDITION (above/below)')
    alert_group.add_argument('--list', action='store_true', help='List active alerts')
    alert_group.add_argument('--check', action='store_true', help='Check for triggered alerts')
    alert_parser.set_defaults(func=cli_alert_command)

    return parser

def main():
    """Main CLI entry point."""
    parser = create_cli_parser()
    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    # Initialize database
    init_database()

    # Execute command
    try:
        args.func(args)
    except KeyboardInterrupt:
        console.print("\n[yellow]Operation cancelled by user.[/yellow]")
    except Exception as e:
        console.print(f"[red]Unexpected error: {e}[/red]")

if __name__ == "__main__":
    main()

# REST API functions
app = Flask(__name__)
CORS(app)  # Enable CORS for web dashboard

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'version': '2.0.0'
    })

@app.route('/api/prices/<coin>', methods=['GET'])
def get_price_api(coin):
    """Get price for a specific coin via REST API."""
    try:
        price_data = get_crypto_price_with_fallback(coin)

        # Parse price from response
        import re
        price_match = re.search(r'\$([0-9,]+\.?[0-9]*)', price_data)
        if price_match:
            price = float(price_match.group(1).replace(',', ''))
            return jsonify({
                'coin': coin,
                'price': price,
                'currency': 'USD',
                'timestamp': datetime.now().isoformat(),
                'source': 'multiple_apis'
            })
        else:
            return jsonify({'error': 'Price not found'}), 404

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/prices', methods=['GET'])
def get_multiple_prices_api():
    """Get prices for multiple coins."""
    coins = request.args.get('coins', 'bitcoin').split(',')

    results = {}
    for coin in coins:
        coin = coin.strip()
        try:
            price_data = get_crypto_price_with_fallback(coin)
            import re
            price_match = re.search(r'\$([0-9,]+\.?[0-9]*)', price_data)
            if price_match:
                price = float(price_match.group(1).replace(',', ''))
                results[coin] = {
                    'price': price,
                    'currency': 'USD',
                    'timestamp': datetime.now().isoformat()
                }
            else:
                results[coin] = {'error': 'Price not found'}
        except Exception as e:
            results[coin] = {'error': str(e)}

    return jsonify(results)

@app.route('/api/market', methods=['GET'])
def get_market_api():
    """Get market overview."""
    try:
        market_data = market_analysis()
        return jsonify({
            'market_overview': market_data,
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/portfolio', methods=['GET'])
def get_portfolio_api():
    """Get portfolio data."""
    try:
        init_database()
        conn = sqlite3.connect('crypto_data.db')
        cursor = conn.cursor()

        cursor.execute('SELECT * FROM portfolio ORDER BY purchase_date DESC')
        rows = cursor.fetchall()
        conn.close()

        portfolio = []
        for row in rows:
            portfolio.append({
                'id': row[0],
                'coin_id': row[1],
                'amount': row[2],
                'purchase_price': row[3],
                'purchase_date': row[4],
                'notes': row[5]
            })

        return jsonify({
            'portfolio': portfolio,
            'timestamp': datetime.now().isoformat()
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/portfolio', methods=['POST'])
def add_portfolio_api():
    """Add entry to portfolio."""
    try:
        data = request.get_json()

        if not data or not all(k in data for k in ['coin_id', 'amount', 'purchase_price']):
            return jsonify({'error': 'Missing required fields: coin_id, amount, purchase_price'}), 400

        result = save_portfolio_to_db(
            data['coin_id'],
            float(data['amount']),
            float(data['purchase_price']),
            data.get('notes', '')
        )

        return jsonify({
            'message': result,
            'timestamp': datetime.now().isoformat()
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/technical/<coin>', methods=['GET'])
def get_technical_api(coin):
    """Get technical analysis for a coin."""
    try:
        days = int(request.args.get('days', 30))

        # Get historical data
        df = get_historical_prices(coin, days)

        if df.empty:
            return jsonify({'error': 'No historical data available'}), 404

        # Calculate indicators
        prices = df['price']
        rsi = calculate_rsi(prices)
        macd_data = calculate_macd(prices)
        bollinger = calculate_bollinger_bands(prices)

        # Prepare response
        technical_data = {
            'coin': coin,
            'period_days': days,
            'indicators': {
                'rsi': {
                    'current': rsi.iloc[-1] if not rsi.empty else None,
                    'signal': 'oversold' if rsi.iloc[-1] < 30 else 'overbought' if rsi.iloc[-1] > 70 else 'neutral'
                },
                'macd': {
                    'macd_line': macd_data['macd'].iloc[-1] if not macd_data['macd'].empty else None,
                    'signal_line': macd_data['signal'].iloc[-1] if not macd_data['signal'].empty else None,
                    'histogram': macd_data['histogram'].iloc[-1] if not macd_data['histogram'].empty else None,
                    'signal': 'bullish' if macd_data['macd'].iloc[-1] > macd_data['signal'].iloc[-1] else 'bearish'
                },
                'bollinger_bands': {
                    'upper': bollinger['upper'].iloc[-1] if not bollinger['upper'].empty else None,
                    'middle': bollinger['middle'].iloc[-1] if not bollinger['middle'].empty else None,
                    'lower': bollinger['lower'].iloc[-1] if not bollinger['lower'].empty else None,
                    'current_price': prices.iloc[-1],
                    'position': 'above_upper' if prices.iloc[-1] > bollinger['upper'].iloc[-1] else 'below_lower' if prices.iloc[-1] < bollinger['lower'].iloc[-1] else 'within_bands'
                }
            },
            'timestamp': datetime.now().isoformat()
        }

        return jsonify(technical_data)

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/chart/<coin>', methods=['GET'])
def get_chart_api(coin):
    """Generate and return price chart as image."""
    try:
        days = int(request.args.get('days', 30))
        chart_type = request.args.get('type', 'price')  # price or technical

        if chart_type == 'technical':
            result = create_technical_analysis_chart(coin, days)
        else:
            result = create_price_chart(coin, days)

        # Extract base64 data from result
        import re
        base64_match = re.search(r'data:image/png;base64,([A-Za-z0-9+/=]+)', result)
        if base64_match:
            image_data = base64_match.group(1)
            # Return as file
            image_bytes = base64.b64decode(image_data)
            return send_file(
                io.BytesIO(image_bytes),
                mimetype='image/png',
                as_attachment=True,
                download_name=f'{coin}_{chart_type}_chart.png'
            )
        else:
            return jsonify({'error': 'Chart generation failed'}), 500

    except Exception as e:
        return jsonify({'error': str(e)}), 500

def start_api_server(host='0.0.0.0', port=5000):
    """Start the REST API server in a separate thread."""
    def run_server():
        console.print(f"[green]Starting REST API server on http://{host}:{port}[/green]")
        app.run(host=host, port=port, debug=False)

    api_thread = threading.Thread(target=run_server, daemon=True)
    api_thread.start()
    return api_thread

# MCP tool for starting API server
@mcp.tool()
def start_rest_api(host: str = "0.0.0.0", port: int = 5000):
    """Start the REST API server for web dashboard integration."""
    try:
        global api_thread
        api_thread = start_api_server(host, port)
        return f"REST API server started on http://{host}:{port}"
    except Exception as e:
        logger.error(f"Error starting API server: {e}")
        return f"Error starting API server: {str(e)}"

# Alert/Notification system
alerts = []

def add_price_alert(coin_id: str, target_price: float, condition: str = "above", alert_type: str = "price"):
    """Add a price alert."""
    alert = {
        'id': len(alerts) + 1,
        'coin_id': coin_id,
        'target_price': target_price,
        'condition': condition,  # 'above', 'below', 'change_percent'
        'alert_type': alert_type,
        'created_at': datetime.now(),
        'active': True
    }
    alerts.append(alert)
    return alert

def check_alerts():
    """Check all active alerts and return triggered ones."""
    triggered_alerts = []

    for alert in alerts:
        if not alert['active']:
            continue

        try:
            # Get current price
            price_data = get_crypto_price_with_fallback(alert['coin_id'])
            import re
            price_match = re.search(r'\$([0-9,]+\.?[0-9]*)', price_data)
            if price_match:
                current_price = float(price_match.group(1).replace(',', ''))

                triggered = False
                if alert['condition'] == 'above' and current_price >= alert['target_price']:
                    triggered = True
                elif alert['condition'] == 'below' and current_price <= alert['target_price']:
                    triggered = True

                if triggered:
                    alert['triggered_at'] = datetime.now()
                    alert['trigger_price'] = current_price
                    alert['active'] = False
                    triggered_alerts.append(alert)

        except Exception as e:
            logger.error(f"Error checking alert for {alert['coin_id']}: {e}")

    return triggered_alerts

@mcp.tool()
def create_price_alert(coin_id: str, target_price: float, condition: str = "above"):
    """Create a price alert for a cryptocurrency. Conditions: 'above' or 'below'."""
    try:
        alert = add_price_alert(coin_id, target_price, condition)
        return f"Price alert created: {coin_id.upper()} {condition} ${target_price}"
    except Exception as e:
        logger.error(f"Error creating price alert: {e}")
        return f"Error creating price alert: {str(e)}"

@mcp.tool()
def check_active_alerts():
    """Check and return any triggered price alerts."""
    try:
        triggered = check_alerts()

        if not triggered:
            return "No alerts triggered. All active alerts are still monitoring."

        result = "🚨 TRIGGERED ALERTS:\n"
        for alert in triggered:
            result += f"• {alert['coin_id'].upper()} {alert['condition']} ${alert['target_price']} - "
            result += f"Current: ${alert['trigger_price']:.2f} (Triggered at {alert['triggered_at'].strftime('%H:%M:%S')})\n"

        return result

    except Exception as e:
        logger.error(f"Error checking alerts: {e}")
        return f"Error checking alerts: {str(e)}"

@mcp.tool()
def list_active_alerts():
    """List all active price alerts."""
    try:
        active_alerts = [alert for alert in alerts if alert['active']]

        if not active_alerts:
            return "No active alerts."

        result = "📊 ACTIVE ALERTS:\n"
        for alert in active_alerts:
            result += f"• Alert #{alert['id']}: {alert['coin_id'].upper()} {alert['condition']} ${alert['target_price']}\n"
            result += f"  Created: {alert['created_at'].strftime('%Y-%m-%d %H:%M:%S')}\n"

        return result

    except Exception as e:
        logger.error(f"Error listing alerts: {e}")
        return f"Error listing alerts: {str(e)}"

# Background alert checker
def start_alert_monitor(interval_seconds: int = 60):
    """Start background alert monitoring."""
    def monitor_alerts():
        console.print(f"[yellow]Starting alert monitor (check every {interval_seconds}s)...[/yellow]")
        while True:
            try:
                triggered = check_alerts()
                if triggered:
                    for alert in triggered:
                        console.print(f"[red]🚨 ALERT TRIGGERED: {alert['coin_id'].upper()} {alert['condition']} ${alert['target_price']} - Current: ${alert['trigger_price']:.2f}[/red]")
                time.sleep(interval_seconds)
            except KeyboardInterrupt:
                break
            except Exception as e:
                logger.error(f"Error in alert monitor: {e}")
                time.sleep(interval_seconds)

    monitor_thread = threading.Thread(target=monitor_alerts, daemon=True)
    monitor_thread.start()
    return monitor_thread


if __name__ == "__main__":
    main()