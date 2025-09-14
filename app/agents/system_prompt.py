"""
Dynamic System Prompt Generator for Medical QueryBot
"""
import sqlite3
from typing import Dict, List, Any, Optional
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
    
    system_prompt = f"""You are a medical database expert working with SQLite databases. You are designed to convert natural language questions into SQL queries for medical data analysis.

## 🏥 DATABASE SCHEMA

{schema_info}

## 🔗 TABLE RELATIONSHIPS

- **json_patients** ↔ **json_admissions**: Connected by subject_id
- **json_admissions** ↔ **json_transfers**: Connected by hadm_id  
- **json_admissions** ↔ **json_providers**: Connected by admit_provider_id
- **json_patients** ↔ **json_transfers**: Connected by subject_id

## 📊 DATA TYPES AND DESCRIPTIONS

### Patient Information (json_patients)
- **subject_id**: Unique patient identifier
- **gender**: Gender (M/F)
- **anchor_age**: Age
- **anchor_year**: Reference year
- **dod**: Date of death (if applicable)

### Admission Information (json_admissions)  
- **hadm_id**: Unique admission identifier
- **admittime**: Admission time
- **dischtime**: Discharge time
- **admission_type**: Type of admission (EMERGENCY, ELECTIVE, etc.)
- **admission_location**: Admission location
- **discharge_location**: Discharge location
- **insurance**: Insurance information
- **race**: Race information
- **marital_status**: Marital status

### Transfer Information (json_transfers)
- **transfer_id**: Unique transfer identifier
- **eventtype**: Transfer type (admit, transfer, discharge)
- **careunit**: Care unit
- **intime**: Entry time
- **outtime**: Exit time

### Healthcare Providers (json_providers)
- **provider_id**: Provider identifier
- **npi**: National Provider Identifier
- **dea**: DEA number

## 🎯 QUERY TYPES AND EXAMPLES

### Count Queries
- "How many patients are there?" → `SELECT COUNT(*) FROM json_patients`
- "How many admissions are there?" → `SELECT COUNT(*) FROM json_admissions`
- "How many transfers are there?" → `SELECT COUNT(*) FROM json_transfers`

### Demographic Queries
- "What is the age distribution of patients?" → `SELECT anchor_age, COUNT(*) FROM json_patients GROUP BY anchor_age`
- "What is the gender distribution?" → `SELECT gender, COUNT(*) FROM json_patients GROUP BY gender`
- "How many patients by race?" → `SELECT race, COUNT(*) FROM json_admissions GROUP BY race`

### Admission Queries
- "How many emergency admissions?" → `SELECT COUNT(*) FROM json_admissions WHERE admission_type = 'EMERGENCY'`
- "How many patients by admission location?" → `SELECT admission_location, COUNT(*) FROM json_admissions GROUP BY admission_location`
- "Distribution by insurance type?" → `SELECT insurance, COUNT(*) FROM json_admissions GROUP BY insurance`

### Transfer Queries
- "How many transfers by care unit?" → `SELECT careunit, COUNT(*) FROM json_transfers GROUP BY careunit`
- "Distribution by transfer type?" → `SELECT eventtype, COUNT(*) FROM json_transfers GROUP BY eventtype`

### Time-based Queries
- "How many admissions in the last 30 days?" → `SELECT COUNT(*) FROM json_admissions WHERE admittime >= date('now', '-30 days')`
- "How many patients in 2024?" → `SELECT COUNT(*) FROM json_admissions WHERE strftime('%Y', admittime) = '2024'`
- "What was the last admission?" → `SELECT admittime, dischtime, admission_type FROM json_admissions ORDER BY admittime DESC LIMIT 1`
- "Show the 5 most recent admissions" → `SELECT admittime, dischtime, admission_type FROM json_admissions ORDER BY admittime DESC LIMIT 5`

### Relational Queries
- "Which patients have multiple admissions?" → `SELECT subject_id, COUNT(*) FROM json_admissions GROUP BY subject_id HAVING COUNT(*) > 1`
- "Which providers have the most patients?" → `SELECT admit_provider_id, COUNT(*) FROM json_admissions GROUP BY admit_provider_id ORDER BY COUNT(*) DESC`

## ⚠️ IMPORTANT RULES - DATA SECURITY

1. **ONLY SELECT queries** - INSERT, UPDATE, DELETE, DROP, ALTER, CREATE, TRUNCATE, REPLACE are FORBIDDEN
2. **Single SQL statement** - Multiple statements are forbidden
3. **No semicolon** - Don't add ; at the end of SQL statements
4. **Safe queries** - Be careful against SQL injection
5. **Use JOINs** - Connect related tables
6. **English responses** - Always respond in English unless specifically asked for another language
7. **Meaningful results** - Don't just return numbers, add explanations
8. **Error handling** - Give clear messages when no data is found
9. **ORDER BY required with LIMIT** - If using LIMIT, always add ORDER BY
10. **Numeric/date columns for ORDER BY** - ORDER BY requires INTEGER, REAL, DATE, DATETIME columns
11. **No LIMIT without ORDER BY** - Don't use LIMIT if no suitable numeric/date column for ORDER BY
12. **Latest/newest queries** - Use ORDER BY ... DESC LIMIT 1 for latest/newest (only with numeric/date columns)
13. **Schema analysis** - Check ORDER BY suitable columns for each table
14. **NO DATA MODIFICATION** - Never insert, delete, or update data
15. **READ ONLY** - Only read and report existing data

## 🔍 QUESTION ANALYSIS

Analyze the user's question:
1. **Main topic**: Patient, admission, transfer, provider?
2. **Query type**: Count, distribution, filtering, relationship?
3. **Time range**: Specific date, period?
4. **Grouping**: Group by which field?
5. **Sorting**: Sort by which criteria?

## 📝 EXAMPLE OUTPUT FORMAT

```sql
-- User question: "How many male patients are there?"
SELECT 
    gender,
    COUNT(*) as patient_count
FROM json_patients 
WHERE gender = 'M'
GROUP BY gender
```

Use this system prompt to convert users' natural language questions into correct SQL queries and produce meaningful results."""

    return system_prompt

