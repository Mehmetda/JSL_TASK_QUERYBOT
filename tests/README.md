# Test Suite

Bu klasör, Medical QueryBot projesinin tüm testlerini içerir.

## 📁 Test Dosyaları

### 🔧 Temel Testler
- `test_local_llm.py` - Local LLM entegrasyonu testleri
- `test_llm_switching.py` - LLM geçiş fonksiyonları testleri
- `test_ner_filter.py` - NER (Named Entity Recognition) filtre testleri

### 🔍 RAG Testleri
- `test_rag_schema.py` - RAG schema retrieval testleri
- `test_hybrid_rag.py` - Hybrid RAG (embedding + keyword) testleri

### 🔄 Pipeline Testleri
- `test_retry_flow.py` - SQL retry/repair flow testleri
- `test_integration.py` - Tam entegrasyon testleri

### 🚀 Test Runner
- `run_all_tests.py` - Tüm testleri çalıştırır

## 🏃‍♂️ Testleri Çalıştırma

### Tüm Testleri Çalıştır
```bash
python tests/run_all_tests.py
```

### Tekil Test Çalıştır
```bash
# Local LLM testleri
python tests/test_local_llm.py

# LLM switching testleri
python tests/test_llm_switching.py

# NER filter testleri
python tests/test_ner_filter.py

# RAG testleri
python tests/test_rag_schema.py

# Hybrid RAG testleri
python tests/test_hybrid_rag.py

# Retry flow testleri
python tests/test_retry_flow.py

# Entegrasyon testleri
python tests/test_integration.py
```

## 📋 Test Gereksinimleri

### Temel Gereksinimler
- Python 3.8+
- Tüm requirements.txt paketleri yüklü

### LLM Testleri için
- Local LLM modelleri indirilmiş
- OpenAI API key (opsiyonel)

### NER Testleri için
- spaCy modelleri indirilmiş:
  ```bash
  python -m spacy download xx_ent_wiki_sm
  python -m spacy download en_core_web_sm
  ```

## 🎯 Test Kategorileri

### 1. Unit Tests
- Bireysel fonksiyon ve sınıf testleri
- Mock verilerle izole testler

### 2. Integration Tests
- Bileşenler arası etkileşim testleri
- Gerçek veritabanı ile testler

### 3. End-to-End Tests
- Tam pipeline testleri
- Kullanıcı senaryoları testleri

## 📊 Test Sonuçları

Her test dosyası şu formatı kullanır:
- ✅ Başarılı testler
- ❌ Başarısız testler
- 📊 Test istatistikleri

## 🐛 Sorun Giderme

### Test Başarısız Olursa
1. Gerekli paketlerin yüklü olduğundan emin olun
2. Veritabanı bağlantısını kontrol edin
3. API key'lerin doğru olduğundan emin olun
4. Log mesajlarını inceleyin

### Yaygın Sorunlar
- **spaCy model hatası**: `python -m spacy download xx_ent_wiki_sm`
- **OpenAI API hatası**: API key'i kontrol edin
- **Local LLM hatası**: Model dosyalarını kontrol edin
- **Veritabanı hatası**: `app/db/demo.sqlite` dosyasının varlığını kontrol edin

## 🔧 Test Geliştirme

### Yeni Test Ekleme
1. `tests/` klasöründe yeni dosya oluşturun
2. `test_` prefix'i kullanın
3. `run_all_tests.py`'ye ekleyin
4. README'yi güncelleyin

### Test Formatı
```python
def test_function_name():
    """Test description"""
    print("Testing...")
    try:
        # Test code
        print("✅ Test passed")
        return True
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

def main():
    """Run all tests"""
    tests = [test_function_name]
    # ... test runner code
```

## 📈 Test Coverage

- **LLM Integration**: ✅
- **NER Filtering**: ✅
- **SQL Generation**: ✅
- **Data Validation**: ✅
- **Security Checks**: ✅
- **Pipeline Flow**: ✅
- **Error Handling**: ✅
