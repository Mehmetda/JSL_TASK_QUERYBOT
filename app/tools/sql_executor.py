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
    
    cursor = conn.cursor()
    cursor.execute(sql)
    rows = cursor.fetchall()
    meta = {"columns": [d[0] for d in cursor.description]} if cursor.description else {"columns": []}
    return rows, meta
