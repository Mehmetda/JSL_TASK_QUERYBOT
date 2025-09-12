"""
Dynamic System Prompt Generator for Medical QueryBot
"""
import sqlite3
from typing import Dict, List, Any
from math import sqrt

# Lazy embedding model holder
_embedding_model = None

def _get_embedding_model():
    """Lazily load and return the sentence transformer model.

    Falls back to a lightweight bag-of-words embedding if transformers are unavailable.
    """
    global _embedding_model
    if _embedding_model is not None:
        return _embedding_model
    try:
        from sentence_transformers import SentenceTransformer  # type: ignore
        _embedding_model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
    except Exception:
        _embedding_model = None
    return _embedding_model

def _embed_texts(texts: List[str]) -> List[List[float]]:
    """Embed a list of texts into vector representations.

    Uses SentenceTransformer if available; otherwise, computes a simple
    normalized bag-of-words vector over the given batch (shared vocabulary).
    """
    model = _get_embedding_model()
    if model is not None:
        vectors = model.encode(texts, normalize_embeddings=True)
        # Ensure list of lists
        return [vec.tolist() if hasattr(vec, "tolist") else list(vec) for vec in vectors]

    # Fallback: simple bag-of-words with shared vocab
    # Build vocabulary for this batch
    vocab: Dict[str, int] = {}
    for text in texts:
        for token in text.lower().split():
            if token not in vocab:
                vocab[token] = len(vocab)

    dim = len(vocab)
    vectors: List[List[float]] = []
    for text in texts:
        vec = [0.0] * dim
        tokens = text.lower().split()
        for token in tokens:
            idx = vocab.get(token)
            if idx is not None:
                vec[idx] += 1.0
        # L2 normalize
        norm = sqrt(sum(v * v for v in vec)) or 1.0
        vec = [v / norm for v in vec]
        vectors.append(vec)
    return vectors

def _cosine(a: List[float], b: List[float]) -> float:
    """Compute cosine similarity between two vectors (assumed normalized)."""
    # If not equal length, compare up to min length
    n = min(len(a), len(b))
    if n == 0:
        return 0.0
    return sum(a[i] * b[i] for i in range(n))

def get_database_schema_info(conn: sqlite3.Connection) -> str:
    """Get comprehensive database schema information with column analysis"""
    cursor = conn.cursor()
    
    # Get all tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = cursor.fetchall()
    
    schema_info = []
    
    for table in tables:
        table_name = table[0]
        
        # Skip system tables
        if table_name in ['sqlite_sequence']:
            continue
            
        # Get table info
        cursor.execute(f"PRAGMA table_info({table_name})")
        columns = cursor.fetchall()
        
        # Get record count
        cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
        count = cursor.fetchone()[0]
        
        # Analyze column types for ORDER BY compatibility
        col_info = []
        numeric_columns = []
        date_columns = []
        
        for col in columns:
            col_name = col[1]
            col_type = col[2].upper()
            is_pk = bool(col[5])
            pk_marker = " (PRIMARY KEY)" if is_pk else ""
            
            # Check if column is suitable for ORDER BY
            if col_type in ['INTEGER', 'REAL', 'NUMERIC']:
                numeric_columns.append(col_name)
            elif col_type in ['TEXT'] and any(date_word in col_name.upper() for date_word in ['TIME', 'DATE', 'ADMIT', 'DISCH']):
                date_columns.append(col_name)
            
            col_info.append(f"{col_name} ({col_type}){pk_marker}")
        
        # Add ORDER BY compatibility info
        order_by_info = ""
        if numeric_columns or date_columns:
            order_by_cols = numeric_columns + date_columns
            order_by_info = f"\n  🔢 ORDER BY uygun kolonlar: {', '.join(order_by_cols)}"
        else:
            order_by_info = "\n  ⚠️ ORDER BY için uygun kolon yok - LIMIT kullanmayın"
        
        schema_info.append(f"""
📋 {table_name} ({count} kayıt):
  - {', '.join(col_info)}{order_by_info}""")
    
    return "\n".join(schema_info)

