"""
SQL validation module
"""
import sqlite3
from typing import Dict, Any

FORBIDDEN_KEYWORDS = ("insert", "update", "delete", "drop", "alter", "create", "attach", "pragma", "vacuum", "truncate", "replace")


def _normalize_table_typos(sql: str) -> str:
    """Normalize common table name typos in SQL query"""
    import re
    
    # Common typos → correct table names
    typo_mappings = {
        "json_admission": "json_admissions",
        "json_admissionss": "json_admissions", 
        "json_patient": "json_patients",
        "json_provider": "json_providers",
        "json_transfer": "json_transfers",
        "json_careunit": "json_careunits",
        "json_labs": "json_lab",
        "json_diagnosis": "json_diagnoses",
        "json_insurances": "json_insurance",
    }
    
    # Apply typo fixes (case-insensitive)
    normalized_sql = sql
    for typo, correct in typo_mappings.items():
        # Match table names after FROM, JOIN, etc.
        pattern = rf'\b{re.escape(typo)}\b'
        normalized_sql = re.sub(pattern, correct, normalized_sql, flags=re.IGNORECASE)
    
    return normalized_sql


def validate_sql(conn: sqlite3.Connection, sql: str) -> Dict[str, Any]:
    """Validate SQL query for safety and syntax"""
    # First normalize common table name typos
    normalized_sql = _normalize_table_typos(sql)
    sql_lower = normalized_sql.strip().lower()
    
    # Check if it's a SELECT query
    if not sql_lower.startswith("select"):
        return {"is_valid": False, "error": "Only SELECT queries are allowed."}
    
    # Check for forbidden keywords
    if any(keyword in sql_lower for keyword in FORBIDDEN_KEYWORDS):
        return {"is_valid": False, "error": "Forbidden SQL keywords detected."}

    # Disallow multiple statements
    if ";" in sql_lower:
        return {"is_valid": False, "error": "Multiple SQL statements are not allowed."}

    # Rule: LIMIT requires ORDER BY to ensure deterministic results
    if " limit " in f" {sql_lower} " and " order by " not in sql_lower:
        return {"is_valid": False, "error": "LIMIT without ORDER BY is not allowed."}
    
    try:
        # Use EXPLAIN to check syntax
        cursor = conn.cursor()
        cursor.execute(f"EXPLAIN {normalized_sql}")
        # Execute safely by wrapping in a subquery to avoid duplicating LIMIT
        cursor.execute(f"SELECT 1 FROM ({normalized_sql}) LIMIT 1")
        cursor.fetchone()
        return {"is_valid": True, "error": None}
    except sqlite3.Error as e:
        return {"is_valid": False, "error": str(e)}
