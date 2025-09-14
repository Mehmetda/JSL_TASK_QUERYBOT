"""
SQL Agent v2 - Inherits from Base Agent

This agent handles SQL generation using NER-enhanced hybrid RAG system.
It inherits from BaseAgent to get common functionality like logging, tracing, and error handling.
"""
import sqlite3
from typing import Any, Dict, Optional
from app.agents.base_agent import BaseAgent, AgentContext, AgentResponse
from app.agents.system_prompt import get_ner_enhanced_hybrid_schema_snippets
from app.db.connection import get_connection


class SQLAgent(BaseAgent):
    """
    SQL Agent that generates SQL queries using NER-enhanced hybrid RAG.
    
    This agent:
    1. Uses NER to extract entities from user questions
    2. Applies entity-based metadata filtering for schema retrieval
    3. Generates SQL queries using LLM with enhanced context
    4. Provides comprehensive logging and error handling
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize SQL Agent
        
        Args:
            config: Optional configuration dictionary
        """
        super().__init__("SQLAgent", config)
        
        # SQL-specific configuration
        self.default_top_k = self.config.get("top_k", 3)
        self.default_language = self.config.get("language", "en")  # English by default
        self.max_sql_length = self.config.get("max_sql_length", 1000)
        
        # SQL generation statistics
        self._sql_generation_count = 0
        self._successful_sql_count = 0
    
    def _execute_agent_logic(self, context: AgentContext, trace_id: str) -> Dict[str, Any]:
        """
        Execute SQL generation logic
        
        Args:
            context: Agent context with question and parameters
            trace_id: Trace ID for this execution
            
        Returns:
            Dictionary containing SQL query and metadata
        """
        # Validate context
        if not self.validate_context(context):
            raise ValueError("Invalid agent context")
        
        # Get database connection
        conn = get_connection()
        
        try:
            # Generate SQL using NER-enhanced hybrid RAG
            sql_result = self._generate_sql_with_ner_rag(
                context, conn, trace_id
            )
            
            # Update statistics
            self._sql_generation_count += 1
            if sql_result.get("sql"):
                self._successful_sql_count += 1
            
            return sql_result
            
        finally:
            conn.close()
    
    def _generate_sql_with_ner_rag(
        self, 
        context: AgentContext, 
        conn: sqlite3.Connection, 
        trace_id: str
    ) -> Dict[str, Any]:
        """
        Generate SQL using NER-enhanced hybrid RAG
        
        Args:
            context: Agent context
            conn: Database connection
            trace_id: Trace ID
            
        Returns:
            Dictionary with SQL query and metadata
        """
        # Get enhanced schema snippets using NER + hybrid RAG
        enhanced_schema_snippets = get_ner_enhanced_hybrid_schema_snippets(
            conn, 
            context.question, 
            top_k=self.default_top_k, 
            language_code=context.language
        )
        
        # Create system prompt with enhanced schema information
        system_prompt = self._create_system_prompt(enhanced_schema_snippets, context)
        
        # Generate SQL using LLM
        response = self.llm_manager.generate_response(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"User Question: {context.question}\n\nGenerate SQL Query:"}
            ],
            max_tokens=context.max_tokens,
            temperature=context.temperature
        )
        
        # Extract and clean SQL query
        sql_query = self._extract_and_clean_sql(response.get("content", ""))
        
        # Get usage information
        usage = response.get("usage", {})
        
        return {
            "sql": sql_query,
            "schema_snippets": enhanced_schema_snippets,
            "usage": usage,
            "trace_id": trace_id,
            "agent_name": self.agent_name
        }
    
    def _create_system_prompt(self, schema_snippets: str, context: AgentContext) -> str:
        """
        Create system prompt for SQL generation
        
        Args:
            schema_snippets: Enhanced schema snippets from NER-RAG
            context: Agent context
            
        Returns:
            Formatted system prompt
        """
        return f"""You are a medical database SQL expert. Generate accurate SQL queries for the given question.

Database Schema Information:
{schema_snippets}

Important Guidelines:
- Use only the provided schema information
- Generate clean, efficient SQL queries
- Use proper JOINs when needed
- Include appropriate WHERE clauses
- Use ORDER BY when using LIMIT
- Handle multilingual text properly in queries
- Focus on medical domain entities and relationships
- Maximum SQL length: {self.max_sql_length} characters

Question: {context.question}

Generate SQL query:"""
    
    def _extract_and_clean_sql(self, raw_sql: str) -> str:
        """
        Extract and clean SQL query from LLM response
        
        Args:
            raw_sql: Raw SQL response from LLM
            
        Returns:
            Cleaned SQL query
        """
        if not raw_sql:
            return ""
        
        # Remove code block markers
        if raw_sql.startswith("```sql"):
            raw_sql = raw_sql[6:]
        elif raw_sql.startswith("```"):
            raw_sql = raw_sql[3:]
        
        if raw_sql.endswith("```"):
            raw_sql = raw_sql[:-3]
        
        # Extract only the first SQL statement (before semicolon)
        sql_query = raw_sql.strip()
        if ';' in sql_query:
            sql_query = sql_query.split(';')[0].strip()
        
        # Limit SQL length
        if len(sql_query) > self.max_sql_length:
            sql_query = sql_query[:self.max_sql_length]
            self.logger.warning(f"SQL query truncated to {self.max_sql_length} characters")
        
        return sql_query
    
    def get_sql_statistics(self) -> Dict[str, Any]:
        """Get SQL generation statistics"""
        base_stats = self.get_performance_stats()
        return {
            **base_stats,
            "sql_generation_count": self._sql_generation_count,
            "successful_sql_count": self._successful_sql_count,
            "sql_success_rate": (
                self._successful_sql_count / self._sql_generation_count 
                if self._sql_generation_count > 0 else 0.0
            )
        }
    
    def generate_sql(self, question: str, **kwargs) -> AgentResponse:
        """
        Convenience method to generate SQL for a question
        
        Args:
            question: User question
            **kwargs: Additional context parameters
            
        Returns:
            AgentResponse with SQL result
        """
        context = AgentContext(
            question=question,
            language=kwargs.get("language", self.default_language),
            max_tokens=kwargs.get("max_tokens", 300),
            temperature=kwargs.get("temperature", 0.1),
            user_id=kwargs.get("user_id"),
            session_id=kwargs.get("session_id"),
            additional_context=kwargs.get("additional_context")
        )
        
        return self.execute(context)


# Global SQL Agent instance
_sql_agent = None

def get_sql_agent(config: Optional[Dict[str, Any]] = None) -> SQLAgent:
    """
    Get or create the global SQL agent instance
    
    Args:
        config: Optional configuration for the agent
        
    Returns:
        SQLAgent instance
    """
    global _sql_agent
    if _sql_agent is None:
        _sql_agent = SQLAgent(config)
    return _sql_agent

def generate_sql_with_agent(question: str, **kwargs) -> AgentResponse:
    """
    Convenience function to generate SQL using the global agent
    
    Args:
        question: User question
        **kwargs: Additional parameters
        
    Returns:
        AgentResponse with SQL result
    """
    agent = get_sql_agent()
    return agent.generate_sql(question, **kwargs)