def get_enhanced_system_prompt(conn: sqlite3.Connection) -> str:
    """Get enhanced system prompt with additional context"""
    base_prompt = generate_system_prompt(conn)
    
    # Add additional context
    enhanced_prompt = f"""{base_prompt}

## 🚀 ADVANCED FEATURES

### Smart Assumptions
- When user says "patient" → json_patients table
- When user says "admission" → json_admissions table  
- When user says "transfer" → json_transfers table
- When user says "doctor/provider" → json_providers table

### Multi-language Support
- patient → patient
- admission → admission
- transfer → transfer
- doctor → provider
- age → age
- gender → gender
- admission location → admission_location
- discharge location → discharge_location

### Common Error Corrections
- "hospital" → use admission_location (not in database)
- "clinic" → careunit 
- "service" → careunit
- "department" → careunit

Use this information to convert user questions into the most accurate SQL queries."""

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


def get_ner_enhanced_hybrid_schema_snippets(
    conn: sqlite3.Connection, 
    question: str, 
    top_k: int = 3,
    language_code: str = "tr"
) -> str:
    """
    Get relevant schema snippets using NER-enhanced hybrid approach
    
    This function:
    1. Extracts entities from the question using NER
    2. Uses entities to create metadata filters for more targeted retrieval
    3. Combines semantic similarity with entity-based filtering
    4. Enhances retrieval with domain-specific terms and IDs
    
    Args:
        conn: Database connection
        question: User question
        top_k: Number of top relevant snippets to return
        language_code: Language code for NER processing
        
    Returns:
        Relevant schema snippets as string with NER context
    """
    try:
        # Import NER components
        from app.tools.ner_filter import SpaCyNERProvider, build_system_context_block
        
        # Extract entities using NER (default to English)
        ner = SpaCyNERProvider(language_code=language_code or "en")
        ner_result = ner.filter_and_deidentify(question)
        
        # Create metadata filters from extracted entities
        metadata_filters = _create_metadata_filters_from_entities(ner_result.desired_entities)
        
        # Get schema documents
        docs = _build_schema_docs(conn)
        if not docs:
            return "No schema information available."
        
        # Apply entity-based metadata filtering
        if metadata_filters:
            filtered_docs = _apply_metadata_filters(docs, metadata_filters)
            # If we have filtered results, use them; otherwise use all docs
            docs = filtered_docs if filtered_docs else docs
        
        # Extract texts for embedding
        texts = [doc.get("text", "") for doc in docs]
        
        # Enhance question with domain terms for better semantic matching
        enhanced_question = _enhance_question_with_domain_terms(question, ner_result.desired_entities)
        
        # Get embeddings
        question_embedding = _embed_texts([enhanced_question])[0]
        doc_embeddings = _embed_texts(texts)
        
        # Calculate similarities
        similarities = []
        for i, doc_embedding in enumerate(doc_embeddings):
            similarity = _cosine(question_embedding, doc_embedding)
            similarities.append((similarity, docs[i]))
        
        # Sort by similarity and take top_k
        similarities.sort(key=lambda x: x[0], reverse=True)
        top_docs = similarities[:top_k]
        
        # Format results with NER context
        result_parts = []
        
        # Add NER context header
        entity_context = build_system_context_block(ner_result.desired_entities)
        if entity_context and entity_context != "None":
            result_parts.append(f"## Extracted Entities and Domain Terms:\n{entity_context}\n")
        
        # Add schema snippets
        for similarity, doc in top_docs:
            table = doc.get("table", "")
            column = doc.get("column", "")
            text = doc.get("text", "")
            result_parts.append(f"Table: {table}, Column: {column} (similarity: {similarity:.3f})\n{text}")
        
        return "\n\n".join(result_parts)
        
    except Exception as e:
        print(f"Error getting NER-enhanced hybrid schema snippets: {e}")
        # Fallback to regular hybrid approach
        return get_hybrid_relevant_schema_snippets(conn, question, top_k)


