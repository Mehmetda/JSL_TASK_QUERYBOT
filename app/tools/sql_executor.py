"""
SQL execution module
"""
import sqlite3
from typing import List, Tuple, Any

FORBIDDEN = ("insert", "update", "delete", "drop", "alter", "create", "attach", "pragma", "vacuum")


def is_safe_select(sql: str) -> bool:
    """Check if SQL is a safe SELECT query"""
    q = sql.strip().lower()
    if not q.startswith("select"):
        return False
    return not any(word in q for word in FORBIDDEN)


def execute_sql(conn: sqlite3.Connection, sql: str) -> Tuple[List[Tuple[Any, ...]], dict]:
    """Execute safe SELECT SQL query"""
    if not is_safe_select(sql):
        raise ValueError("Only safe SELECT queries are allowed.")
    
    # Final defensive normalization for common table/column typos
    try:
        import re
        normalizations = {
            # tables
            "json_admissionss": "json_admissions",
            "json_admission": "json_admissions",
            "json_patientss": "json_patients",
            "json_patient": "json_patients",
            "json_provider": "json_providers",
            "json_transfer": "json_transfers",
            "json_careunit": "json_careunits",
            "json_labs": "json_lab",
            "json_diagnosis": "json_diagnoses",
            "json_insurances": "json_insurance",
            # columns
            "json_insurance": "insurance",
        }
        fixed_sql = sql
        for wrong, right in normalizations.items():
            pattern = r"\b" + re.escape(wrong) + r"\b"
            fixed_sql = re.sub(pattern, right, fixed_sql, flags=re.IGNORECASE)
        sql = fixed_sql
    except Exception:
        pass

    cursor = conn.cursor()
    cursor.execute(sql)
    rows = cursor.fetchall()
    meta = {"columns": [d[0] for d in cursor.description]} if cursor.description else {"columns": []}
    return rows, meta
