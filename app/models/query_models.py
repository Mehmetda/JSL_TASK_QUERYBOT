"""
Query-related Pydantic models
"""
from pydantic import BaseModel, Field, model_validator
from typing import List, Optional, Dict, Any, Union
from datetime import datetime
from enum import Enum


class QueryType(str, Enum):
    """Query type enumeration"""
    COUNT_QUERY = "COUNT_QUERY"
    GROUP_BY_QUERY = "GROUP_BY_QUERY"
    ORDERED_QUERY = "ORDERED_QUERY"
    JOIN_QUERY = "JOIN_QUERY"
    SELECT = "SELECT"
    SELECT_QUERY = "SELECT_QUERY"
    OTHER = "OTHER"


class ComplexityLevel(str, Enum):
    """Query complexity enumeration"""
    SIMPLE = "SIMPLE"
    MEDIUM = "MEDIUM"
    COMPLEX = "COMPLEX"


class ValidationStatus(str, Enum):
    """Validation status enumeration"""
    PASSED = "PASSED"
    FAILED = "FAILED"
    BLOCKED_DATA_MODIFICATION = "BLOCKED_DATA_MODIFICATION"


class LLMMode(str, Enum):
    """LLM mode enumeration"""
    OPENAI = "openai"
    LOCAL = "local"
    AUTO = "auto"


class ColumnInfo(BaseModel):
    """Column information model"""
    name: str
    type: str
    is_primary_key: bool = False
    is_nullable: bool = True


class TableInfo(BaseModel):
    """Table information model"""
    name: str
    columns: List[ColumnInfo]
    row_count: int = 0


class DatabaseInfo(BaseModel):
    """Database information model"""
    tables_used: List[str] = Field(default_factory=list)
    query_type: QueryType
    complexity: ComplexityLevel
    relevant_schema: Optional[str] = None
    tables_info: List[TableInfo] = Field(default_factory=list)


class ValidationInfo(BaseModel):
    """Validation information model"""
    is_valid: bool
    error: Optional[str] = None
    sql_safety: ValidationStatus
    retried: bool = False


class PerformanceInfo(BaseModel):
    """Performance information model"""
    rows_returned: int
    columns_returned: int
    data_size_estimate: str
    execution_ms: int
    tokens: Dict[str, int] = Field(default_factory=dict)
    total_tokens: int = 0

    @model_validator(mode="after")
    def compute_total_tokens(self):
        try:
            self.total_tokens = int(sum(int(v) for v in self.tokens.values()))
        except Exception:
            # Keep default if tokens are not numeric
            self.total_tokens = self.total_tokens or 0
        return self


class LLMInfo(BaseModel):
    """LLM information model"""
    selected_mode: LLMMode
    effective_mode: LLMMode
    model_used: Optional[str] = None
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0


class SecurityInfo(BaseModel):
    """Security information model"""
    allowed_tables: List[str] = Field(default_factory=list)
    blocked_operations: List[str] = Field(default_factory=list)
    data_modification_blocked: bool = False


class QueryMetadata(BaseModel):
    """Query metadata model"""
    results: Dict[str, Any] = Field(default_factory=dict)
    validation: ValidationInfo
    database: DatabaseInfo
    performance: PerformanceInfo
    llm: Optional[LLMInfo] = None
    security: Optional[SecurityInfo] = None
    trace_id: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.now)


class QueryRequest(BaseModel):
    """Query request model"""
    question: str
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    trace_id: Optional[str] = None
    llm_mode: Optional[LLMMode] = None
    max_tokens: int = 300
    temperature: float = 0.1


class QueryResponse(BaseModel):
    """Query response model"""
    sql: str
    answer: str
    meta: QueryMetadata
    success: bool = True
    error: Optional[str] = None
    trace_id: Optional[str] = None