def _create_metadata_filters_from_entities(entities: List[Dict[str, str]]) -> Optional[Dict[str, str]]:
    """
    Create metadata filters from NER entities for targeted schema retrieval
    
    Args:
        entities: List of extracted entities from NER
        
    Returns:
        Dictionary of metadata filters or None
    """
    if not entities:
        return None
    
    filters = {}
    table_priority = []
    
    # Enhanced entity mapping with comprehensive medical domain coverage
    entity_mapping = {
        "PERSON": {
            "columns": ["subject_id", "admit_provider_id", "discharge_provider_id"],
            "tables": ["json_patients", "json_admissions", "json_providers"],
            "priority": 1
        },
        "ORG": {
            "columns": ["admission_location", "discharge_location", "careunit"],
            "tables": ["json_admissions", "json_transfers"],
            "priority": 2
        },
        "GPE": {
            "columns": ["admission_location", "discharge_location"],
            "tables": ["json_admissions"],
            "priority": 3
        },
        "DATE": {
            "columns": ["admittime", "dischtime", "deathtime", "intime", "outtime"],
            "tables": ["json_admissions", "json_transfers"],
            "priority": 2
        },
        "TIME": {
            "columns": ["admittime", "dischtime", "intime", "outtime"],
            "tables": ["json_admissions", "json_transfers"],
            "priority": 2
        },
        "CARDINAL": {
            "columns": ["age", "anchor_age", "hospital_expire_flag"],
            "tables": ["json_patients", "json_admissions"],
            "priority": 1
        },
        "ORDINAL": {
            "columns": ["admission_type", "insurance", "marital_status"],
            "tables": ["json_admissions"],
            "priority": 2
        },
        "MONEY": {
            "columns": ["insurance"],
            "tables": ["json_admissions"],
            "priority": 3
        },
        "PERCENT": {
            "columns": ["hospital_expire_flag"],
            "tables": ["json_admissions"],
            "priority": 3
        },
        "SUBJECT_ID": {
            "columns": ["subject_id"],
            "tables": ["json_patients", "json_admissions", "json_transfers"],
            "priority": 1
        },
        "HADM_ID": {
            "columns": ["hadm_id"],
            "tables": ["json_admissions", "json_transfers"],
            "priority": 1
        },
        "PROVIDER_ID": {
            "columns": ["admit_provider_id", "discharge_provider_id"],
            "tables": ["json_admissions", "json_providers"],
            "priority": 2
        },
        "DOMAIN_TERM": {
            "columns": ["admission_type", "careunit", "insurance"],
            "tables": ["json_admissions", "json_transfers"],
            "priority": 2
        }
    }
    
    # Process entities and build comprehensive filters
    for entity in entities:
        label = entity.get("label", "").upper()
        value = entity.get("value", "").lower()
        
        if label in entity_mapping:
            mapping = entity_mapping[label]
            
            # Add table priority
            for table in mapping["tables"]:
                if table not in [t[0] for t in table_priority]:
                    table_priority.append((table, mapping["priority"]))
            
            # Add column-specific filters with entity context
            for column in mapping["columns"]:
                if column not in filters:
                    filters[column] = value
                else:
                    # Combine multiple values for the same column
                    if isinstance(filters[column], list):
                        filters[column].append(value)
                    else:
                        filters[column] = [filters[column], value]
    
    # Sort tables by priority and select the most relevant ones
    if table_priority:
        table_priority.sort(key=lambda x: x[1])
        top_tables = [table for table, _ in table_priority[:3]]  # Top 3 tables
        filters["tables"] = top_tables
    
    # Add entity context for better retrieval
    filters["entity_context"] = {
        "entities": entities,
        "entity_count": len(entities),
        "entity_types": list(set([e.get("label", "") for e in entities]))
    }
    
    return filters if filters else None


