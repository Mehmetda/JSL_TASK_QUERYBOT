# Agentic QueryBot (Task 3 – Streamlined)

A lightweight, production-oriented Natural Language → SQL → Answer system with Local LLM, hybrid schema RAG, security guardrails, structured logging, and a Streamlit UI. This codebase follows the interview task specs, focuses on SQLite (Postgres/Docker optional), and removes Ollama. Local LLM and OpenAI are supported with an Auto fallback.

---

## Key Features

- NL → SQL → Execute → Summarize pipeline
- Local LLM + OpenAI with Auto fallback; offline works with Local
- MCP-style provider abstraction (`app/services/provider.py`)
- Hybrid RAG over schema (dense + keyword, with optional metadata filters)
- Security guardrails:
  - Allow-list tables (from env)
  - Block DML/destructive ops; block multiple statements
  - Enforce ORDER BY when LIMIT is used
- Structured JSON logging with trace IDs
- Streamlit UI with mode selection, query history, stats, and JSON download
- Minimal Windows-safe smoke tests

---

## What's New

- NER-enhanced hybrid RAG integrated into `SQLAgent` flow for better schema retrieval
- Modular 3-layer agent architecture: `BaseAgent` + `SQLAgent` + prompt helpers
- Security hardening:
  - Table allow-list alias mapping (e.g., admissions → json_admissions)
  - Hard guard: Only `SELECT` statements allowed (blocks DML early)
  - SQLite validator updated to avoid duplicate LIMIT during syntax check
- Expanded tests:
  - Edge-case integration tests (`tests/test_edge_cases.py`)
  - English system prompt check (`tests/test_english_system_prompts.py`)

These changes improve reliability, security and determinism, and make the agent easier to extend.

---

## Repository Layout (selected)

```
app/
  __init__.py               # .env auto-loader
  main.py                   # end-to-end query pipeline
  agents/
    sql_agent.py            # LLM → SQL generation
    system_prompt.py        # schema RAG + hybrid retrieval helpers
  db/
    connection.py           # SQLite connection
  history/
    query_history.py        # history storage & export
  llm/
    local_llm_client.py     # transformers-based local client (with fallback)
    llm_manager.py          # OpenAI / Local / Auto
  security/
    table_allowlist.py      # table allow-list checks
  services/
    provider.py             # MCP-like service layer
  tools/
    sql_executor.py         # query execution
    sql_validator.py        # safety rules (LIMIT/ORDER BY, DML block, etc.)
    stats_tool.py           # optional column stats
  ui/
    streamlit_app.py        # Streamlit frontend
  utils/
    logger.py               # structured JSON logger
    internet_check.py       # online/OpenAI checks
    tracing.py              # trace IDs (optional)
logs/
  app.log                   # runtime logs
tests/
  test_structured_logging.py # minimal smoke test (Windows-safe)
```

---

## Requirements

- Python 3.9+
- Windows/Linux/macOS
- Recommended: virtualenv or conda

Install dependencies:

```bash
pip install -r requirements.txt
```

Note: `transformers` may download models on first use; ensure disk/RAM are sufficient. The local client falls back to a smaller model if needed.

---

## Configuration (.env)

The app loads `.env` automatically via `app/__init__.py` (optional). Supported keys:

- `OPENAI_API_KEY`           # optional; enables OpenAI mode and Auto fallback
- `ALLOWED_TABLES`           # comma-separated allow-list, e.g. `json_patients,json_admissions,...`

Example `.env`:

```
OPENAI_API_KEY=sk-...  # optional
ALLOWED_TABLES=json_patients,json_admissions,json_transfers,json_providers,json_lab,json_diagnoses,json_insurance,json_careunits
```

---

## Running the App

Streamlit UI:

```bash
cd JSL_TASK_2
streamlit run app/ui/streamlit_app.py
```

