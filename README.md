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
