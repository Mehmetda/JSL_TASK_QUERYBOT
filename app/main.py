"""
Main pipeline for QueryBot
"""
import re
import logging
from app.agents.sql_agent import generate_sql
from app.tools.sql_executor import execute_sql
from app.tools.answer_summarizer import summarize_results
from app.db.connection import get_connection
from app.tools.sql_validator import validate_sql


# Basic logging configuration
logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(asctime)s - %(name)s - %(message)s")
logger = logging.getLogger(__name__)


def extract_tables_from_sql(sql: str) -> list:
    """Extract table names from SQL query"""
    if not sql:
        return []
    
    # Simple regex to find table names after FROM and JOIN
    tables = re.findall(r'(?:FROM|JOIN)\s+(\w+)', sql.upper())
    return list(set(tables))  # Remove duplicates


def classify_query_type(sql: str) -> str:
    """Classify the type of SQL query"""
    if not sql:
        return "UNKNOWN"
    
    sql_upper = sql.upper().strip()
    
    if sql_upper.startswith('SELECT COUNT'):
        return "COUNT_QUERY"
    elif sql_upper.startswith('SELECT') and 'GROUP BY' in sql_upper:
        return "GROUP_BY_QUERY"
    elif sql_upper.startswith('SELECT') and 'ORDER BY' in sql_upper:
        return "ORDERED_QUERY"
    elif sql_upper.startswith('SELECT') and 'JOIN' in sql_upper:
        return "JOIN_QUERY"
    elif sql_upper.startswith('SELECT'):
        return "SELECT_QUERY"
    else:
        return "OTHER"


def assess_query_complexity(sql: str) -> str:
    """Assess the complexity of the SQL query"""
    if not sql:
        return "UNKNOWN"
    
    sql_upper = sql.upper()
    complexity_score = 0
    
    # Count complexity indicators
    if 'JOIN' in sql_upper:
        complexity_score += 2
    if 'GROUP BY' in sql_upper:
        complexity_score += 1
    if 'ORDER BY' in sql_upper:
        complexity_score += 1
    if 'HAVING' in sql_upper:
        complexity_score += 1
    if 'WHERE' in sql_upper:
        complexity_score += 1
    if 'COUNT' in sql_upper:
        complexity_score += 1
    
    if complexity_score <= 1:
        return "SIMPLE"
    elif complexity_score <= 3:
        return "MEDIUM"
    else:
        return "COMPLEX"


def run_query_pipeline(question: str) -> dict:
    """Run the complete query pipeline"""
    # Get database connection
    conn = get_connection()
    
    try:
        # Generate SQL with dynamic schema
        logger.info("Generating SQL for question")
        sql = generate_sql(question, conn)
        
        # Validate SQL
        logger.info("Validating generated SQL")
        validation_result = validate_sql(conn, sql)
        if not validation_result["is_valid"]:
            # One-time retry with guidance appended to the question
            logger.warning("SQL validation failed, attempting one-time retry with guidance")
            retry_question = (
                question
                + "\n(Not: Tek bir SELECT ifadesi üret, noktalı virgül kullanma, mevcut şemaya uygun sütun ve tablo isimlerini kullan.)"
            )
            sql = generate_sql(retry_question, conn)
            validation_result = validate_sql(conn, sql)
            if not validation_result["is_valid"]:
                logger.error("Retry validation also failed")
                return {
                    "sql": sql,
                    "answer": "",
                    "meta": {"validation": validation_result}
                }
        
        # Execute SQL
        logger.info("Executing SQL")
        rows, meta = execute_sql(conn, sql)
        
        # Summarize results
        logger.info("Summarizing results")
        answer = summarize_results(question, rows)
        
        # Prepare enhanced metadata (without question and sql_generated)
        enhanced_meta = {
            "results": {
                "row_count": len(rows),
                "columns": meta.get("columns", [])
            },
            "validation": {
                "is_valid": validation_result["is_valid"],
                "error": validation_result.get("error"),
                "sql_safety": "PASSED" if validation_result["is_valid"] else "FAILED"
            },
            "database": {
                "tables_used": extract_tables_from_sql(sql),
                "query_type": classify_query_type(sql),
                "complexity": assess_query_complexity(sql)
            },
            "performance": {
                "rows_returned": len(rows),
                "columns_returned": len(meta.get("columns", [])),
                "data_size_estimate": f"{len(str(rows))} characters"
            }
        }
        
        result = {
            "sql": sql,
            "answer": answer,
            "meta": enhanced_meta
        }
        logger.info("Pipeline completed successfully")
        return result
        
    except Exception as e:
        logger.exception("Pipeline failed with an unhandled exception")
        return {
            "sql": "",
            "answer": f"Hata oluştu: {str(e)}",
            "meta": {"error": str(e)}
        }
    finally:
        conn.close()
