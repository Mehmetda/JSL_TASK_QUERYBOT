"""
SQL validation module
"""
import sqlite3
from typing import Dict, Any

FORBIDDEN_KEYWORDS = ("insert", "update", "delete", "drop", "alter", "create", "attach", "pragma", "vacuum")


def validate_sql(conn: sqlite3.Connection, sql: str) -> Dict[str, Any]:
    """Validate SQL query for safety and syntax"""
    sql_lower = sql.strip().lower()
    
    # Check if it's a SELECT query
    if not sql_lower.startswith("select"):
        return {"is_valid": False, "error": "Only SELECT queries are allowed."}
    
    # Check for forbidden keywords
    if any(keyword in sql_lower for keyword in FORBIDDEN_KEYWORDS):
        return {"is_valid": False, "error": "Forbidden SQL keywords detected."}
    
    try:
        # Use EXPLAIN to check syntax
        cursor = conn.cursor()
        cursor.execute(f"EXPLAIN {sql}")
        # Try to fetch one row to ensure it's executable
        cursor.execute(f"{sql} LIMIT 1")
        cursor.fetchone()
        return {"is_valid": True, "error": None}
    except sqlite3.Error as e:
        return {"is_valid": False, "error": str(e)}
