"""
SQL Agent with LLM integration and dynamic schema support
"""
import os
import sqlite3
from app.db.connection import get_connection
from app.agents.system_prompt import get_contextual_system_prompt
from app.llm.llm_manager import get_llm_manager
from app.tools.ner_filter import SpaCyNERProvider, build_system_context_block

# Use LLM manager for flexible LLM selection
llm_manager = get_llm_manager()

# last LLM usage (for metrics)
LAST_LLM_USAGE = {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}


def generate_sql_with_llm(question: str, conn: sqlite3.Connection) -> str:
    """Generate SQL using local LLM with dynamic schema and NER filtering"""
    try:
        # Run NER filtering and de-identification before sending to LLM
        language_code = "tr"  # could be detected dynamically
        ner = SpaCyNERProvider(language_code=language_code)
        ner_result = ner.filter_and_deidentify(question)

        # Augment system prompt with entity context
        system_prompt = get_contextual_system_prompt(conn, question)
        entity_block = build_system_context_block(ner_result.desired_entities)
        system_prompt = f"{system_prompt}\n\n## Extracted entities (sanitized input used)\n{entity_block}"
        
        response = llm_manager.generate_response(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Kullanıcı Sorusu (sanitize): {ner_result.sanitized_text}\n\nSQL Sorgusu:"}
            ],
            max_tokens=300,
            temperature=0.1
        )
        # capture usage for token metrics
        try:
            usage = response.get("usage", {})
            if usage:
                LAST_LLM_USAGE.update({
                    "prompt_tokens": usage.get("prompt_tokens", 0),
                    "completion_tokens": usage.get("completion_tokens", 0),
                    "total_tokens": usage.get("total_tokens", 0),
                })
        except Exception:
            pass
        
        sql_query = response.get("content", "").strip()
        
        # Clean up SQL query
        if sql_query.startswith("```sql"):
            sql_query = sql_query[6:]
        if sql_query.endswith("```"):
            sql_query = sql_query[:-3]
        
        # Extract only the first SQL statement (before semicolon)
        sql_query = sql_query.strip()
        if ';' in sql_query:
            sql_query = sql_query.split(';')[0].strip()
        
        # Ensure it's a single SELECT statement and no data modification
        sql_upper = sql_query.upper().strip()
        dangerous_keywords = ['INSERT', 'UPDATE', 'DELETE', 'DROP', 'ALTER', 'CREATE', 'TRUNCATE', 'REPLACE', 'EXEC', 'EXECUTE']
        
        if not sql_upper.startswith('SELECT'):
            return generate_sql_fallback(question)
            
        # Check for dangerous keywords
        for keyword in dangerous_keywords:
            if keyword in sql_upper:
                print(f"Security: Dangerous keyword '{keyword}' detected, using fallback")
                return generate_sql_fallback(question)
        
        # Check for ORDER BY with LIMIT but no numeric columns
        if 'ORDER BY' in sql_upper and 'LIMIT' in sql_upper:
            # This is a basic check - in production you'd want to parse the ORDER BY clause
            # and check if the column is numeric/date type
            print("Info: ORDER BY with LIMIT detected - ensure column is numeric/date type")
            
            # Try to validate against schema if possible
            try:
                cursor = conn.cursor()
                # Extract table name from query (basic approach)
                if 'FROM' in sql_upper:
                    table_part = sql_upper.split('FROM')[1].split()[0]
                    # Check if table has numeric columns
                    cursor.execute(f"PRAGMA table_info({table_part})")
                    columns = cursor.fetchall()
                    numeric_cols = [col[1] for col in columns if col[2].upper() in ['INTEGER', 'REAL', 'NUMERIC']]
                    if not numeric_cols:
                        print(f"Warning: Table {table_part} has no numeric columns for ORDER BY")
            except Exception as e:
                print(f"Schema validation error: {e}")
        
        return sql_query
        
    except Exception as e:
        print(f"LLM Error: {e}")
        return generate_sql_fallback(question)


def generate_sql_fallback(question: str) -> str:
    """Fallback SQL generation using heuristics"""
    q = question.lower().strip()
    
    if "how many" in q or "kaç" in q or "count" in q or "toplam" in q:
        if "patient" in q or "hasta" in q:
            return "SELECT COUNT(*) AS total_patients FROM json_patients"
        if "admission" in q or "yatış" in q:
            return "SELECT COUNT(*) AS total_admissions FROM json_admissions"
        if "provider" in q or "doktor" in q:
            return "SELECT COUNT(*) AS total_providers FROM json_providers"
        if "transfer" in q or "transfer" in q:
            return "SELECT COUNT(*) AS total_transfers FROM json_transfers"
        return "SELECT COUNT(*) AS total_records FROM json_patients"
    
    if "age" in q or "yaş" in q:
        return "SELECT anchor_age FROM json_patients WHERE anchor_age IS NOT NULL LIMIT 10"
    
    if "gender" in q or "cinsiyet" in q:
        return "SELECT gender, COUNT(*) FROM json_patients GROUP BY gender"
    
    if "admission" in q or "yatış" in q:
        return "SELECT admittime, dischtime, admission_type FROM json_admissions LIMIT 10"
    
    if "provider" in q or "doktor" in q:
        return "SELECT provider_id, npi FROM json_providers LIMIT 10"
    
    # Default query
    return "SELECT COUNT(*) AS total_records FROM json_patients"


def generate_sql(question: str, conn: sqlite3.Connection) -> str:
    """Main SQL generation function with dynamic schema support"""
    # Try LLM first, fallback to heuristics
    sql = generate_sql_with_llm(question, conn)
    if not sql:
        sql = generate_sql_fallback(question)
    return sql
