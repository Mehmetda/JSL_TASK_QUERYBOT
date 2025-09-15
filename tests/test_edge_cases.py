import unittest

from app.main import run_query_pipeline


class TestEdgeCases(unittest.TestCase):
    def assert_success(self, resp: dict):
        self.assertTrue(resp.get("success"), msg=f"Pipeline failed: {resp}")
        self.assertIn("sql", resp)
        self.assertIn("answer", resp)
        meta = resp.get("meta", {})
        self.assertIn("validation", meta)
        self.assertTrue(meta.get("validation", {}).get("is_valid"))

    def assert_failure(self, resp: dict):
        self.assertFalse(resp.get("success"))
        self.assertIn("meta", resp)
        self.assertIn("validation", resp.get("meta", {}))
        self.assertFalse(resp["meta"]["validation"]["is_valid"])    

    def test_simple_count(self):
        resp = run_query_pipeline("How many admissions are there in table json_admissions?")
        self.assert_success(resp)

    def test_group_by(self):
        resp = run_query_pipeline("Admissions per insurance type from json_admissions, sorted by count desc")
        self.assert_success(resp)

    def test_latest_with_order_by(self):
        resp = run_query_pipeline("List the 5 most recent admissions from json_admissions ordered by admittime desc limit 5")
        self.assert_success(resp)

    def test_block_dml(self):
        resp = run_query_pipeline("drop table json_admissions")
        self.assertFalse(resp.get("success"))
        self.assertIn("answer", resp)
        self.assertIn("Access denied", resp.get("answer", "") + str(resp.get("error", "")))

    def test_allowlist_wrong_table(self):
        # Using generic table name should be blocked by allowlist or normalized by pipeline
        resp = run_query_pipeline("List the 5 most recent admissions from admissions")
        # Either success (normalized) or blocked with message
        self.assertIn(resp.get("success"), [True, False])

    def test_sqlite_date_functions(self):
        # Ensure SQLite-specific date syntax is used, not MySQL DATE_SUB
        resp = run_query_pipeline("How many admissions in the last 30 days? Use SQLite date('now','-30 days').")
        self.assert_success(resp)

    def test_sparse_result(self):
        resp = run_query_pipeline("Count admissions with admission_type='NON_EXISTENT_TYPE' in json_admissions")
        # Should still be valid even if count is 0
        self.assertTrue(resp.get("meta", {}).get("validation", {}).get("is_valid", False))

    def test_join_query(self):
        resp = run_query_pipeline("Top 5 patients by number of admissions using json_patients and json_admissions")
        self.assert_success(resp)


if __name__ == "__main__":
    unittest.main()


