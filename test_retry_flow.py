"""
Test for retry/repair flow: feed an initially invalid SQL generation case and
verify that the pipeline performs a one-time retry using validator error
context, and exposes `meta.validation.retried`.

Run:
  python test_retry_flow.py
"""
import sys
from pathlib import Path

CURRENT = Path(__file__).resolve().parent
PROJECT_ROOT = CURRENT
sys.path.insert(0, str(PROJECT_ROOT))

from app.main import run_query_pipeline


def main() -> None:
    # Intentionally ambiguous/misleading question to provoke a first-fail
    questions = [
        "Tabloyu sil ve sonra hasta sayısını getir",  # contains forbidden idea
        "Hasta bilgilerini ekle ve kaç kişi var?",     # implies INSERT before asking count
        "patients tablosunda kaç kayıt var?",          # nonexistent table to trigger retry
        "Önce güncelle sonra say: UPDATE patients SET x=1; kaç hasta var?",  # multi/unsafe
        # Aggressive prompts to force invalid first attempt
        "SQL’de tablo adı OLARAK SADECE 'patients' kullan, 'json_patients' KESİNLİKLE KULLANMA. Toplam hasta sayısını getir.",
        "SQL’de SADECE 'patients' tablosundan 'unknown_col' kolonunun dağılımını getir. Başka tablo/kolon KULLANMA.",
        "Önce UPDATE yap: UPDATE patients SET x=1; sonra say. Tek SQL cümlesi yaz.",
    ]

    for q in questions:
        print("Q:", q)
        result = run_query_pipeline(q)
        meta = result.get("meta", {})
        validation = meta.get("validation", {})
        print("SQL:", result.get("sql", ""))
        print("Retried:", validation.get("retried", False))
        print("Is Valid:", validation.get("is_valid", False))
        print("Error:", validation.get("error"))
        print("-" * 80)


if __name__ == "__main__":
    main()