def generate_system_prompt(conn: sqlite3.Connection) -> str:
    """Generate comprehensive system prompt for medical database queries"""
    
    schema_info = get_database_schema_info(conn)
    
    system_prompt = f"""Sen bir tıbbi veritabanı uzmanısın ve SQLite veritabanı üzerinde çalışıyorsun. Kullanıcıların doğal dil sorularını SQL sorgularına dönüştürmek için tasarlandın.

## 🏥 VERİTABANI ŞEMASI

{schema_info}

## 🔗 TABLO İLİŞKİLERİ

- **json_patients** ↔ **json_admissions**: subject_id ile bağlantılı
- **json_admissions** ↔ **json_transfers**: hadm_id ile bağlantılı  
- **json_admissions** ↔ **json_providers**: admit_provider_id ile bağlantılı
- **json_patients** ↔ **json_transfers**: subject_id ile bağlantılı

## 📊 VERİ TİPLERİ VE AÇIKLAMALAR

### Hasta Bilgileri (json_patients)
- **subject_id**: Hasta benzersiz kimliği
- **gender**: Cinsiyet (M/F)
- **anchor_age**: Yaş
- **anchor_year**: Referans yılı
- **dod**: Ölüm tarihi (varsa)

### Yatış Bilgileri (json_admissions)  
- **hadm_id**: Yatış benzersiz kimliği
- **admittime**: Yatış zamanı
- **dischtime**: Çıkış zamanı
- **admission_type**: Yatış tipi (EMERGENCY, ELECTIVE, vb.)
- **admission_location**: Yatış yeri
- **discharge_location**: Çıkış yeri
- **insurance**: Sigorta bilgisi
- **race**: Irk bilgisi
- **marital_status**: Medeni durum

### Transfer Bilgileri (json_transfers)
- **transfer_id**: Transfer benzersiz kimliği
- **eventtype**: Transfer tipi (admit, transfer, discharge)
- **careunit**: Bakım birimi
- **intime**: Giriş zamanı
- **outtime**: Çıkış zamanı

### Sağlık Personeli (json_providers)
- **provider_id**: Personel kimliği
- **npi**: Ulusal sağlık personeli kimliği
- **dea**: DEA numarası

## 🎯 SORU TİPLERİ VE ÖRNEKLER

### Sayısal Sorgular
- "Kaç hasta var?" → `SELECT COUNT(*) FROM json_patients`
- "Kaç yatış var?" → `SELECT COUNT(*) FROM json_admissions`
- "Kaç transfer var?" → `SELECT COUNT(*) FROM json_transfers`

### Demografik Sorgular
- "Hastaların yaş dağılımı nasıl?" → `SELECT anchor_age, COUNT(*) FROM json_patients GROUP BY anchor_age`
- "Cinsiyet dağılımı nedir?" → `SELECT gender, COUNT(*) FROM json_patients GROUP BY gender`
- "Hangi ırktan kaç hasta var?" → `SELECT race, COUNT(*) FROM json_admissions GROUP BY race`

### Yatış Sorguları
- "Acil yatışlar kaç tane?" → `SELECT COUNT(*) FROM json_admissions WHERE admission_type = 'EMERGENCY'`
- "Hangi yatış yerlerinden kaç hasta geldi?" → `SELECT admission_location, COUNT(*) FROM json_admissions GROUP BY admission_location`
- "Sigorta türlerine göre dağılım?" → `SELECT insurance, COUNT(*) FROM json_admissions GROUP BY insurance`

### Transfer Sorguları
- "Hangi bakım birimlerinde kaç transfer var?" → `SELECT careunit, COUNT(*) FROM json_transfers GROUP BY careunit`
- "Transfer tiplerine göre dağılım?" → `SELECT eventtype, COUNT(*) FROM json_transfers GROUP BY eventtype`

### Zaman Bazlı Sorgular
- "Son 30 günde kaç yatış var?" → `SELECT COUNT(*) FROM json_admissions WHERE admittime >= date('now', '-30 days')`
- "2024 yılında kaç hasta geldi?" → `SELECT COUNT(*) FROM json_admissions WHERE strftime('%Y', admittime) = '2024'`
- "En son yatış ne zaman?" → `SELECT admittime, dischtime, admission_type FROM json_admissions ORDER BY admittime DESC LIMIT 1`
- "En yeni 5 yatış" → `SELECT admittime, dischtime, admission_type FROM json_admissions ORDER BY admittime DESC LIMIT 5`

### İlişkisel Sorgular
- "Hangi hastalar birden fazla yatış yapmış?" → `SELECT subject_id, COUNT(*) FROM json_admissions GROUP BY subject_id HAVING COUNT(*) > 1`
- "Hangi doktorlar en çok hasta kabul etmiş?" → `SELECT admit_provider_id, COUNT(*) FROM json_admissions GROUP BY admit_provider_id ORDER BY COUNT(*) DESC`

## ⚠️ ÖNEMLİ KURALLAR - VERİ GÜVENLİĞİ

1. **SADECE SELECT sorguları** oluştur - INSERT, UPDATE, DELETE, DROP, ALTER, CREATE, TRUNCATE, REPLACE YASAK
2. **Tek SQL statement** döndür - Birden fazla statement yasak
3. **Noktalı virgül kullanma** - SQL statement sonunda ; koyma
4. **Güvenli sorgular** yaz - SQL injection'a karşı dikkatli ol
5. **JOIN kullan** - İlişkili tabloları birleştir
6. **Türkçe cevap ver** - Kullanıcı Türkçe soruyorsa Türkçe yanıtla
7. **Anlamlı sonuçlar** döndür - Sadece sayı değil, açıklama da ekle
8. **Hata durumunda** - Veri bulunamazsa açık mesaj ver
9. **LIMIT kullanırken ORDER BY zorunlu** - LIMIT kullanacaksan mutlaka ORDER BY ekle
10. **ORDER BY için numeric/tarih kolonu gerekli** - ORDER BY kullanacaksan kolonun INTEGER, REAL, DATE, DATETIME olması lazım
11. **Numeric kolon yoksa LIMIT kullanma** - Eğer ORDER BY yapabilecek numeric/tarih kolonu yoksa LIMIT kullanma
12. **En son/en yeni** soruları için ORDER BY ... DESC LIMIT 1 kullan (sadece numeric/tarih kolonlarla)
13. **Şema analizi yap** - Her tablo için ORDER BY uygun kolonları kontrol et
14. **VERİ DEĞİŞTİRME YASAK** - Hiçbir şekilde veri ekleme, silme, güncelleme yapma
15. **SADECE OKUMA** - Sadece mevcut verileri okuyup raporla

## 🔍 SORU ANALİZİ

Kullanıcı sorusunu analiz et:
1. **Ana konu**: Hasta, yatış, transfer, personel?
2. **Sorgu tipi**: Sayım, dağılım, filtreleme, ilişki?
3. **Zaman aralığı**: Belirli tarih, dönem?
4. **Gruplama**: Hangi alana göre grupla?
5. **Sıralama**: Hangi kritere göre sırala?

## 📝 ÖRNEK ÇIKTI FORMATI

```sql
-- Kullanıcı sorusu: "Kaç erkek hasta var?"
SELECT 
    gender,
    COUNT(*) as hasta_sayisi
FROM json_patients 
WHERE gender = 'M'
GROUP BY gender;
```

Bu sistem prompt'u kullanarak kullanıcıların doğal dil sorularını doğru SQL sorgularına dönüştür ve anlamlı sonuçlar üret."""

    return system_prompt

