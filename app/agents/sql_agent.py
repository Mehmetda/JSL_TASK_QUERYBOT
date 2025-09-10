"""
SQL Agent with LLM integration and dynamic schema support
"""
import os
import sqlite3
from openai import OpenAI
from app.db.connection import get_connection
from app.agents.system_prompt import get_enhanced_system_prompt

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def generate_sql_with_llm(question: str, conn: sqlite3.Connection) -> str:
    """Generate SQL using OpenAI LLM with dynamic schema"""
    try:
        system_prompt = get_enhanced_system_prompt(conn)
        
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Kullanıcı Sorusu: {question}\n\nSQL Sorgusu:"}
            ],
            max_tokens=300,
            temperature=0.1
        )
        
        sql_query = response.choices[0].message.content.strip()
        
        # Clean up SQL query
        if sql_query.startswith("```sql"):
            sql_query = sql_query[6:]
        if sql_query.endswith("```"):
            sql_query = sql_query[:-3]
        
        # Extract only the first SQL statement (before semicolon)
        sql_query = sql_query.strip()
        if ';' in sql_query:
            sql_query = sql_query.split(';')[0].strip()
        
        # Ensure it's a single SELECT statement
        if not sql_query.upper().startswith('SELECT'):
            return generate_sql_fallback(question)
        
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