def _apply_metadata_filters(docs: List[Dict[str, str]], filters: Dict[str, str]) -> List[Dict[str, str]]:
    """
    Apply metadata filters to schema documents with enhanced matching
    
    Args:
        docs: List of schema documents
        filters: Dictionary of metadata filters
        
    Returns:
        Filtered list of documents
    """
    if not filters:
        return docs
    
    filtered = []
    
    for doc in docs:
        match_score = 0
        total_checks = 0
        
        # Check table filters
        if "tables" in filters:
            total_checks += 1
            doc_table = doc.get("table", "").lower()
            filter_tables = [t.lower() for t in filters["tables"]]
            if any(table in doc_table for table in filter_tables):
                match_score += 1
        
        # Check column filters
        for key, value in filters.items():
            if key in ["tables", "entity_context"]:
                continue
                
            total_checks += 1
            if key in doc:
                doc_value = str(doc[key]).lower()
                filter_value = str(value).lower()
                
                # Enhanced matching logic
                if isinstance(value, list):
                    # Multiple values for the same column
                    if any(v.lower() in doc_value for v in value):
                        match_score += 1
                else:
                    # Single value matching
                    if filter_value in doc_value or doc_value in filter_value:
                        match_score += 1
            else:
                # Check if the filter key matches any column name
                doc_columns = [str(v).lower() for v in doc.values()]
                if any(key.lower() in col for col in doc_columns):
                    match_score += 1
        
        # Include document if it matches at least 50% of the criteria
        if total_checks > 0 and (match_score / total_checks) >= 0.5:
            # Add match score to document for ranking
            doc["match_score"] = match_score / total_checks
            filtered.append(doc)
    
    # Sort by match score for better ranking
    filtered.sort(key=lambda x: x.get("match_score", 0), reverse=True)
    
    return filtered


def _enhance_question_with_domain_terms(question: str, entities: List[Dict[str, str]]) -> str:
    """
    Enhance the question with domain terms for better semantic matching
    
    Args:
        question: Original question
        entities: Extracted entities from NER
        
    Returns:
        Enhanced question with domain context
    """
    if not entities:
        return question
    
    # Extract domain terms and IDs with enhanced categorization
    domain_terms = []
    medical_terms = []
    temporal_terms = []
    numeric_terms = []
    id_terms = []
    
    for entity in entities:
        label = entity.get("label", "").upper()
        value = entity.get("value", "")
        
        if label == "DOMAIN_TERM":
            medical_terms.append(value)
        elif label in ["SUBJECT_ID", "HADM_ID", "PROVIDER_ID"]:
            id_terms.append(f"{label.lower()}: {value}")
        elif label in ["DATE", "TIME", "ADMITTIME", "DISCHTIME"]:
            temporal_terms.append(f"{label.lower()}: {value}")
        elif label in ["CARDINAL", "ORDINAL", "MONEY", "PERCENT"]:
            numeric_terms.append(f"{label.lower()}: {value}")
        elif label in ["PERSON", "ORG", "GPE"]:
            medical_terms.append(f"{label.lower()}: {value}")
    
    # Build enhanced question with structured context
    enhanced_parts = [question]
    
    if medical_terms:
        enhanced_parts.append(f"Medical entities: {', '.join(medical_terms)}")
    
    if id_terms:
        enhanced_parts.append(f"Database IDs: {', '.join(id_terms)}")
    
    if temporal_terms:
        enhanced_parts.append(f"Temporal context: {', '.join(temporal_terms)}")
    
    if numeric_terms:
        enhanced_parts.append(f"Numeric values: {', '.join(numeric_terms)}")
    
    # Add medical domain synonyms for better semantic matching
    medical_synonyms = []
    question_lower = question.lower()
    
    if any(term in question_lower for term in ["patient", "hasta", "person"]):
        medical_synonyms.extend(["patient", "subject", "individual"])
    
    if any(term in question_lower for term in ["admission", "yatış", "hospital"]):
        medical_synonyms.extend(["admission", "hospitalization", "stay"])
    
    if any(term in question_lower for term in ["doctor", "doktor", "provider"]):
        medical_synonyms.extend(["provider", "physician", "doctor", "clinician"])
    
    if any(term in question_lower for term in ["age", "yaş", "old"]):
        medical_synonyms.extend(["age", "years", "demographics"])
    
    if any(term in question_lower for term in ["gender", "cinsiyet", "sex"]):
        medical_synonyms.extend(["gender", "sex", "demographics"])
    
    if medical_synonyms:
        enhanced_parts.append(f"Medical synonyms: {', '.join(set(medical_synonyms))}")
    
    if len(enhanced_parts) > 1:
        return "\n\n".join(enhanced_parts)
    
    return question