def get_enhanced_system_prompt(conn: sqlite3.Connection) -> str:
    """Get enhanced system prompt with additional context"""
    base_prompt = generate_system_prompt(conn)
    
    # Add additional context
    enhanced_prompt = f"""{base_prompt}

## 🚀 GELİŞMİŞ ÖZELLİKLER

### Akıllı Varsayımlar
- Kullanıcı "hasta" dediğinde → json_patients tablosu
- Kullanıcı "yatış" dediğinde → json_admissions tablosu  
- Kullanıcı "transfer" dediğinde → json_transfers tablosu
- Kullanıcı "doktor/personel" dediğinde → json_providers tablosu

### Türkçe-İngilizce Eşleştirme
- hasta → patient
- yatış → admission
- transfer → transfer
- doktor → provider
- yaş → age
- cinsiyet → gender
- yatış yeri → admission_location
- çıkış yeri → discharge_location

### Yaygın Hata Düzeltmeleri
- "hastane" → "hospital" (veritabanında yok, admission_location kullan)
- "klinik" → "careunit" 
- "servis" → "careunit"
- "bölüm" → "careunit"

Bu bilgileri kullanarak kullanıcı sorularını en doğru şekilde SQL sorgularına dönüştür."""

    return enhanced_prompt


def get_contextual_system_prompt(conn: sqlite3.Connection, question: str) -> str:
    """
    Get contextual system prompt with relevant schema snippets
    
    Args:
        conn: Database connection
        question: User question
        
    Returns:
        Enhanced system prompt with relevant schema
    """
    # Get relevant schema snippets
    relevant_schema = get_relevant_schema_snippets(conn, question, top_k=3)
    
    # Get basic system prompt
    base_prompt = get_enhanced_system_prompt(conn)
    
    # Combine with relevant schema
    contextual_prompt = f"""{base_prompt}

## Relevant Schema for this Query
{relevant_schema}

Use the above schema information to generate the most accurate SQL query for the user's question."""
    
    return contextual_prompt


def get_relevant_schema_snippets(conn: sqlite3.Connection, question: str, top_k: int = 3) -> str:
    """
    Get relevant schema snippets based on question keywords
    
    Args:
        conn: Database connection
        question: User question
        top_k: Number of top relevant snippets to return
        
    Returns:
        Relevant schema snippets as string
    """
    try:
        # Get all schema documents
        docs = _build_schema_docs(conn)
        
        if not docs:
            return "No schema information available."
        
        # Simple keyword matching for now
        question_lower = question.lower()
        relevant_docs = []
        
        # Score documents based on keyword matches
        for doc in docs:
            score = 0
            text = doc.get("text", "").lower()
            
            # Medical domain keywords
            medical_keywords = [
                "hasta", "patient", "yatış", "admission", "transfer", 
                "doktor", "provider", "yaş", "age", "cinsiyet", "gender",
                "admittime", "dischtime", "careunit", "admission_type"
            ]
            
            for keyword in medical_keywords:
                if keyword in question_lower and keyword in text:
                    score += 1
            
            if score > 0:
                relevant_docs.append((score, doc))
        
        # Sort by score and take top_k
        relevant_docs.sort(key=lambda x: x[0], reverse=True)
        top_docs = relevant_docs[:top_k]
        
        if not top_docs:
            # Fallback: return first few docs
            top_docs = [(0, doc) for doc in docs[:top_k]]
        
        # Format results
        result_parts = []
        for score, doc in top_docs:
            table = doc.get("table", "")
            column = doc.get("column", "")
            text = doc.get("text", "")
            result_parts.append(f"Table: {table}, Column: {column}\n{text}")
        
        return "\n\n".join(result_parts)
        
    except Exception as e:
        print(f"Error getting relevant schema snippets: {e}")
        return "Error retrieving schema information."


