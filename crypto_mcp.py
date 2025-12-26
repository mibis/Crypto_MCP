from fastmcp import FastMCP
import requests

mcp = FastMCP("Crypto_MCP")

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
        "get_latest_news": "Get basic news placeholder"
    }
    result = "Available Crypto_MCP Tools:\n"
    for name, desc in tools.items():
        result += f"- {name}: {desc}\n"
    return result

@mcp.tool()
def get_crypto_price(coin_name: str = "bitcoin"):
    """Gets the current price of a specific cryptocurrency in USD from CoinGecko."""
    url = f"https://api.coingecko.com/api/v3/simple/price?ids={coin_name}&vs_currencies=usd"
    response = requests.get(url).json()
    return f"{coin_name.capitalize()} price: ${response[coin_name]['usd']}"

@mcp.tool()
def get_price_binance(symbol: str = "BTCUSDT"):
    """Gets real-time cryptocurrency price from Binance exchange. Use symbols like BTCUSDT, ETHUSDT."""
    url = f"https://api.binance.com/api/v3/ticker/price?symbol={symbol}"
    response = requests.get(url).json()
    return f"{symbol} price (Binance): ${response['price']}"

@mcp.tool()
def get_price_kraken(pair: str = "XBTUSD"):
    """Gets cryptocurrency price from Kraken exchange. Use pairs like XBTUSD (BTC), ETHUSD."""
    url = f"https://api.kraken.com/0/public/Ticker?pair={pair}"
    response = requests.get(url).json()
    price = response['result'][pair]['c'][0]
    return f"{pair} price (Kraken): ${price}"

@mcp.tool()
def get_price_coinpaprika(coin_id: str = "btc-bitcoin"):
    """Gets detailed cryptocurrency information from CoinPaprika. Use coin IDs like btc-bitcoin, eth-ethereum."""
    url = f"https://api.coinpaprika.com/v1/tickers/{coin_id}"
    response = requests.get(url).json()
    price = response['quotes']['USD']['price']
    return f"{coin_id} price (CoinPaprika): ${price}"

@mcp.tool()
def get_price_coinstats(coin: str = "bitcoin"):
    """Gets cryptocurrency price from CoinStats. Use coin names like bitcoin, ethereum."""
    url = f"https://api.coinstats.app/public/v1/coins/{coin}"
    response = requests.get(url).json()
    price = response['coin']['price']
    return f"{coin} price (CoinStats): ${price}"

@mcp.tool()
def get_latest_news():
    """Gets basic cryptocurrency news headlines. Note: This is a placeholder - use get_crypto_news_cryptocompare for real news."""
    # CryptoPanic veya benzeri bir API entegrasyonu buraya gelecek
    return "News: Bitcoin reached 100k dollar barrier!"

@mcp.tool()
def get_crypto_news_cryptocompare():
    """Gets the latest cryptocurrency news from CryptoCompare API, including Bitcoin, Ethereum, and general crypto news."""
    url = "https://min-api.cryptocompare.com/data/v2/news/?lang=EN&categories=Bitcoin,Ethereum,Cryptocurrency"
    response = requests.get(url).json()
    news = response['Data'][:5]  # İlk 5 haber
    result = "Latest crypto news (CryptoCompare):\n"
    for item in news:
        result += f"- {item['title']}\n"
    return result

@mcp.tool()
def market_analysis():
    """Returns a summary table of the top 10 cryptocurrencies by market cap, including current price and 24h change percentage."""
    url = "https://api.coingecko.com/api/v3/coins/markets?vs_currency=usd&order=market_cap_desc&per_page=10&page=1"
    response = requests.get(url).json()
    result = "Top 10 cryptocurrencies (CoinGecko):\n"
    for coin in response:
        result += f"{coin['name']} ({coin['symbol'].upper()}): ${coin['current_price']} | 24h: {coin['price_change_percentage_24h']:.2f}%\n"
    return result

if __name__ == "__main__":
    mcp.run()