- LLM Mode selection in sidebar (Auto/OpenAI/Local)
- If internet is off, Auto falls back to Local automatically; use the Refresh status button to update the indicators
- After submitting a question:
  - SQL + answer are shown
  - Metadata (validation, tables, performance) available in expanders
  - “Download Response” provides JSON
  - Query history and statistics appear below results

CLI (optional):

```bash
cd JSL_TASK_2
python -c "from app.main import run_query_pipeline; print(run_query_pipeline('Kaç hasta var?'))"
```

---

## What’s Implemented vs Task 3

- Implemented
  - MCP-style provider abstraction (service layer)
  - Local LLM (offline) + Auto fallback
  - Hybrid schema RAG: dense (SentenceTransformer) + keyword, with metadata filters
  - Security: allow-list, DML/destructive block, multiple statement block, LIMIT requires ORDER BY
  - Observability: structured JSON logs + trace IDs
  - UI: query history, statistics, downloadable JSON response
  - .env based configuration
- Not included by design (can be added on request)
  - Postgres and Docker Compose setup
  - Persistent vector store (current approach is schema-centric hybrid retrieval)
  - Expanded test matrix; kept a minimal Windows-safe smoke test

---

## Example Questions (and expected output shape)

- “Kaç hasta var?”
  - SQL: `SELECT COUNT(*) ...`
  - Answer: “Toplam X hasta bulundu.”
  - Meta: `database.query_type=COUNT_QUERY`, `performance.execution_ms`, `results.row_count`
- “Son 30 günde kaç yatış var?”
  - SQL: `SELECT COUNT(*) FROM json_admissions WHERE admittime >= date('now','-30 days')`
  - Meta: validation passes; ORDER BY / LIMIT rules apply if used
- “Hangi bakım birimlerinde kaç transfer var?”
  - SQL: `SELECT careunit, COUNT(*) FROM json_transfers GROUP BY careunit`

These are examples; exact numbers depend on your dataset.

---

## Security Guardrails

- Only `SELECT` queries are allowed
- Forbidden keywords: `insert, update, delete, drop, alter, create, attach, pragma, vacuum, truncate, replace`
- Multiple statements (;) blocked
- `LIMIT` requires `ORDER BY`
- Table allow-list enforced via `ALLOWED_TABLES`

---

## Logging & Tracing

- Structured JSON logs written to `logs/app.log`
- Each pipeline run includes a `trace_id`
- Minimal smoke test: `python tests/test_structured_logging.py`

---

## Development Notes

- Local LLM
  - Uses `transformers` pipeline; falls back to `microsoft/DialoGPT-small` if the configured model cannot load
  - Token usage is approximate (based on tokenizer lengths)
- RAG
  - Schema documents are built from SQLite PRAGMA
  - Dense embeddings via `sentence-transformers/all-MiniLM-L6-v2` when available; else bag-of-words fallback
  - `get_hybrid_relevant_schema_snippets_with_metadata` supports filters such as `{ "table": "json_admissions" }`
- Provider Layer (`app/services/provider.py`)
  - Centralizes access to DB, Security, RAG, Logger, Tracing, and LLM manager

---

## Troubleshooting

- Streamlit shows “Connection error”
  - Check terminal for exceptions; large model load may exceed memory
  - Switch to Local Only or rely on fallback small model
- OpenAI unavailable
  - Ensure internet and `OPENAI_API_KEY`; otherwise use Local Only
- SQLite schema
  - Ensure the sample DB file exists under `app/db/`; adjust `connection.py` if needed

---

## Lightweight Testing

Run the minimal smoke test:

```bash
cd JSL_TASK_2
python tests/test_structured_logging.py
```

Optionally, you can add more tests under `tests/` following the same pattern.

---

## Roadmap (Optional Extensions)

- Postgres + Docker Compose (app + db + vector store)
- Persistent vector index (FAISS/Chroma)
- More comprehensive test suite
- Expanded UI (intermediate steps, assumptions panel)

---

## License

This repository is intended for interview evaluation. Licensing can be adapted to company policy.
