"""
Database-related Pydantic models
"""
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from enum import Enum


class ColumnType(str, Enum):
    """Column type enumeration"""
    INTEGER = "INTEGER"
    REAL = "REAL"
    TEXT = "TEXT"
    BLOB = "BLOB"
    NUMERIC = "NUMERIC"
    DATE = "DATE"
    DATETIME = "DATETIME"
    BOOLEAN = "BOOLEAN"


class ColumnInfo(BaseModel):
    """Column information model"""
    name: str
    type: ColumnType
    is_primary_key: bool = False
    is_nullable: bool = True
    default_value: Optional[str] = None
    is_foreign_key: bool = False
    foreign_table: Optional[str] = None
    foreign_column: Optional[str] = None


class TableInfo(BaseModel):
    """Table information model"""
    name: str
    columns: List[ColumnInfo]
    row_count: int = 0
    description: Optional[str] = None
    is_system_table: bool = False


class SchemaInfo(BaseModel):
    """Schema information model"""
    tables: List[TableInfo]
    total_tables: int
    total_columns: int
    last_updated: Optional[str] = None


class DatabaseConnection(BaseModel):
    """Database connection model"""
    host: str
    port: int
    database: str
    username: str
    password: str
    ssl_mode: str = "prefer"


class QueryResult(BaseModel):
    """Query result model"""
    rows: List[Dict[str, Any]]
    columns: List[str]
    row_count: int
    execution_time_ms: int
    success: bool = True
    error: Optional[str] = None
