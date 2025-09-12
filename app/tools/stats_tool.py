"""
Statistics tool for numeric column analysis
"""
import sqlite3
from typing import Dict, List, Any, Optional, Union
import logging
from app.models.database_models import ColumnType

logger = logging.getLogger(__name__)


class StatsTool:
    """Tool for calculating statistics on numeric columns"""
    
    def __init__(self, connection: sqlite3.Connection):
        """
        Initialize stats tool
        
        Args:
            connection: Database connection
        """
        self.connection = connection
    
    def get_column_stats(self, 
                        table_name: str, 
                        column_name: str,
                        where_clause: Optional[str] = None) -> Dict[str, Any]:
        """
        Get statistics for a numeric column
        
        Args:
            table_name: Name of the table
            column_name: Name of the column
            where_clause: Optional WHERE clause for filtering
            
        Returns:
            Dictionary with statistics
        """
        try:
            # Validate column is numeric
            if not self._is_numeric_column(table_name, column_name):
                return {
                    "error": f"Column {column_name} in table {table_name} is not numeric",
                    "is_numeric": False
                }
            
            # Build query
            base_query = f"SELECT {column_name} FROM {table_name}"
            if where_clause:
                base_query += f" WHERE {where_clause}"
            
            # Get basic statistics
            stats_query = f"""
            SELECT 
                COUNT(*) as count,
                MIN({column_name}) as min_value,
                MAX({column_name}) as max_value,
                AVG({column_name}) as avg_value,
                SUM({column_name}) as sum_value
            FROM ({base_query}) as filtered_data
            WHERE {column_name} IS NOT NULL
            """
            
            cursor = self.connection.cursor()
            cursor.execute(stats_query)
            result = cursor.fetchone()
            
            if not result or result[0] == 0:
                return {
                    "error": "No numeric data found",
                    "is_numeric": True,
                    "count": 0
                }
            
            count, min_val, max_val, avg_val, sum_val = result
            # Use database-provided AVG for consistency with SQLite's numeric handling
            computed_avg = avg_val
            
            # Calculate additional statistics
            variance_query = f"""
            SELECT 
                COUNT(*) as count,
                AVG(({column_name} - {avg_val}) * ({column_name} - {avg_val})) as variance
            FROM ({base_query}) as filtered_data
            WHERE {column_name} IS NOT NULL
            """
            
            cursor.execute(variance_query)
            var_result = cursor.fetchone()
            variance = var_result[1] if var_result and var_result[0] > 0 else 0
            std_dev = variance ** 0.5 if variance else 0
            
            # Get quartiles
            quartiles = self._get_quartiles(table_name, column_name, where_clause)
            
            return {
                "is_numeric": True,
                "count": count,
                "min": float(min_val) if min_val is not None else None,
                "max": float(max_val) if max_val is not None else None,
                "avg": round(float(computed_avg), 4) if computed_avg is not None else None,
                "sum": float(sum_val) if sum_val is not None else None,
                "variance": float(variance) if variance else 0,
                "std_dev": float(std_dev),
                "quartiles": quartiles,
                "range": float(max_val - min_val) if min_val is not None and max_val is not None else None
            }
            
        except Exception as e:
            logger.error(f"Error calculating stats for {table_name}.{column_name}: {e}")
            return {
                "error": str(e),
                "is_numeric": True
            }
    
    def _is_numeric_column(self, table_name: str, column_name: str) -> bool:
        """Check if column is numeric"""
        try:
            cursor = self.connection.cursor()
            cursor.execute(f"PRAGMA table_info({table_name})")
            columns = cursor.fetchall()
            
            numeric_types = {
                'INTEGER', 'INT', 'TINYINT', 'SMALLINT', 'BIGINT',
                'REAL', 'DOUBLE', 'FLOAT', 'NUMERIC', 'DECIMAL',
                'BOOLEAN', 'BOOL'
            }
            for col in columns:
                if col[1] == column_name:
                    col_type = (col[2] or "").upper()
                    # SQLite type affinity may include size/precision, match by prefix
                    if any(col_type.startswith(t) for t in numeric_types):
                        return True
                    # Fallback: infer from data types in the column
                    try:
                        cursor.execute(
                            f"SELECT typeof({column_name}) FROM {table_name} WHERE {column_name} IS NOT NULL LIMIT 10"
                        )
                        types = {row[0] for row in cursor.fetchall()}
                        if types and types.issubset({"integer", "real", "numeric"}):
                            return True
                    except Exception:
                        pass
                    return False
            
            return False
            
        except Exception as e:
            logger.error(f"Error checking column type: {e}")
            return False
    
    def _get_quartiles(self, 
                      table_name: str, 
                      column_name: str,
                      where_clause: Optional[str] = None) -> Dict[str, float]:
        """Calculate quartiles for a numeric column"""
        try:
            base_query = f"SELECT {column_name} FROM {table_name}"
            if where_clause:
                base_query += f" WHERE {where_clause}"
            
            # Get ordered values
            order_query = f"""
            SELECT {column_name} 
            FROM ({base_query}) as filtered_data
            WHERE {column_name} IS NOT NULL
            ORDER BY {column_name}
            """
            
            cursor = self.connection.cursor()
            cursor.execute(order_query)
            values = [row[0] for row in cursor.fetchall()]
            
            if len(values) == 0:
                return {"q1": None, "q2": None, "q3": None}
            
            n = len(values)
            
            # Calculate quartiles
            q1_idx = int(0.25 * n)
            q2_idx = int(0.5 * n)
            q3_idx = int(0.75 * n)
            
            return {
                "q1": float(values[q1_idx]) if q1_idx < n else None,
                "q2": float(values[q2_idx]) if q2_idx < n else None,  # Median
                "q3": float(values[q3_idx]) if q3_idx < n else None
            }
            
        except Exception as e:
            logger.error(f"Error calculating quartiles: {e}")
            return {"q1": None, "q2": None, "q3": None}
    
    def get_table_numeric_columns(self, table_name: str) -> List[str]:
        """Get list of numeric columns in a table"""
        try:
            cursor = self.connection.cursor()
            cursor.execute(f"PRAGMA table_info({table_name})")
            columns = cursor.fetchall()
            
            numeric_columns = []
            for col in columns:
                col_name = col[1]
                if self._is_numeric_column(table_name, col_name):
                    numeric_columns.append(col_name)
            
            return numeric_columns
            
        except Exception as e:
            logger.error(f"Error getting numeric columns: {e}")
            return []
    
    def analyze_table_numeric_data(self, table_name: str) -> Dict[str, Any]:
        """Analyze all numeric columns in a table"""
        try:
            numeric_columns = self.get_table_numeric_columns(table_name)
            
            if not numeric_columns:
                return {
                    "table": table_name,
                    "numeric_columns": [],
                    "message": "No numeric columns found"
                }
            
            column_stats = {}
            for col in numeric_columns:
                stats = self.get_column_stats(table_name, col)
                column_stats[col] = stats
            
            return {
                "table": table_name,
                "numeric_columns": numeric_columns,
                "column_stats": column_stats
            }
            
        except Exception as e:
            logger.error(f"Error analyzing table: {e}")
            return {
                "table": table_name,
                "error": str(e)
            }
    
    def format_stats_summary(self, stats: Dict[str, Any]) -> str:
        """Format statistics into a human-readable summary"""
        if "error" in stats:
            return f"Error: {stats['error']}"
        
        if not stats.get("is_numeric", False):
            return "Column is not numeric"
        
        if stats.get("count", 0) == 0:
            return "No data available"
        
        summary_parts = []
        
        # Basic stats
        summary_parts.append(f"Count: {stats['count']}")
        
        if stats.get("min") is not None:
            summary_parts.append(f"Min: {stats['min']:.2f}")
        if stats.get("max") is not None:
            summary_parts.append(f"Max: {stats['max']:.2f}")
        if stats.get("avg") is not None:
            summary_parts.append(f"Average: {stats['avg']:.2f}")
        
        # Range
        if stats.get("range") is not None:
            summary_parts.append(f"Range: {stats['range']:.2f}")
        
        # Standard deviation
        if stats.get("std_dev") is not None and stats['std_dev'] > 0:
            summary_parts.append(f"Std Dev: {stats['std_dev']:.2f}")
        
        # Quartiles
        quartiles = stats.get("quartiles", {})
        if quartiles.get("q1") is not None:
            summary_parts.append(f"Q1: {quartiles['q1']:.2f}")
        if quartiles.get("q2") is not None:
            summary_parts.append(f"Median: {quartiles['q2']:.2f}")
        if quartiles.get("q3") is not None:
            summary_parts.append(f"Q3: {quartiles['q3']:.2f}")
        
        return " | ".join(summary_parts)
