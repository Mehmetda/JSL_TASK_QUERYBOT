"""
Database connection module
"""
import os
import sqlite3
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

DEFAULT_DB = Path(__file__).parent / "demo.sqlite"
DB_PATH = Path(os.getenv("DB_PATH", DEFAULT_DB.as_posix()))


def get_connection() -> sqlite3.Connection:
    """Get SQLite database connection"""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    return sqlite3.connect(DB_PATH.as_posix())
