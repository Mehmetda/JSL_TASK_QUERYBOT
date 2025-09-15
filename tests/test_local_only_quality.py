import os
import unittest

from app.main import run_query_pipeline
from app.llm.llm_manager import get_llm_manager


class TestLocalOnlyQuality(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Force Local Only mode when possible
        os.environ.pop("OPENAI_API_KEY", None)
        cls.llm = get_llm_manager()
        try:
            cls.llm.set_mode("ollama")
        except Exception:
            pass

    def _ensure_local_available(self):
        if getattr(self.llm, "ollama_client", None) is None:
            self.skipTest("Local LLM (Ollama) not available on this machine.")

    def test_local_generates_sql_and_answer(self):
        self._ensure_local_available()
        resp = run_query_pipeline("How many admissions are there in table json_admissions?")
        self.assertTrue(resp.get("success"), msg=resp)
        self.assertTrue(resp.get("sql", "").lower().startswith("select"))
        meta = resp.get("meta", {})
        self.assertTrue(meta.get("validation", {}).get("is_valid", False), msg=resp)
        self.assertIsInstance(resp.get("answer", ""), str)
        self.assertGreater(len(resp.get("answer", "")), 0)

    def test_local_group_by_quality(self):
        self._ensure_local_available()
        resp = run_query_pipeline(
            "Admissions per insurance type from json_admissions, sorted by count desc"
        )
        self.assertTrue(resp.get("success"), msg=resp)
        sql = resp.get("sql", "").lower()
        self.assertTrue(sql.startswith("select"))
        self.assertIn("group by", sql)
        self.assertIn("order by", sql)


if __name__ == "__main__":
    unittest.main()


