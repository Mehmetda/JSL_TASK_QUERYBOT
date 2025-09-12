"""
Quick test script for minimal RAG (keyword top-K schema) and prompt integration.

Run:
  python tests/test_rag_schema.py
"""
import sys
from pathlib import Path

# Add project root to Python path
CURRENT = Path(__file__).resolve().parent
PROJECT_ROOT = CURRENT.parent
sys.path.insert(0, str(PROJECT_ROOT))

from app.db.connection import get_connection
from app.agents.system_prompt import get_relevant_schema_snippets
from app.main import run_query_pipeline


QUESTIONS = [
    "Cinsiyete göre hasta sayıları nedir?",
    "Yatış tiplerine göre dağılım nedir?",
    "Bakım birimlerine göre transfer sayıları?",
    "En çok hasta kabul eden doktorlar?",
]


def main() -> None:
    with get_connection() as conn:
        print("=== Minimal RAG Relevant Schema (top-k) ===\n")
        for q in QUESTIONS:
            snippet = get_relevant_schema_snippets(conn, q, top_k=3)
            print(f"Q: {q}")
            print("Relevant Schema:\n" + snippet)
            print("-" * 60)

    print("\n=== Full Pipeline Check (SQL + Meta) ===\n")
    for q in QUESTIONS:
        result = run_query_pipeline(q)
        db_meta = result.get("meta", {}).get("database", {})
        print(f"Q: {q}")
        print("SQL:\n" + result.get("sql", ""))
        print("Tables Used:", db_meta.get("tables_used", []))
        print("Relevant Schema (from meta):\n" + str(db_meta.get("relevant_schema", "")))
        print("Exec Time (ms):", result.get("meta", {}).get("performance", {}).get("execution_ms", "N/A"))
        print("=" * 80)


if __name__ == "__main__":
    main()
