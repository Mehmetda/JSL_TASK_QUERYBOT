"""
Query history management

Features:
- Store query history in SQLite
- Retrieve query history with filtering
- Export query history
- Query analytics
"""

import sqlite3
import json
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path
from dataclasses import dataclass, asdict
from app.models.query_models import QueryResponse, QueryRequest

@dataclass
class QueryHistoryEntry:
    """Query history entry"""
    id: Optional[int] = None
    trace_id: str = ""
    question: str = ""
    sql: str = ""
    answer: str = ""
    success: bool = True
    execution_time_ms: int = 0
    rows_returned: int = 0
    user_id: Optional[str] = None
    timestamp: Optional[datetime] = None
    llm_mode: str = "local"
    tokens_used: int = 0
    error: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

class QueryHistoryManager:
    """Manages query history storage and retrieval"""
    
    def __init__(self, db_path: str = "data/query_history.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(exist_ok=True)
        self._init_database()
    
    def _init_database(self):
        """Initialize the query history database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS query_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                trace_id TEXT NOT NULL,
                question TEXT NOT NULL,
                sql TEXT NOT NULL,
                answer TEXT NOT NULL,
                success BOOLEAN NOT NULL,
                execution_time_ms INTEGER NOT NULL,
                rows_returned INTEGER NOT NULL,
                user_id TEXT,
                timestamp DATETIME NOT NULL,
                llm_mode TEXT NOT NULL,
                tokens_used INTEGER NOT NULL,
                error TEXT,
                metadata TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Create indexes for better performance
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_trace_id ON query_history(trace_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_user_id ON query_history(user_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_timestamp ON query_history(timestamp)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_success ON query_history(success)")
        
        conn.commit()
        conn.close()
    
    def save_query(self, query_response: QueryResponse, request: Optional[QueryRequest] = None) -> int:
        """Save a query to history"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # Extract metadata
            metadata = {}
            if query_response.meta:
                try:
                    # Pydantic models provide model_dump for dict serialization
                    metadata = {
                        "validation": query_response.meta.validation.model_dump() if query_response.meta.validation else None,
                        "database": query_response.meta.database.model_dump() if query_response.meta.database else None,
                        "performance": query_response.meta.performance.model_dump() if query_response.meta.performance else None,
                        "security": query_response.meta.security.model_dump() if query_response.meta.security else None
                    }
                except Exception:
                    # Fallback to asdict for dataclass-like objects
                    metadata = {
                        "validation": asdict(query_response.meta.validation) if query_response.meta.validation else None,
                        "database": asdict(query_response.meta.database) if query_response.meta.database else None,
                        "performance": asdict(query_response.meta.performance) if query_response.meta.performance else None,
                        "security": asdict(query_response.meta.security) if query_response.meta.security else None
                    }
            
            # Get token usage
            tokens_used = 0
            if query_response.meta and query_response.meta.performance and query_response.meta.performance.tokens:
                tokens_used = sum(query_response.meta.performance.tokens.values())
            
            # Get LLM mode
            llm_mode = "local"
            if query_response.meta and query_response.meta.llm:
                llm_mode = query_response.meta.llm.mode.value if hasattr(query_response.meta.llm.mode, 'value') else str(query_response.meta.llm.mode)
            
            cursor.execute("""
                INSERT INTO query_history (
                    trace_id, question, sql, answer, success, execution_time_ms,
                    rows_returned, user_id, timestamp, llm_mode, tokens_used,
                    error, metadata
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                query_response.trace_id or "",
                request.question if request else "",
                query_response.sql,
                query_response.answer,
                query_response.success,
                query_response.meta.performance.execution_ms if query_response.meta and query_response.meta.performance else 0,
                query_response.meta.performance.rows_returned if query_response.meta and query_response.meta.performance else 0,
                request.user_id if request else None,
                datetime.now(),
                llm_mode,
                tokens_used,
                query_response.error,
                json.dumps(metadata) if metadata else None
            ))
            
            entry_id = cursor.lastrowid
            conn.commit()
            return entry_id
            
        finally:
            conn.close()
    
    def get_query_history(self, 
                         user_id: Optional[str] = None,
                         limit: int = 50,
                         offset: int = 0,
                         success_only: bool = False,
                         start_date: Optional[datetime] = None,
                         end_date: Optional[datetime] = None) -> List[QueryHistoryEntry]:
        """Get query history with filtering"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # Build query
            query = "SELECT * FROM query_history WHERE 1=1"
            params = []
            
            if user_id:
                query += " AND user_id = ?"
                params.append(user_id)
            
            if success_only:
                query += " AND success = 1"
            
            if start_date:
                query += " AND timestamp >= ?"
                params.append(start_date)
            
            if end_date:
                query += " AND timestamp <= ?"
                params.append(end_date)
            
            query += " ORDER BY timestamp DESC LIMIT ? OFFSET ?"
            params.extend([limit, offset])
            
            cursor.execute(query, params)
            rows = cursor.fetchall()
            
            # Convert to QueryHistoryEntry objects
            entries = []
            for row in rows:
                entry = QueryHistoryEntry(
                    id=row[0],
                    trace_id=row[1],
                    question=row[2],
                    sql=row[3],
                    answer=row[4],
                    success=bool(row[5]),
                    execution_time_ms=row[6],
                    rows_returned=row[7],
                    user_id=row[8],
                    timestamp=datetime.fromisoformat(row[9]) if row[9] else None,
                    llm_mode=row[10],
                    tokens_used=row[11],
                    error=row[12],
                    metadata=json.loads(row[13]) if row[13] else None
                )
                entries.append(entry)
            
            return entries
            
        finally:
            conn.close()
    
    def get_query_by_id(self, query_id: int) -> Optional[QueryHistoryEntry]:
        """Get a specific query by ID"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute("SELECT * FROM query_history WHERE id = ?", (query_id,))
            row = cursor.fetchone()
            
            if not row:
                return None
            
            return QueryHistoryEntry(
                id=row[0],
                trace_id=row[1],
                question=row[2],
                sql=row[3],
                answer=row[4],
                success=bool(row[5]),
                execution_time_ms=row[6],
                rows_returned=row[7],
                user_id=row[8],
                timestamp=datetime.fromisoformat(row[9]) if row[9] else None,
                llm_mode=row[10],
                tokens_used=row[11],
                error=row[12],
                metadata=json.loads(row[13]) if row[13] else None
            )
            
        finally:
            conn.close()
    
    def get_query_stats(self, user_id: Optional[str] = None, days: int = 30) -> Dict[str, Any]:
        """Get query statistics"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            start_date = datetime.now() - timedelta(days=days)
            
            # Base query
            base_query = "FROM query_history WHERE timestamp >= ?"
            params = [start_date]
            
            if user_id:
                base_query += " AND user_id = ?"
                params.append(user_id)
            
            # Total queries
            cursor.execute(f"SELECT COUNT(*) {base_query}", params)
            total_queries = cursor.fetchone()[0]
            
            # Successful queries
            cursor.execute(f"SELECT COUNT(*) {base_query} AND success = 1", params)
            successful_queries = cursor.fetchone()[0]
            
            # Average execution time
            cursor.execute(f"SELECT AVG(execution_time_ms) {base_query} AND success = 1", params)
            avg_execution_time = cursor.fetchone()[0] or 0
            
            # Total tokens used
            cursor.execute(f"SELECT SUM(tokens_used) {base_query}", params)
            total_tokens = cursor.fetchone()[0] or 0
            
            # Queries by LLM mode
            cursor.execute(f"SELECT llm_mode, COUNT(*) {base_query} GROUP BY llm_mode", params)
            llm_mode_stats = dict(cursor.fetchall())
            
            # Queries by day
            cursor.execute(f"""
                SELECT DATE(timestamp) as date, COUNT(*) 
                {base_query} 
                GROUP BY DATE(timestamp) 
                ORDER BY date DESC
            """, params)
            daily_stats = dict(cursor.fetchall())
            
            return {
                "total_queries": total_queries,
                "successful_queries": successful_queries,
                "success_rate": (successful_queries / total_queries * 100) if total_queries > 0 else 0,
                "avg_execution_time_ms": round(avg_execution_time, 2),
                "total_tokens_used": total_tokens,
                "llm_mode_stats": llm_mode_stats,
                "daily_stats": daily_stats,
                "period_days": days
            }
            
        finally:
            conn.close()
    
    def delete_query(self, query_id: int) -> bool:
        """Delete a query from history"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute("DELETE FROM query_history WHERE id = ?", (query_id,))
            deleted = cursor.rowcount > 0
            conn.commit()
            return deleted
            
        finally:
            conn.close()
    
    def clear_history(self, user_id: Optional[str] = None, older_than_days: Optional[int] = None) -> int:
        """Clear query history"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            query = "DELETE FROM query_history WHERE 1=1"
            params = []
            
            if user_id:
                query += " AND user_id = ?"
                params.append(user_id)
            
            if older_than_days:
                cutoff_date = datetime.now() - timedelta(days=older_than_days)
                query += " AND timestamp < ?"
                params.append(cutoff_date)
            
            cursor.execute(query, params)
            deleted_count = cursor.rowcount
            conn.commit()
            return deleted_count
            
        finally:
            conn.close()
    
    def export_history(self, 
                      user_id: Optional[str] = None,
                      start_date: Optional[datetime] = None,
                      end_date: Optional[datetime] = None,
                      format: str = "json") -> str:
        """Export query history"""
        entries = self.get_query_history(
            user_id=user_id,
            limit=10000,  # Large limit for export
            start_date=start_date,
            end_date=end_date
        )
        
        if format == "json":
            return json.dumps([asdict(entry) for entry in entries], indent=2, default=str)
        elif format == "csv":
            import csv
            import io
            
            output = io.StringIO()
            if entries:
                writer = csv.DictWriter(output, fieldnames=asdict(entries[0]).keys())
                writer.writeheader()
                for entry in entries:
                    writer.writerow(asdict(entry))
            return output.getvalue()
        else:
            raise ValueError(f"Unsupported format: {format}")


# Global history manager instance
_history_manager = None

def get_history_manager() -> QueryHistoryManager:
    """Get the global history manager instance"""
    global _history_manager
    if _history_manager is None:
        _history_manager = QueryHistoryManager()
    return _history_manager

def save_query_to_history(query_response: QueryResponse, request: Optional[QueryRequest] = None) -> int:
    """Save a query to history"""
    manager = get_history_manager()
    return manager.save_query(query_response, request)
