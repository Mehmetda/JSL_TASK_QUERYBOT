# Local LLM Setup Guide

Bu rehber, projeyi OpenAI yerine local Llama 7B modeli ile çalıştırmak için gerekli adımları açıklar.

## 🚀 Hızlı Başlangıç

### 1. Gerekli Paketleri Yükleyin

```bash
pip install -r requirements.txt
```

### 2. Model Konfigürasyonu

`config.py` dosyasında model ayarlarını yapabilirsiniz:

```python
# Varsayılan model (küçük ve hızlı)
LLM_MODEL_NAME = "microsoft/DialoGPT-medium"

# Llama 7B modeli için (daha büyük, daha iyi performans)
# LLM_MODEL_NAME = "meta-llama/Llama-2-7b-chat-hf"
```

### 3. Uygulamayı Test Edin

```bash
python test_local_llm.py
```

### 4. Uygulamayı Çalıştırın

```bash
streamlit run app/ui/streamlit_app.py
```

## 📋 Desteklenen Modeller

### Küçük Modeller (Hızlı, az RAM)
- `microsoft/DialoGPT-small` (varsayılan fallback)
- `microsoft/DialoGPT-medium`

### Llama Modelleri (Daha iyi performans, daha fazla RAM)
- `meta-llama/Llama-2-7b-chat-hf` (önerilen)
- `meta-llama/Llama-2-7b-hf`

## ⚙️ Konfigürasyon Seçenekleri

`config.py` dosyasında aşağıdaki ayarları yapabilirsiniz:

```python
# LLM Model
LLM_MODEL_NAME = "meta-llama/Llama-2-7b-chat-hf"

# Embedding Model (semantic search için)
EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"

# GPU kullanımı
USE_GPU = True  # GPU varsa kullan

# Veritabanı yolu
DATABASE_PATH = "app/db/demo.sqlite"
```

## 🔧 Sistem Gereksinimleri

### Minimum Gereksinimler
- **RAM**: 8GB (DialoGPT için)
- **Disk**: 2GB boş alan
- **Python**: 3.8+

### Önerilen Gereksinimler (Llama 7B için)
- **RAM**: 16GB+
- **GPU**: NVIDIA GPU (8GB+ VRAM)
- **Disk**: 10GB+ boş alan

## 🐛 Sorun Giderme

### Model Yükleme Hatası
```bash
# Cache'i temizle
rm -rf ~/.cache/huggingface/

# Tekrar dene
python test_local_llm.py
```

### GPU Kullanımı
```python
# config.py'de GPU'yu kapat
USE_GPU = False
```

### Bellek Hatası
Daha küçük bir model kullanın:
```python
LLM_MODEL_NAME = "microsoft/DialoGPT-small"
```

## 📊 Performans Karşılaştırması

| Model | Boyut | RAM | Hız | Kalite |
|-------|-------|-----|-----|--------|
| DialoGPT-small | ~300MB | 2GB | Çok Hızlı | Orta |
| DialoGPT-medium | ~1.5GB | 4GB | Hızlı | İyi |
| Llama-2-7b | ~13GB | 16GB | Yavaş | Çok İyi |

## 🔄 OpenAI'dan Geçiş

Proje artık tamamen local çalışır:
- ✅ OpenAI API key gerekmez
- ✅ İnternet bağlantısı gerekmez
- ✅ Veri güvenliği (local processing)
- ✅ Maliyet yok

## 📝 Notlar

- İlk çalıştırmada model indirilecektir (internet gerekir)
- Model cache'lenir, sonraki çalıştırmalarda hızlı başlar
- GPU varsa otomatik kullanılır
- CPU'da da çalışır ama daha yavaş olur
