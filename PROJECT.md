# Crypto_MCP Proje Dökümanı

## Proje Özeti

Crypto_MCP, yerel Large Language Model (LLM) sistemlerinin dış dünyaya kapalı yapısını kırarak, kripto para piyasası gibi son derece dinamik ve hızlı değişen bir alanda güncel ve analiz edilmiş veriye ulaşmasını sağlayan modern bir Model Context Protocol (MCP) köprüsüdür.

## Proje Amacı ve Vizyon

Günümüzde yerel LLM'ler (örneğin Ollama, LM Studio) güçlü yapay zeka yetenekleri sunsa da, internet erişimi olmadığından güncel piyasa verilerine ulaşamaz. Bu durum özellikle kripto para gibi 24/7 değişen piyasalarda ciddi bir sınırlama yaratır.

Crypto_MCP projesi bu sorunu çözmek için:
- **Gerçek Zamanlı Veri Erişimi**: Kripto fiyatları, haberler ve piyasa analizleri
- **Çoklu Veri Kaynağı**: Farklı API'lerden gelen verilerin karşılaştırılması
- **LLM Entegrasyonu**: Yerel LLM'lerin bu verileri doğal dille sorgulaması
- **Güvenlik ve Gizlilik**: Tüm işlemler yerel ortamda kalır

## Teknoloji Altyapısı

### Ana Teknolojiler
- **Programlama Dili**: Python 3.10+
- **MCP Framework**: FastMCP (Python için optimize edilmiş MCP kütüphanesi)
- **Veri Kaynakları**: 6 farklı ücretsiz kripto API'si
- **LLM Entegrasyonu**: Claude Desktop, LM Studio desteği

### Veri Kaynakları
1. **CoinGecko API**: Genel kripto fiyatları ve piyasa verileri
2. **Binance API**: Spot ticaret fiyatları
3. **Kraken API**: Profesyonel ticaret verileri
4. **CoinPaprika API**: Detaylı coin bilgileri
5. **CoinStats API**: Basit fiyat verileri
6. **CryptoCompare API**: Kripto haberleri ve analizler

## Proje Özellikleri

### Temel Özellikler
- **Fiyat Sorgulama**: 6 farklı kaynaktan kripto para fiyatları
- **Haber Akışı**: Güncel kripto haberleri
- **Piyasa Analizi**: Top 10 kripto paranın performans özeti
- **Araç Listeleme**: Mevcut tüm araçları görüntüleme
- **Çoklu Dil Desteği**: Türkçe ve İngilizce arayüz

### Teknik Özellikler
- **Modüler Tasarım**: Her API ayrı araç olarak implemente edilmiş
- **Hata Yönetimi**: API limitleri ve bağlantı hatalarına karşı dayanıklı
- **Performans Optimizasyonu**: Paralel veri çekme ve caching desteği
- **Genişletilebilirlik**: Yeni API'lerin kolay eklenmesi

## Kullanım Senaryoları

### Finansal Analiz
- Portföy yönetimi ve risk analizi
- Fiyat karşılaştırması ve arbitraj fırsatları
- Piyasa trendlerinin takibi

### Eğitim ve Öğrenme
- Kripto para eğitiminde güncel örnekler
- Piyasa dinamiklerini anlama
- Teknik analiz uygulamaları

### Geliştirme ve Test
- Trading botlarının test edilmesi
- Veri analizi projelerinde benchmark
- API entegrasyonlarının doğrulanması
### Örnek Kullanıcı Sorguları

#### Basit Sorgular
- "Bitcoin fiyatı nedir?"
- "Ethereum kaç dolar?"
- "Kripto haberleri neler?"

#### Gelişmiş Sorgular
- "Bitcoin'i Binance, Kraken ve CoinGecko'da karşılaştır"
- "Top 10 coin'in 24 saatlik değişimini göster"
- "CryptoCompare'den son haberleri al"

