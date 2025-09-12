# LLM Switching Guide

Bu rehber, Streamlit UI'daki LLM seçim özelliklerini açıklar.

## 🤖 LLM Seçenekleri

### 1. 🔄 Auto Mode (Önerilen)
- **Nasıl çalışır**: İnternet varsa OpenAI, yoksa Local LLM kullanır
- **Avantajları**: Otomatik geçiş, en iyi performans
- **Kullanım**: Varsayılan seçenek

### 2. 🔑 OpenAI Only
- **Nasıl çalışır**: Sadece OpenAI API kullanır
- **Avantajları**: En iyi kalite, hızlı
- **Gereksinimler**: İnternet + OpenAI API key

### 3. 🏠 Local Only
- **Nasıl çalışır**: Sadece local LLM kullanır
- **Avantajları**: Offline çalışır, veri güvenliği
- **Gereksinimler**: Yeterli RAM (8GB+)

## 🎯 Kullanım Senaryoları

### Senaryo 1: Normal Kullanım
```
Seçim: Auto Mode
Durum: İnternet var + OpenAI key var
Sonuç: OpenAI kullanılır
```

### Senaryo 2: İnternet Kesintisi
```
Seçim: Auto Mode
Durum: İnternet yok
Sonuç: Local LLM kullanılır
```

### Senaryo 3: OpenAI Key Yok
```
Seçim: Auto Mode
Durum: İnternet var ama OpenAI key yok
Sonuç: Local LLM kullanılır
```

### Senaryo 4: Offline Çalışma
```
Seçim: Local Only
Durum: İnternet yok
Sonuç: Local LLM kullanılır
```

## 🔧 Konfigürasyon

### OpenAI API Key
```bash
# .env dosyası oluşturun
echo "OPENAI_API_KEY=your_api_key_here" > .env
```

### Local LLM Model
```python
# config.py dosyasında
LLM_MODEL_NAME = "microsoft/DialoGPT-medium"  # Küçük model
# LLM_MODEL_NAME = "meta-llama/Llama-2-7b-chat-hf"  # Büyük model
```

## 📊 Durum Göstergeleri

### Sidebar'da Gösterilen Bilgiler:
- 🌐 **Internet**: Bağlantı durumu
- 🔑 **OpenAI**: API erişilebilirliği
- 🎯 **Currently using**: Aktif LLM

### Metadata'da Gösterilen Bilgiler:
- **Selected Mode**: Kullanıcının seçtiği mod
- **Effective Mode**: Gerçekte kullanılan mod
- **Token Usage**: LLM kullanım istatistikleri

## 🚀 Kurulum

```bash
# 1. Paketleri yükle
pip install -r requirements.txt

# 2. spaCy modellerini indir
python -m spacy download xx_ent_wiki_sm
python -m spacy download en_core_web_sm

# 3. Test et
python test_local_llm.py

# 4. Çalıştır
streamlit run app/ui/streamlit_app.py
```

## 🐛 Sorun Giderme

### OpenAI Kullanılamıyor
- ✅ İnternet bağlantısını kontrol edin
- ✅ OpenAI API key'inizi kontrol edin
- ✅ Auto mode kullanın (otomatik local'a geçer)

### Local LLM Yüklenmiyor
- ✅ Yeterli RAM olduğundan emin olun (8GB+)
- ✅ Daha küçük model seçin (DialoGPT-small)
- ✅ GPU kullanımını kapatın (config.py'de USE_GPU=False)

### Performans Sorunları
- ✅ Local mode için daha küçük model kullanın
- ✅ GPU varsa kullanın
- ✅ Auto mode ile en iyi performansı alın

## 💡 İpuçları

1. **İlk kullanım**: Auto mode ile başlayın
2. **Offline çalışma**: Local only mode kullanın
3. **En iyi kalite**: OpenAI only mode kullanın
4. **Güvenlik**: Local only mode kullanın
5. **Performans**: Auto mode kullanın

## 📈 Performans Karşılaştırması

| Mode | Hız | Kalite | Güvenlik | Maliyet |
|------|-----|--------|----------|---------|
| Auto | ⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐ |
| OpenAI | ⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐ | ⭐ |
| Local | ⭐⭐ | ⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐ |
