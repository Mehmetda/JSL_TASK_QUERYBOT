"""
Dynamic System Prompt Generator for Medical QueryBot
"""
import sqlite3
from typing import Dict, List, Any
import re
import os
from openai import OpenAI

def get_database_schema_info(conn: sqlite3.Connection) -> str:
    """Get comprehensive database schema information"""
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
        
        # Format columns
        col_info = []
        for col in columns:
            col_name = col[1]
            col_type = col[2]
            is_pk = bool(col[5])
            pk_marker = " (PRIMARY KEY)" if is_pk else ""
            col_info.append(f"{col_name} ({col_type}){pk_marker}")
        
        schema_info.append(f"""
📋 {table_name} ({count} kayıt):
  - {', '.join(col_info)}""")
    
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

### İlişkisel Sorgular
- "Hangi hastalar birden fazla yatış yapmış?" → `SELECT subject_id, COUNT(*) FROM json_admissions GROUP BY subject_id HAVING COUNT(*) > 1`
- "Hangi doktorlar en çok hasta kabul etmiş?" → `SELECT admit_provider_id, COUNT(*) FROM json_admissions GROUP BY admit_provider_id ORDER BY COUNT(*) DESC`

## ⚠️ ÖNEMLİ KURALLAR

1. **Sadece SELECT sorguları** oluştur - INSERT, UPDATE, DELETE yasak
2. **Tek SQL statement** döndür - Birden fazla statement yasak
3. **Noktalı virgül kullanma** - SQL statement sonunda ; koyma
4. **Güvenli sorgular** yaz - SQL injection'a karşı dikkatli ol
5. **JOIN kullan** - İlişkili tabloları birleştir
6. **Türkçe cevap ver** - Kullanıcı Türkçe soruyorsa Türkçe yanıtla
7. **Anlamlı sonuçlar** döndür - Sadece sayı değil, açıklama da ekle
8. **Hata durumunda** - Veri bulunamazsa açık mesaj ver

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


# ---- Minimal RAG over schema: keyword-based top-K retriever ----

def _tokenize(text: str) -> List[str]:
    return re.findall(r"[a-zA-Z0-9_]+", text.lower())


def get_relevant_schema_snippets(conn: sqlite3.Connection, question: str, top_k: int = 3) -> str:
    """Select top-k tables/columns relevant to the question using simple token overlap.
    This is a lightweight alternative to embeddings for Task 2.
    """
    # Lightweight synonym expansion (TR -> EN/field hints)
    synonym_map = {
        "hasta": ["patient", "json_patients", "subject_id", "gender", "age", "anchor_age"],
        "yas": ["age", "anchor_age"],
        "yaş": ["age", "anchor_age"],
        "cinsiyet": ["gender"],
        "yatış": ["admission", "json_admissions", "hadm_id", "admission_type", "admittime", "dischtime"],
        "yatis": ["admission", "json_admissions", "hadm_id", "admission_type"],
        "yatış tipi": ["admission_type"],
        "doktor": ["provider", "json_providers", "admit_provider_id", "provider_id"],
        "personel": ["provider", "json_providers"],
        "transfer": ["transfer", "json_transfers", "careunit", "eventtype"],
        "bakim birimi": ["careunit"],
        "bakım birimi": ["careunit"],
        "servis": ["careunit"],
        "klinik": ["careunit"],
    }

    expanded = question.lower()
    for tr, hints in synonym_map.items():
        if tr in expanded:
            expanded += " " + " ".join(hints)

    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [r[0] for r in cursor.fetchall() if r[0] != 'sqlite_sequence']

    q_tokens = set(_tokenize(expanded))
    scored: List[tuple[str, int, List[str]]] = []

    for table in tables:
        cursor.execute(f"PRAGMA table_info({table})")
        cols = cursor.fetchall()
        col_names = [c[1] for c in cols]
        corpus = f"{table} " + " ".join(col_names)
        t_tokens = set(_tokenize(corpus))
        score = len(q_tokens & t_tokens)
        scored.append((table, score, col_names))

    scored.sort(key=lambda x: x[1], reverse=True)
    top = [s for s in scored[:top_k] if s[1] > 0] or scored[: min(top_k, len(scored))]

    parts: List[str] = []
    for table, _, col_names in top:
        try:
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            count = cursor.fetchone()[0]
        except Exception:
            count = 0
        parts.append(f"- Table: {table} ({count} rows)\n  Columns: {', '.join(col_names)}")

    return "\n".join(parts) if parts else "- (No specific relevant tables detected; use overall schema above)"


def get_contextual_system_prompt(conn: sqlite3.Connection, question: str) -> str:
    base = get_enhanced_system_prompt(conn)
    # Switchable: hybrid vs keyword-only
    use_hybrid = os.getenv("RAG_HYBRID", "0") == "1"
    if use_hybrid:
        relevant = get_hybrid_relevant_schema_snippets(conn, question, top_k=int(os.getenv("RAG_TOP_K", "3")))
    else:
        relevant = get_relevant_schema_snippets(conn, question, top_k=int(os.getenv("RAG_TOP_K", "3")))
    return f"{base}\n\n## 🔎 İlgili Şema (Soruya göre)\n{relevant}\n\nYukarıdaki ilgili şemayı kullanarak tek ve güvenli bir SELECT sorgusu üret."


# ---- Hybrid RAG (semantic + keyword) over schema ----

def _build_schema_docs(conn: sqlite3.Connection) -> List[Dict[str, str]]:
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [r[0] for r in cursor.fetchall() if r[0] != 'sqlite_sequence']
    docs: List[Dict[str, str]] = []
    for table in tables:
        cursor.execute(f"PRAGMA table_info({table})")
        cols = cursor.fetchall()
        for col in cols:
            col_name = col[1]
            col_type = col[2]
            text = f"table: {table} | column: {col_name} | type: {col_type}"
            docs.append({"table": table, "column": col_name, "text": text})
        # Also a table-level doc
        texts = ", ".join([c[1] for c in cols])
        docs.append({"table": table, "column": "*", "text": f"table: {table} | columns: {texts}"})
    return docs


def _embed_texts(texts: List[str]) -> List[List[float]]:
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    model = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")
    # Batch embed
    res = client.embeddings.create(model=model, input=texts)
    return [d.embedding for d in res.data]


def _cosine(a: List[float], b: List[float]) -> float:
    import math
    dot = sum(x*y for x, y in zip(a, b))
    na = math.sqrt(sum(x*x for x in a))
    nb = math.sqrt(sum(x*x for x in b))
    if na == 0 or nb == 0:
        return 0.0
    return dot / (na * nb)


def get_hybrid_relevant_schema_snippets(conn: sqlite3.Connection, question: str, top_k: int = 3) -> str:
    """Hybrid retrieval: semantic (embeddings) + keyword/metadata scoring."""
    # Build docs
    docs = _build_schema_docs(conn)
    if not docs:
        return get_relevant_schema_snippets(conn, question, top_k)

    # Semantic scores
    try:
        q_emb = _embed_texts([question])[0]
        doc_embs = _embed_texts([d["text"] for d in docs])
        sem_scores = [_cosine(q_emb, e) for e in doc_embs]
    except Exception:
        # Fallback to keyword-only on embedding error
        return get_relevant_schema_snippets(conn, question, top_k)

    # Keyword/metadata score (reuse tokenizer + synonyms)
    synonym_text = question.lower()
    # reuse synonym_map from earlier function by light expansion
    # (avoid ref duplication: call get_relevant_schema_snippets to expand)
    expanded_snippet = get_relevant_schema_snippets(conn, question, top_k=0)  # returns guidance text; we won't use
    q_tokens = set(_tokenize(synonym_text))

    kw_scores: List[int] = []
    for d in docs:
        t_tokens = set(_tokenize(d["text"]))
        kw_scores.append(len(q_tokens & t_tokens))

    alpha = float(os.getenv("RAG_ALPHA", "0.7"))
    combined = [(i, alpha*sem_scores[i] + (1-alpha)*(kw_scores[i] > 0)) for i in range(len(docs))]
    combined.sort(key=lambda x: x[1], reverse=True)

    # Aggregate by table, keep best per table
    table_best: Dict[str, float] = {}
    for idx, sc in combined:
        tb = docs[idx]["table"]
        if tb not in table_best:
            table_best[tb] = sc
        if len(table_best) >= max(top_k, 1):
            # we still continue but limit will apply on formatting
            pass

    # Format top-k tables with columns
    ranked_tables = sorted(table_best.items(), key=lambda x: x[1], reverse=True)[:top_k]
    out_lines: List[str] = []
    cursor = conn.cursor()
    for tb, _ in ranked_tables:
        try:
            cursor.execute(f"SELECT COUNT(*) FROM {tb}")
            count = cursor.fetchone()[0]
        except Exception:
            count = 0
        cursor.execute(f"PRAGMA table_info({tb})")
        cols = cursor.fetchall()
        col_names = [c[1] for c in cols]
        out_lines.append(f"- Table: {tb} ({count} rows)\n  Columns: {', '.join(col_names)}")
    return "\n".join(out_lines) if out_lines else get_relevant_schema_snippets(conn, question, top_k)