#### Analitik Sorgular
- "Piyasa genel durumu nasıl?"
- "Hangi coin'ler yükseliyor?"
- "Volatilite yüksek olan kripto paralar"
## Kurulum ve Çalıştırma

### Sistem Gereksinimleri
- Windows/Linux/macOS
- Python 3.10 veya üzeri
- İnternet bağlantısı (API erişimi için)

### Kurulum Adımları
1. **Python Ortamı Kurulumu**
   ```bash
   python -m venv .venv
   .venv\Scripts\activate  # Windows
   pip install -r requirements.txt
   ```

2. **MCP Server Başlatma**
   ```bash
   python crypto_mcp.py
   ```

3. **LLM Entegrasyonu**
   - Claude Desktop: `claude_desktop_config.json` kullanın
   - LM Studio: `lm_studio_config.json` kullanın

### Test ve Doğrulama
- MCP Inspector ile araçları test edin
- Örnek sorgular: "Bitcoin fiyatı nedir?", "Kripto haberleri"

## Proje Yapısı

```
Crypto_MCP/
├── crypto_mcp.py          # Ana MCP server kodu
├── requirements.txt       # Python bağımlılıkları
├── README.md              # Temel kullanım rehberi
├── MCP_Integration.md     # Detaylı entegrasyon rehberi
├── claude_desktop_config.json  # Claude Desktop config örneği
├── lm_studio_config.json       # LM Studio config örneği
└── .venv/                 # Python sanal ortamı
```

## Geliştirme Yol Haritası

### Kısa Vadeli Hedefler (1-3 ay)
- [x] Temel MCP server implementasyonu
- [x] Çoklu API entegrasyonu
- [x] Claude Desktop entegrasyonu
- [ ] LM Studio tam entegrasyonu
- [ ] Haber API'si geliştirme (CryptoPanic)

### Orta Vadeli Hedefler (3-6 ay)
- [ ] Teknik analiz araçları
- [ ] Grafik ve görselleştirme
- [ ] Çoklu dil desteği genişletme
- [ ] Web arayüzü

### Uzun Vadeli Hedefler (6+ ay)
- [ ] Özel trading botları
- [ ] Portföy yönetim sistemi
- [ ] Sosyal medya entegrasyonu
- [ ] Mobil uygulama

## Riskler ve Çözümler

### Teknik Riskler
- **API Limitleri**: Çözüm: Çoklu API kullanımı ve caching
- **Veri Tutarsızlığı**: Çözüm: Veri validasyonu ve cross-checking
- **Güvenlik**: Çözüm: Yerel çalıştırma ve API key koruması

### Piyasa Riskleri
- **API Değişiklikleri**: Çözüm: Modüler tasarım ve hızlı adaptasyon
- **Rekabet**: Çözüm: Benzersiz çoklu kaynak yaklaşımı

## Katkıda Bulunma

Proje açık kaynak olarak geliştirilmektedir. Katkıda bulunmak için:
1. GitHub repository'sini forklayın
2. Feature branch oluşturun
3. Pull request gönderin

### Geliştirme Standartları
- PEP 8 kod stili
- İngilizce docstring'ler
- Unit test coverage
- MCP protokol uyumluluğu

## Lisans ve Kullanım

Bu proje MIT lisansı altında açık kaynak kodludur. Ticari ve kişisel kullanım için serbesttir.

## İletişim ve Destek

- **GitHub Issues**: Hata raporları ve özellik istekleri
- **Discussions**: Genel tartışmalar ve yardım
- **Wiki**: Detaylı dokümantasyon

## Sonuç ve Gelecek Beklentileri

Crypto_MCP, yerel LLM'lerin kripto piyasasına erişimini demokratikleştirerek, yapay zeka destekli finansal analizlerin daha geniş kitlelere ulaşmasını sağlayacaktır. Proje, MCP protokolünün güçlü yeteneklerini kullanarak, güvenli ve etkili bir veri köprüsü oluşturmaktadır.

Gelecekte, daha fazla finansal araç ve gelişmiş analiz özellikleriyle projenin etkisi artacaktır.