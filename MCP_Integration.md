# MCP Server Entegrasyonu Rehberi

Bu rehber, Crypto_MCP server'ının Claude Desktop ve LM Studio ile entegrasyonu için adım adım talimatları içerir.

## Gereksinimler

- Python 3.10+
- Claude Desktop (MCP desteği ile)
- LM Studio (MCP desteği ile)
- Proje bağımlılıkları yüklü (`pip install -r requirements.txt`)

## Claude Desktop Entegrasyonu

### Adım 1: Config Dosyasını Hazırlayın
Claude Desktop'ın config.json dosyasını bulun (genellikle `~/Library/Application Support/Claude/claude_desktop_config.json`).

### Adım 2: Crypto_MCP'yi Ekleyin
`claude_desktop_config.json` dosyasına aşağıdaki gibi ekleyin:

```json
{
  "mcpServers": {
    "crypto-mcp": {
      "command": "C:\\VS_WorkSpace\\Crypto_MCP\\start_crypto_mcp.bat",
      "args": [],
      "env": {}
    }
  }
}
```

**Not:** `start_crypto_mcp.bat` dosyası sanal ortamı otomatik olarak etkinleştirir ve server'ı başlatır.

### Adım 3: Claude Desktop'ı Yeniden Başlatın
Değişikliklerin etkili olması için Claude Desktop'ı yeniden başlatın.

## LM Studio Entegrasyonu

### Adım 1: Config Dosyasını Hazırlayın
LM Studio'nun MCP config dosyasını bulun veya oluşturun.

### Adım 2: Crypto_MCP'yi Ekleyin
Config dosyasına aşağıdaki gibi ekleyin:

```json
{
  "mcpServers": {
    "crypto-mcp": {
      "command": "C:\\VS_WorkSpace\\Crypto_MCP\\start_crypto_mcp.bat",
      "args": [],
      "env": {}
    }
  }
}
```

**Not:** `start_crypto_mcp.bat` dosyası sanal ortamı otomatik olarak etkinleştirir ve server'ı başlatır.

### Adım 3: LM Studio'yu Yeniden Başlatın
Değişikliklerin etkili olması için LM Studio'yu yeniden başlatın.

## Kullanım Örnekleri

MCP server aktif olduktan sonra, LLM'e aşağıdaki gibi sorular sorabilirsiniz:

### Fiyat Sorgulama
- "Bitcoin'in şu anki fiyatı nedir?"
- "Ethereum'u Binance'den kontrol et"
- "Top 10 kripto paranın durumu nedir?"
- "What is the current price of Bitcoin?"
- "Check Ethereum price on Kraken"
- "Show me the top 10 cryptocurrencies"

### Haber Sorgulama
- "Kripto piyasasında son haberler neler?"
- "Bitcoin ile ilgili güncel gelişmeler"
- "Latest crypto news from CryptoCompare"
- "Any breaking news in cryptocurrency market?"

### Çoklu Kaynak Karşılaştırma
- "Farklı borsalardan Bitcoin fiyatlarını karşılaştır"
- "Compare Bitcoin prices across different exchanges"
- "Get Bitcoin price from multiple sources"

### Detaylı Analiz
- "Bitcoin'in piyasa performansı nasıl?"
- "Ethereum'un 24 saatlik değişimi nedir?"
- "Show me detailed analysis of top cryptocurrencies"
- "What are the market trends for altcoins?"

### Özel Sorgular
- "CoinPaprika'dan detaylı Bitcoin bilgilerini al"
- "Get Bitcoin data from CoinStats"
- "Show me available tools for crypto analysis"
- "List all cryptocurrency tools you have"

### Gelişmiş Kullanım
- "Bitcoin ve Ethereum'u karşılaştır, hangi borsa daha iyi fiyat veriyor?"
- "Compare Bitcoin prices on Binance vs Kraken"
- "Get news and price analysis for Ethereum"
- "Show me market overview and latest news together"

## Araç Açıklamaları

- `list_available_tools()`: Mevcut tüm araçları listeler ve açıklamalarını gösterir
- `get_crypto_price(coin_name)`: CoinGecko'dan fiyat (varsayılan, coin adı ile)
- `get_price_binance(symbol)`: Binance borsasından fiyat (BTCUSDT gibi semboller)
- `get_price_kraken(pair)`: Kraken borsasından fiyat (XBTUSD gibi pair'ler)
- `get_price_coinpaprika(coin_id)`: CoinPaprika'dan detaylı fiyat (btc-bitcoin gibi ID'ler)
- `get_price_coinstats(coin)`: CoinStats'den fiyat (bitcoin gibi isimler)
- `get_crypto_news_cryptocompare()`: CryptoCompare'den güncel haberler
- `market_analysis()`: İlk 10 kripto paranın piyasa özeti
- `get_latest_news()`: Temel haber placeholder

## Sorun Giderme

### Server Başlamıyor
- Python yolunun doğru olduğundan emin olun
- Bağımlılıkların yüklü olduğunu kontrol edin
- Firewall ayarlarını kontrol edin

### Araçlar Görünmüyor
- Config dosyasının syntax'ını kontrol edin
- Uygulamayı yeniden başlatın
- Log dosyalarını inceleyin

### API Limitleri
- Ücretsiz API'ler günlük limitlere tabidir
- Alternatif API'leri kullanın

## Gelişmiş Konfigürasyon

### Ortam Değişkenleri
API anahtarları gerekiyorsa env bölümüne ekleyin:

```json
"env": {
  "API_KEY": "your_api_key_here"
}
```

### Çoklu Server
Birden fazla MCP server ekleyebilirsiniz:

```json
{
  "mcpServers": {
    "crypto-mcp": { ... },
    "other-server": { ... }
  }
}
```