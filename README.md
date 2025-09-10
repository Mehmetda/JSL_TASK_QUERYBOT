# Medical QueryBot - Task 1

A Natural Language to SQL to Answer system for medical data queries.

## Features
- Natural language question processing
- SQL query generation using LLM
- SQLite database integration
- Streamlit web interface
 - Safe SQL validation (SELECT-only, single statement)
 - ETL to ingest JSON/CSV into SQLite
 - JSON response with metadata
 - Minimal/Hybrid RAG (keyword + optional embeddings)
 - Retry/repair on SQL validation failure
 - Execution time metrics and detailed metadata

## Setup
1) Dependencies
```bash
pip install -r requirements.txt
```

2) Environment
Create `.env` from the example and fill values:
```bash
copy .env.example .env   # Windows
# or
cp .env.example .env     # macOS/Linux
```
Edit `.env`:
```
OPENAI_API_KEY=sk-...
DB_PATH=E:\JSL_TASK_1\app\db\demo.sqlite
```

3) Ingest data (one-time)
```bash
python run_etl.py
```

4) Run UI
```bash
streamlit run app/ui/streamlit_app.py
```

## Usage
Ask medical questions in natural language and get SQL-generated answers.

Example questions:
- Kaç hasta var?
- Cinsiyete göre hasta sayıları nedir?
- Son 7 günde kaç yatış yapılmış?

Response shape:
```json
{ "sql": "...", "answer": "...", "meta": { "results": {"row_count": 12, "columns": ["col1", "col2"]}, "validation": {"is_valid": true}, "database": {"tables_used": ["JSON_PATIENTS"], "query_type": "COUNT_QUERY", "complexity": "SIMPLE"} } }
```

## Docker (optional)
Build and run:
```bash
docker build -t medical-querybot .
docker run --env-file .env -p 8501:8501 medical-querybot
```

## Task 2 Enhancements (kept simple)
- Minimal RAG (keyword + TR→EN mapping) for schema context
- Optional Hybrid RAG (embeddings + keyword) via environment flags
- Retry/repair: if SQL validation fails, one guided regeneration
- Observability: execution time (ms), validation status, tables used
- UI shows: Relevant Schema, Exec Time (ms), Retry banner

### Environment flags
Add to `.env` as needed:
```
# Hybrid RAG (optional)
RAG_HYBRID=1                 # 1: use embeddings+keyword, 0: keyword-only
RAG_TOP_K=3                  # how many schema snippets to include
RAG_ALPHA=0.7                # semantic score weight (0..1)
EMBEDDING_MODEL=text-embedding-3-small

# LLM controls (optional)
OPENAI_MODEL=gpt-3.5-turbo
OPENAI_TEMPERATURE=0.1
```

### Tests
Quick scripts to validate behavior:
```bash
# Relevant schema (RAG) and full pipeline check
python test_rag_schema.py

# Retry/repair flow (should show Retried: True for at least one case)
python test_retry_flow.py

# Hybrid vs keyword-only retrieval (requires OPENAI_API_KEY)
python test_hybrid_rag.py
```

### Notes
- Postgres + vector store are optional for Task 2; SQLite + minimal Hybrid RAG is sufficient.
- If Hybrid RAG is disabled (`RAG_HYBRID=0`), keyword-only retrieval is used as fallback.
