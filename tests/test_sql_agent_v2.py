"""
Test SQL Agent v2

This test suite validates the SQL Agent v2 functionality including:
- SQL generation using NER-enhanced hybrid RAG
- Error handling and validation
- Performance monitoring
- Integration with base agent functionality
"""
import unittest
import os
import sys
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

# Add project root to Python path
CURRENT = Path(__file__).resolve().parent
PROJECT_ROOT = CURRENT.parent
sys.path.insert(0, str(PROJECT_ROOT))

from app.agents.sql_agent import SQLAgent, get_sql_agent, generate_sql_with_agent
from app.agents.base_agent import AgentContext, AgentResponse


class TestSQLAgent(unittest.TestCase):
    """Test cases for SQL Agent v2"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.sql_agent = SQLAgent()
        self.valid_context = AgentContext(
            question="What are the patient counts by gender?",
            language="en",
            max_tokens=300,
            temperature=0.1
        )
    
    def test_sql_agent_initialization(self):
        """Test SQL agent initialization"""
        self.assertEqual(self.sql_agent.agent_name, "SQLAgent")
        self.assertEqual(self.sql_agent.default_top_k, 3)
        self.assertEqual(self.sql_agent.default_language, "tr")
        self.assertEqual(self.sql_agent.max_sql_length, 1000)
        self.assertEqual(self.sql_agent._sql_generation_count, 0)
        self.assertEqual(self.sql_agent._successful_sql_count, 0)
    
    def test_context_validation(self):
        """Test context validation for SQL agent"""
        # Valid context
        self.assertTrue(self.sql_agent.validate_context(self.valid_context))
        
        # Invalid contexts
        empty_question = AgentContext(question="", language="tr")
        self.assertFalse(self.sql_agent.validate_context(empty_question))
        
        invalid_tokens = AgentContext(question="Test", max_tokens=0, language="tr")
        self.assertFalse(self.sql_agent.validate_context(invalid_tokens))
    
    @patch('app.agents.sql_agent_v2.get_connection')
    @patch('app.agents.sql_agent_v2.get_ner_enhanced_hybrid_schema_snippets')
    @patch.object(SQLAgent, 'llm_manager')
    def test_successful_sql_generation(self, mock_llm_manager, mock_schema, mock_conn):
        """Test successful SQL generation"""
        # Mock database connection
        mock_conn.return_value.__enter__.return_value = Mock()
        
        # Mock schema snippets
        mock_schema.return_value = "Table: json_admissions, Column: gender (similarity: 0.8)\nColumn: gender (TEXT) in table json_admissions"
        
        # Mock LLM response
        mock_llm_manager.generate_response.return_value = {
            "content": "SELECT gender, COUNT(*) as hasta_sayisi FROM json_admissions GROUP BY gender",
            "usage": {"prompt_tokens": 100, "completion_tokens": 20, "total_tokens": 120}
        }
        
        # Execute SQL generation
        response = self.sql_agent.execute(self.valid_context)
        
        # Verify response
        self.assertTrue(response.success)
        self.assertIsNotNone(response.result)
        self.assertIn("sql", response.result)
        self.assertIn("schema_snippets", response.result)
        self.assertIn("usage", response.result)
        self.assertEqual(response.result["agent_name"], "SQLAgent")
        
        # Verify SQL was generated
        sql = response.result["sql"]
        self.assertIn("SELECT", sql)
        self.assertIn("gender", sql)
        self.assertIn("json_admissions", sql)
        
        # Verify statistics were updated
        self.assertEqual(self.sql_agent._sql_generation_count, 1)
        self.assertEqual(self.sql_agent._successful_sql_count, 1)
    
    @patch('app.agents.sql_agent_v2.get_connection')
    def test_sql_generation_with_database_error(self, mock_conn):
        """Test SQL generation with database connection error"""
        # Mock database connection error
        mock_conn.side_effect = Exception("Database connection failed")
        
        # Execute SQL generation
        response = self.sql_agent.execute(self.valid_context)
        
        # Verify error response
        self.assertFalse(response.success)
        self.assertIsNone(response.result)
        self.assertIsNotNone(response.error)
        self.assertIn("Database connection failed", response.error)
    
    @patch('app.agents.sql_agent_v2.get_connection')
    @patch('app.agents.sql_agent_v2.get_ner_enhanced_hybrid_schema_snippets')
    @patch.object(SQLAgent, 'llm_manager')
    def test_sql_extraction_and_cleaning(self, mock_llm_manager, mock_schema, mock_conn):
        """Test SQL extraction and cleaning from LLM response"""
        # Mock database connection
        mock_conn.return_value.__enter__.return_value = Mock()
        
        # Mock schema snippets
        mock_schema.return_value = "Test schema"
        
        # Mock LLM response with code block markers
        mock_llm_manager.generate_response.return_value = {
            "content": "```sql\nSELECT * FROM json_admissions WHERE gender = 'M';\n```",
            "usage": {"prompt_tokens": 100, "completion_tokens": 20, "total_tokens": 120}
        }
        
        # Execute SQL generation
        response = self.sql_agent.execute(self.valid_context)
        
        # Verify SQL was cleaned
        self.assertTrue(response.success)
        sql = response.result["sql"]
        self.assertNotIn("```sql", sql)
        self.assertNotIn("```", sql)
        self.assertIn("SELECT * FROM json_admissions", sql)
    
    @patch('app.agents.sql_agent_v2.get_connection')
    @patch('app.agents.sql_agent_v2.get_ner_enhanced_hybrid_schema_snippets')
    @patch.object(SQLAgent, 'llm_manager')
    def test_sql_length_truncation(self, mock_llm_manager, mock_schema, mock_conn):
        """Test SQL length truncation"""
        # Mock database connection
        mock_conn.return_value.__enter__.return_value = Mock()
        
        # Mock schema snippets
        mock_schema.return_value = "Test schema"
        
        # Create a very long SQL query
        long_sql = "SELECT " + ", ".join([f"column_{i}" for i in range(200)]) + " FROM json_admissions"
        mock_llm_manager.generate_response.return_value = {
            "content": long_sql,
            "usage": {"prompt_tokens": 100, "completion_tokens": 20, "total_tokens": 120}
        }
        
        # Execute SQL generation
        response = self.sql_agent.execute(self.valid_context)
        
        # Verify SQL was truncated
        self.assertTrue(response.success)
        sql = response.result["sql"]
        self.assertLessEqual(len(sql), self.sql_agent.max_sql_length)
    
    def test_sql_statistics(self):
        """Test SQL generation statistics"""
        # Initial statistics
        stats = self.sql_agent.get_sql_statistics()
        self.assertEqual(stats["sql_generation_count"], 0)
        self.assertEqual(stats["successful_sql_count"], 0)
        self.assertEqual(stats["sql_success_rate"], 0.0)
        
        # Simulate some generations
        self.sql_agent._sql_generation_count = 5
        self.sql_agent._successful_sql_count = 4
        
        stats = self.sql_agent.get_sql_statistics()
        self.assertEqual(stats["sql_generation_count"], 5)
        self.assertEqual(stats["successful_sql_count"], 4)
        self.assertEqual(stats["sql_success_rate"], 0.8)
    
    def test_system_prompt_creation(self):
        """Test system prompt creation"""
        schema_snippets = "Table: json_admissions, Column: gender\nColumn: gender (TEXT) in table json_admissions"
        
        prompt = self.sql_agent._create_system_prompt(schema_snippets, self.valid_context)
        
        self.assertIn("medical database SQL expert", prompt)
        self.assertIn(schema_snippets, prompt)
        self.assertIn(self.valid_context.question, prompt)
        self.assertIn("Important Guidelines:", prompt)
        self.assertIn(str(self.sql_agent.max_sql_length), prompt)
    
    def test_sql_extraction_edge_cases(self):
        """Test SQL extraction with edge cases"""
        # Test empty response
        sql = self.sql_agent._extract_and_clean_sql("")
        self.assertEqual(sql, "")
        
        # Test response without SQL
        sql = self.sql_agent._extract_and_clean_sql("This is not SQL")
        self.assertEqual(sql, "This is not SQL")
        
        # Test response with multiple semicolons
        sql = self.sql_agent._extract_and_clean_sql("SELECT * FROM table1; SELECT * FROM table2;")
        self.assertEqual(sql, "SELECT * FROM table1")
        
        # Test response with different code block markers
        sql = self.sql_agent._extract_and_clean_sql("```\nSELECT * FROM table\n```")
        self.assertEqual(sql, "SELECT * FROM table")
    
    def test_generate_sql_convenience_method(self):
        """Test the convenience method for SQL generation"""
        with patch.object(self.sql_agent, 'execute') as mock_execute:
            mock_response = AgentResponse(
                success=True,
                result={"sql": "SELECT * FROM table"},
                trace_id="test_trace"
            )
            mock_execute.return_value = mock_response
            
            response = self.sql_agent.generate_sql(
                "Test question",
                language="en",
                max_tokens=500,
                temperature=0.5,
                user_id="user123"
            )
            
            # Verify the convenience method was called
            mock_execute.assert_called_once()
            call_args = mock_execute.call_args[0][0]  # First positional argument
            self.assertEqual(call_args.question, "Test question")
            self.assertEqual(call_args.language, "en")
            self.assertEqual(call_args.max_tokens, 500)
            self.assertEqual(call_args.temperature, 0.5)
            self.assertEqual(call_args.user_id, "user123")


class TestSQLAgentIntegration(unittest.TestCase):
    """Test SQL Agent integration functionality"""
    
    def test_get_sql_agent_singleton(self):
        """Test SQL agent singleton pattern"""
        agent1 = get_sql_agent()
        agent2 = get_sql_agent()
        
        self.assertIs(agent1, agent2)
        self.assertIsInstance(agent1, SQLAgent)
    
    def test_get_sql_agent_with_config(self):
        """Test SQL agent creation with configuration"""
        config = {"top_k": 5, "max_sql_length": 2000}
        agent = get_sql_agent(config)
        
        self.assertEqual(agent.default_top_k, 5)
        self.assertEqual(agent.max_sql_length, 2000)
    
    @patch('app.agents.sql_agent_v2.get_sql_agent')
    def test_generate_sql_with_agent_function(self, mock_get_agent):
        """Test the global generate_sql_with_agent function"""
        mock_agent = Mock()
        mock_response = AgentResponse(
            success=True,
            result={"sql": "SELECT * FROM table"},
            trace_id="test_trace"
        )
        mock_agent.generate_sql.return_value = mock_response
        mock_get_agent.return_value = mock_agent
        
        response = generate_sql_with_agent(
            "Test question",
            language="tr",
            max_tokens=300
        )
        
        # Verify the function was called
        mock_get_agent.assert_called_once()
        mock_agent.generate_sql.assert_called_once_with(
            "Test question",
            language="tr",
            max_tokens=300
        )
        
        self.assertEqual(response, mock_response)


class TestSQLAgentPerformance(unittest.TestCase):
    """Test SQL Agent performance and monitoring"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.sql_agent = SQLAgent()
    
    def test_performance_tracking(self):
        """Test performance tracking for SQL agent"""
        # Simulate some executions
        self.sql_agent._execution_times = [100, 200, 150, 300]
        self.sql_agent._success_count = 3
        self.sql_agent._error_count = 1
        self.sql_agent._sql_generation_count = 4
        self.sql_agent._successful_sql_count = 3
        
        stats = self.sql_agent.get_sql_statistics()
        
        # Check base performance stats
        self.assertEqual(stats["total_executions"], 4)
        self.assertEqual(stats["success_rate"], 0.75)
        self.assertEqual(stats["average_execution_time_ms"], 187.5)
        self.assertEqual(stats["min_execution_time_ms"], 100)
        self.assertEqual(stats["max_execution_time_ms"], 300)
        
        # Check SQL-specific stats
        self.assertEqual(stats["sql_generation_count"], 4)
        self.assertEqual(stats["successful_sql_count"], 3)
        self.assertEqual(stats["sql_success_rate"], 0.75)
    
    def test_agent_info(self):
        """Test agent info retrieval"""
        info = self.sql_agent.get_agent_info()
        
        self.assertEqual(info["agent_name"], "SQLAgent")
        self.assertIn("config", info)
        self.assertIn("performance_stats", info)
        self.assertIn("sql_generation_count", info["performance_stats"])
        self.assertIn("successful_sql_count", info["performance_stats"])
        self.assertIn("sql_success_rate", info["performance_stats"])


def run_tests():
    """Run all SQL agent v2 tests"""
    # Create test suite
    test_suite = unittest.TestSuite()
    
    # Add test cases
    test_suite.addTest(unittest.makeSuite(TestSQLAgent))
    test_suite.addTest(unittest.makeSuite(TestSQLAgentIntegration))
    test_suite.addTest(unittest.makeSuite(TestSQLAgentPerformance))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)
    
    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_tests()
    if success:
        print("\n✅ All SQL agent v2 tests passed!")
    else:
        print("\n❌ Some SQL agent v2 tests failed!")
        exit(1)
