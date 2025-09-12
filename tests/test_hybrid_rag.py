"""
Test hybrid RAG (embedding + keyword) vs keyword-only on schema retrieval.

Run:
  python tests/test_hybrid_rag.py
Requires:
  - OPENAI_API_KEY in env
  - EMBEDDING_MODEL (optional, defaults to text-embedding-3-small)
"""
import os
import sys
from pathlib import Path

# Add project root to Python path
CURRENT = Path(__file__).resolve().parent
PROJECT_ROOT = CURRENT.parent
sys.path.insert(0, str(PROJECT_ROOT))

from app.db.connection import get_connection
from app.agents.system_prompt import (
    get_relevant_schema_snippets,
    get_hybrid_relevant_schema_snippets,
)


QUESTIONS = [
    "Cinsiyete göre hasta sayıları nedir?",
    "Yatış tiplerine göre dağılım nedir?",
    "Bakım birimlerine göre transfer sayıları?",
    "En çok hasta kabul eden doktorlar?",
]


def main() -> None:
    print("OPENAI_MODEL:", os.getenv("EMBEDDING_MODEL", "text-embedding-3-small"))
    with get_connection() as conn:
        for q in QUESTIONS:
            print("\nQ:", q)
            kw = get_relevant_schema_snippets(conn, q, top_k=3)
            print("--- Keyword-only ---\n" + kw)
            try:
                hy = get_hybrid_relevant_schema_snippets(conn, q, top_k=3)
            except Exception as e:
                hy = f"(Hybrid error: {e})"
            print("--- Hybrid (semantic+keyword) ---\n" + hy)
            print("=" * 80)


if __name__ == "__main__":
    main()
