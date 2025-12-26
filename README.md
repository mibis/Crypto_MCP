# Crypto_MCP

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python Version](https://img.shields.io/badge/python-3.10+-blue.svg)](https://python.org)
[![GitHub Issues](https://img.shields.io/github/issues/mibis/Crypto_MCP)](https://github.com/mibis/Crypto_MCP/issues)
[![GitHub Stars](https://img.shields.io/github/stars/mibis/Crypto_MCP)](https://github.com/mibis/Crypto_MCP/stargazers)

Crypto_MCP, yerel bir LLM'in (Large Language Model) dış dünyaya kapalı yapısını kırarak, kripto piyasası gibi son derece dinamik bir alanda güncel ve analiz edilmiş veriye ulaşmasını sağlayacak modern bir köprü olacaktır.

Detaylı proje açıklaması için [PROJECT.md](PROJECT.md) dosyasına bakın.

Kapsamlı kullanım örnekleri için [USAGE_EXAMPLES.md](USAGE_EXAMPLES.md) dosyasına bakın.

## 🚀 Hızlı Başlangıç

### Ön Gereksinimler

- **Python 3.10+**: [python.org](https://python.org) adresinden indirin
- **Git**: [git-scm.com](https://git-scm.com) adresinden indirin
- **Claude Desktop** veya **LM Studio** (MCP desteği ile)

### Kurulum

```bash
# Repository'yi klonlayın
git clone https://github.com/YOUR_USERNAME/Crypto_MCP.git
cd Crypto_MCP

# Sanal ortam oluşturun
python -m venv .venv

# Windows için
.venv\Scripts\activate

# macOS/Linux için
# source .venv/bin/activate

# Bağımlılıkları yükleyin
pip install -r requirements.txt
```

### Test

```bash
# MCP Inspector ile test edin
npm install -g @modelcontextprotocol/inspector
npx @modelcontextprotocol/inspector --config test_config.json --server crypto-mcp
```

### LLM Entegrasyonu

#### Claude Desktop
1. `claude_desktop_config.json` dosyasını kopyalayın
2. Claude Desktop'ı yeniden başlatın

#### LM Studio
1. `lm_studio_config.json` dosyasını kopyalayın
2. LM Studio'yu yeniden başlatın

## � GitHub'a Publish Etme

### Repository Oluşturma

1. [GitHub.com](https://github.com)'da yeni repository oluşturun
2. Repository adını `Crypto_MCP` yapın
3. Public veya private seçin
4. README, .gitignore, license eklemeyin (zaten var)

### Kod Yükleme

```bash
# Local repository'yi başlatın (eğer git init yapmadıysanız)
git init
git add .
git commit -m "Initial commit: Crypto_MCP MCP server for crypto data"

# GitHub repository'sini remote olarak ekleyin
git remote add origin https://github.com/mibis/Crypto_MCP.git

# Push edin
git push -u origin main
```

### Release Oluşturma

1. GitHub repository'sinde "Releases" sekmesine gidin
2. "Create a new release" tıklayın
3. Tag version: `v1.0.0`
4. Release title: `Crypto_MCP v1.0.0`
5. Description: Proje özelliklerini açıklayın

## 📥 Clone ve Kurulum

### Repository'yi İndirme

```bash
# Repository'yi klonlayın
git clone https://github.com/YOUR_USERNAME/Crypto_MCP.git
cd Crypto_MCP
```

### Otomatik Kurulum (Windows)

```bash
# Kurulum scripti çalıştırın (gelecekte eklenecek)
# setup.bat
```

### Manuel Kurulum

```bash
# Sanal ortam oluşturun
python -m venv .venv

# Aktifleştirin
.venv\Scripts\activate  # Windows
# source .venv/bin/activate  # macOS/Linux

# Bağımlılıkları yükleyin
pip install -r requirements.txt

# Test edin
python crypto_mcp.py
```

### LLM Entegrasyonu

```bash
# MCP Inspector ile test edin
npm install -g @modelcontextprotocol/inspector
npx @modelcontextprotocol/inspector --config test_config.json --server crypto-mcp
```

## 🔄 Güncellemeler

```bash
# Repository'yi güncelleyin
git pull origin main

# Yeni bağımlılıkları yükleyin
pip install -r requirements.txt
```

## 🛠️ Geliştirme

### Yerel Geliştirme Ortamı

```bash
# Gerekli paketleri yükleyin
pip install -r requirements.txt

# Kod değişikliklerini test edin
python -m pytest  # Testler eklendikçe

# MCP Inspector ile debug edin
npx @modelcontextprotocol/inspector --config test_config.json --server crypto-mcp
```

### Yeni Araç Ekleme

1. `crypto_mcp.py`'ye yeni `@mcp.tool()` fonksiyonu ekleyin
2. Docstring'i detaylı yazın
3. `USAGE_EXAMPLES.md`'ye örnek sorgu ekleyin
4. Test edin

## 📁 Proje Yapısı

```
Crypto_MCP/
├── crypto_mcp.py              # Ana MCP server kodu
├── requirements.txt           # Python bağımlılıkları
├── test_config.json           # Test config dosyası
├── start_crypto_mcp.bat       # Windows başlatıcı
├── claude_desktop_config.json # Claude Desktop config
├── lm_studio_config.json      # LM Studio config
├── README.md                  # Bu dosya
├── PROJECT.md                 # Proje açıklaması
├── USAGE_EXAMPLES.md          # Kullanım örnekleri
├── MCP_Integration.md         # Entegrasyon rehberi
├── LICENSE                    # MIT lisansı
└── .gitignore                # Git ignore kuralları
```

## 🤝 Katkıda Bulunma

1. Fork edin
2. Feature branch oluşturun (`git checkout -b feature/amazing-feature`)
3. Commit edin (`git commit -m 'Add amazing feature'`)
4. Push edin (`git push origin feature/amazing-feature`)
5. Pull Request açın

Detaylı katkıda bulunma rehberi için [CONTRIBUTING.md](CONTRIBUTING.md) dosyasına bakın.

## 📄 Lisans

Bu proje MIT lisansı altında lisanslanmıştır. Detaylar için [LICENSE](LICENSE) dosyasına bakın.

## 🙏 Teşekkürler

- [Model Context Protocol](https://modelcontextprotocol.io/) ekibi
- [FastMCP](https://github.com/jlowin/fastmcp) kütüphanesi
- Kripto API sağlayıcıları (CoinGecko, Binance, vb.)

## 📞 İletişim

- GitHub Issues: Hata raporları ve özellik istekleri
- Discussions: Genel tartışmalar

---

⭐ Bu proje faydalı olduysa yıldız vermeyi unutmayın!

Bu proje, Model Context Protocol (MCP) kullanarak yerel LLM'lerin kripto piyasası verilerine erişmesini sağlar.

## Veri Kaynakları (APIs)

- **CoinGecko**: Ücretsiz fiyat ve market verileri
- **Binance**: Spot fiyat verileri (ücretsiz)
- **Kraken**: Public ticker verileri (ücretsiz)
- **CoinPaprika**: Ücretsiz fiyat verileri
- **CoinStats**: Ücretsiz fiyat verileri
- **CryptoCompare**: Ücretsiz haber verileri

## Kurulum

1. Python 3.10+ yüklü olduğundan emin olun.
2. Sanal ortam oluşturun ve etkinleştirin:
   ```bash
   python -m venv .venv
   .venv\Scripts\activate  # Windows
   ```
3. Bağımlılıkları yükleyin:
   ```bash
   pip install -r requirements.txt
   ```

## Çalıştırma

MCP server'ını başlatmak için:
```bash
python crypto_mcp.py
```

## Araçlar (Tools)

- `list_available_tools()`: Mevcut tüm araçları listeler
- `get_crypto_price(coin_name)`: CoinGecko'dan fiyat (varsayılan)
- `get_price_binance(symbol)`: Binance borsasından fiyat
- `get_price_kraken(pair)`: Kraken borsasından fiyat
- `get_price_coinpaprika(coin_id)`: CoinPaprika'dan detaylı fiyat
- `get_price_coinstats(coin)`: CoinStats'den fiyat
- `get_crypto_news_cryptocompare()`: CryptoCompare'den haberler
- `market_analysis()`: İlk 10 kripto para özeti
- `get_latest_news()`: Temel haber placeholder

## MCP Server Entegrasyonu

Detaylı entegrasyon rehberi için [MCP_Integration.md](MCP_Integration.md) dosyasına bakın.

### Hızlı Kurulum

1. **Claude Desktop için:**
   - `claude_desktop_config.json` dosyasını kopyalayın
   - `start_crypto_mcp.bat` dosyasını kullanın
   - Claude Desktop'ı yeniden başlatın

2. **LM Studio için:**
   - `lm_studio_config.json` dosyasını kopyalayın
   - `start_crypto_mcp.bat` dosyasını kullanın
   - LM Studio'yu yeniden başlatın

### Kullanım
LLM'e kripto sorularınızı sorun: "Bitcoin fiyatı nedir?" veya "Kripto haberleri neler?"

#### Örnek Sorgular:
- **Basit Fiyat:** "Bitcoin kaç dolar?"
- **Karşılaştırma:** "BTC'yi farklı borsalarda karşılaştır"
- **Haber:** "Kripto piyasasında son gelişmeler"
- **Analiz:** "Top 10 coin'in performansı"
- **Detaylı:** "Ethereum'u CoinPaprika'dan incele"

## API Anahtarları

- CoinGecko: Ücretsiz, API anahtarı gerekmiyor.
- CryptoPanic: Ücretsiz API anahtarı alın.