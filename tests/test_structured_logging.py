"""
Minimal structured logging smoke test

Run:
  python tests/test_structured_logging.py
"""
import sys
from pathlib import Path
import json
import os

# Add project root to Python path
CURRENT = Path(__file__).resolve().parent
PROJECT_ROOT = CURRENT.parent
sys.path.insert(0, str(PROJECT_ROOT))

from app.utils.logger import StructuredLogger, generate_trace_id


def test_minimal_logging():
    print("Testing minimal structured logging...")
    try:
        os.makedirs("logs", exist_ok=True)
        log_file = os.path.join("logs", "test_structured_minimal.log")

        logger = StructuredLogger(log_file)
        trace_id = generate_trace_id()

        # Write two basic structured entries
        logger.log_query_start(trace_id, "Test question", "user123")
        logger.log_query_end(trace_id, True, 123, 7)

        # Flush to disk
        for h in logger.logger.handlers:
            try:
                h.flush()
            except Exception:
                pass

        assert os.path.exists(log_file)
        with open(log_file, "r") as f:
            lines = [ln.strip() for ln in f.readlines() if ln.strip()]
            assert len(lines) >= 2
            first = json.loads(lines[0])
            second = json.loads(lines[1])
            assert first.get("event") == "query_start"
            assert second.get("event") == "query_end"
            assert first.get("trace_id") == trace_id == second.get("trace_id")

        print("✅ Minimal structured logging works")
        return True
    except Exception as e:
        print(f"❌ Minimal logging failed: {e}")
        return False


def main():
    print("🧪 Testing Structured JSON Logging (Minimal)")
    print("=" * 50)
    ok = test_minimal_logging()
    print("=" * 50)
    if ok:
        print("🎉 All structured logging tests passed!")
        return True
    else:
        print("❌ Some tests failed")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