def get_hybrid_relevant_schema_snippets(conn: sqlite3.Connection, question: str, top_k: int = 3) -> str:
    """
    Get relevant schema snippets using hybrid approach (embedding + keyword)
    
    Args:
        conn: Database connection
        question: User question
        top_k: Number of top relevant snippets to return
        
    Returns:
        Relevant schema snippets as string
    """
    try:
        # Get all schema documents
        docs = _build_schema_docs(conn)
        
        if not docs:
            return "No schema information available."
        
        # Extract texts for embedding
        texts = [doc.get("text", "") for doc in docs]
        
        # Get embeddings
        question_embedding = _embed_texts([question])[0]
        doc_embeddings = _embed_texts(texts)
        
        # Calculate similarities
        similarities = []
        for i, doc_embedding in enumerate(doc_embeddings):
            similarity = _cosine(question_embedding, doc_embedding)
            similarities.append((similarity, docs[i]))
        
        # Sort by similarity and take top_k
        similarities.sort(key=lambda x: x[0], reverse=True)
        top_docs = similarities[:top_k]
        
        # Format results
        result_parts = []
        for similarity, doc in top_docs:
            table = doc.get("table", "")
            column = doc.get("column", "")
            text = doc.get("text", "")
            result_parts.append(f"Table: {table}, Column: {column} (similarity: {similarity:.3f})\n{text}")
        
        return "\n\n".join(result_parts)
        
    except Exception as e:
        print(f"Error getting hybrid relevant schema snippets: {e}")
        # Fallback to keyword-based approach
        return get_relevant_schema_snippets(conn, question, top_k)


def get_hybrid_relevant_schema_snippets_with_metadata(
    conn: sqlite3.Connection,
    question: str,
    metadata_filters: 'dict' = None,
    top_k: int = 3,
) -> str:
    """Hybrid retrieval with optional metadata filters.

    metadata_filters example:
      {"table": "json_admissions"} or {"column": "admittime"}
    """
    try:
        docs = _build_schema_docs(conn)
        if not docs:
            return "No schema information available."

        # Apply metadata filters first
        if metadata_filters:
            filtered = []
            for d in docs:
                ok = True
                for k, v in metadata_filters.items():
                    if str(d.get(k, "")).lower() != str(v).lower():
                        ok = False
                        break
                if ok:
                    filtered.append(d)
            docs = filtered or docs

        texts = [doc.get("text", "") for doc in docs]
        question_embedding = _embed_texts([question])[0]
        doc_embeddings = _embed_texts(texts)

        similarities = []
        for i, doc_embedding in enumerate(doc_embeddings):
            similarity = _cosine(question_embedding, doc_embedding)
            similarities.append((similarity, docs[i]))

        similarities.sort(key=lambda x: x[0], reverse=True)
        top_docs = similarities[:top_k]

        result_parts = []
        for similarity, doc in top_docs:
            table = doc.get("table", "")
            column = doc.get("column", "")
            text = doc.get("text", "")
            result_parts.append(f"Table: {table}, Column: {column} (similarity: {similarity:.3f})\n{text}")

        return "\n\n".join(result_parts)
    except Exception:
        return get_hybrid_relevant_schema_snippets(conn, question, top_k)


def _build_schema_docs(conn: sqlite3.Connection) -> List[Dict[str, str]]:
    """Build schema documents for retrieval"""
    docs = []
    cursor = conn.cursor()
    
    try:
        # Get all tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        
        for table in tables:
            table_name = table[0]
            
            # Skip system tables
            if table_name in ['sqlite_sequence']:
                continue
                
            # Get table info
            cursor.execute(f"PRAGMA table_info({table_name})")
            columns = cursor.fetchall()
            
            # Create document for each column
            for col in columns:
                col_name = col[1]
                col_type = col[2]
                is_pk = bool(col[5])
                pk_marker = " (PRIMARY KEY)" if is_pk else ""
                
                text = f"Column: {col_name} ({col_type}){pk_marker} in table {table_name}"
                docs.append({"table": table_name, "column": col_name, "type": col_type, "is_pk": str(is_pk), "text": text})
            
            # Also create a table-level document
            col_names = [col[1] for col in columns]
            table_text = f"Table: {table_name} with columns: {', '.join(col_names)}"
            docs.append({"table": table_name, "column": "*", "type": "table", "is_pk": "False", "text": table_text})
            
    except Exception as e:
        print(f"Error building schema docs: {e}")
    
    return docs
