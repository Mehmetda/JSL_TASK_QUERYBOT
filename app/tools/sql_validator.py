"""
SQL validation module
"""
import sqlite3
from typing import Dict, Any

FORBIDDEN_KEYWORDS = ("insert", "update", "delete", "drop", "alter", "create", "attach", "pragma", "vacuum", "truncate", "replace")


def validate_sql(conn: sqlite3.Connection, sql: str) -> Dict[str, Any]:
    """Validate SQL query for safety and syntax"""
    sql_lower = sql.strip().lower()
    
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
        cursor.execute(f"EXPLAIN {sql}")
        # Execute safely by wrapping in a subquery to avoid duplicating LIMIT
        cursor.execute(f"SELECT 1 FROM ({sql}) LIMIT 1")
        cursor.fetchone()
        return {"is_valid": True, "error": None}
    except sqlite3.Error as e:
        return {"is_valid": False, "error": str(e)}
