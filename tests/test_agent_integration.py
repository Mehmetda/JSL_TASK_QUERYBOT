"""
Test Agent Integration

This test suite validates the integration between:
- Base Agent and SQL Agent
- New agent system with existing pipeline
- End-to-end functionality
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

from app.agents.sql_agent import SQLAgent, generate_sql_with_agent
from app.agents.base_agent import AgentContext, AgentResponse


class TestAgentIntegration(unittest.TestCase):
    """Test agent integration functionality"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.sql_agent = SQLAgent()
        self.test_questions = [
            "Cinsiyete göre hasta sayıları nedir?",
            "Yatış tiplerine göre dağılım nedir?",
            "subject_id 12345 olan hastanın yatış bilgileri?",
            "hadm_id 67890 ile ilgili transfer kayıtları?"
        ]
    
    @patch('app.agents.sql_agent_v2.get_connection')
    @patch('app.agents.sql_agent_v2.get_ner_enhanced_hybrid_schema_snippets')
    @patch.object(SQLAgent, 'llm_manager')
    def test_end_to_end_sql_generation(self, mock_llm_manager, mock_schema, mock_conn):
        """Test end-to-end SQL generation with real-like data"""
        # Mock database connection
        mock_conn.return_value.__enter__.return_value = Mock()
        
        # Mock realistic schema snippets
        mock_schema.return_value = """
## Extracted Entities and Domain Terms:
Domain terms: hasta, cinsiyet

Table: json_admissions, Column: gender (similarity: 0.850)
Column: gender (TEXT) in table json_admissions

Table: json_admissions, Column: * (similarity: 0.750)
Table: json_admissions with columns: id, hadm_id, subject_id, admittime, dischtime, gender, admission_type
"""
        
        # Mock realistic LLM response
        mock_llm_manager.generate_response.return_value = {
            "content": "SELECT gender, COUNT(*) as hasta_sayisi FROM json_admissions GROUP BY gender ORDER BY hasta_sayisi DESC",
            "usage": {"prompt_tokens": 150, "completion_tokens": 25, "total_tokens": 175}
        }
        
        # Test with different questions
        for question in self.test_questions:
            context = AgentContext(
                question=question,
                language="tr",
                max_tokens=300,
                temperature=0.1
            )
            
            response = self.sql_agent.execute(context)
            
            # Verify response structure
            self.assertTrue(response.success)
            self.assertIsNotNone(response.result)
            self.assertIn("sql", response.result)
            self.assertIn("schema_snippets", response.result)
            self.assertIn("usage", response.result)
            self.assertIn("trace_id", response.result)
            
            # Verify SQL quality
            sql = response.result["sql"]
            self.assertIn("SELECT", sql.upper())
            self.assertIn("FROM", sql.upper())
            
            # Verify performance tracking
            self.assertGreater(response.execution_time_ms, 0)
            self.assertIsNotNone(response.trace_id)
    
    @patch('app.agents.sql_agent_v2.get_connection')
    @patch('app.agents.sql_agent_v2.get_ner_enhanced_hybrid_schema_snippets')
    @patch.object(SQLAgent, 'llm_manager')
    def test_ner_enhanced_schema_retrieval(self, mock_llm_manager, mock_schema, mock_conn):
        """Test NER-enhanced schema retrieval integration"""
        # Mock database connection
        mock_conn.return_value.__enter__.return_value = Mock()
        
        # Mock LLM response
        mock_llm_manager.generate_response.return_value = {
            "content": "SELECT * FROM json_admissions WHERE subject_id = 12345",
            "usage": {"prompt_tokens": 100, "completion_tokens": 20, "total_tokens": 120}
        }
        
        # Test with ID-based question
        context = AgentContext(
            question="subject_id 12345 olan hastanın yatış bilgileri?",
            language="tr"
        )
        
        response = self.sql_agent.execute(context)
        
        # Verify NER-enhanced schema was called
        mock_schema.assert_called_once()
        call_args = mock_schema.call_args
        self.assertEqual(call_args[0][1], context.question)  # question parameter
        self.assertEqual(call_args[1]["top_k"], 3)  # top_k parameter
        self.assertEqual(call_args[1]["language_code"], "tr")  # language_code parameter
        
        # Verify response
        self.assertTrue(response.success)
        self.assertIn("subject_id", response.result["sql"])
    
    @patch('app.agents.sql_agent_v2.get_connection')
    @patch('app.agents.sql_agent_v2.get_ner_enhanced_hybrid_schema_snippets')
    @patch.object(SQLAgent, 'llm_manager')
    def test_error_handling_integration(self, mock_llm_manager, mock_schema, mock_conn):
        """Test error handling in integrated system"""
        # Mock database connection error
        mock_conn.side_effect = Exception("Database connection failed")
        
        context = AgentContext(question="Test question", language="tr")
        response = self.sql_agent.execute(context)
        
        # Verify error handling
        self.assertFalse(response.success)
        self.assertIsNone(response.result)
        self.assertIsNotNone(response.error)
        self.assertIn("Database connection failed", response.error)
        
        # Verify error was logged and tracked
        self.assertEqual(self.sql_agent._error_count, 1)
        self.assertEqual(self.sql_agent._sql_generation_count, 0)
    
    @patch('app.agents.sql_agent_v2.get_connection')
    @patch('app.agents.sql_agent_v2.get_ner_enhanced_hybrid_schema_snippets')
    @patch.object(SQLAgent, 'llm_manager')
    def test_performance_monitoring_integration(self, mock_llm_manager, mock_schema, mock_conn):
        """Test performance monitoring in integrated system"""
        # Mock database connection
        mock_conn.return_value.__enter__.return_value = Mock()
        
        # Mock schema and LLM
        mock_schema.return_value = "Test schema"
        mock_llm_manager.generate_response.return_value = {
            "content": "SELECT * FROM table",
            "usage": {"prompt_tokens": 100, "completion_tokens": 20, "total_tokens": 120}
        }
        
        # Execute multiple times
        for i in range(5):
            context = AgentContext(question=f"Test question {i}", language="tr")
            response = self.sql_agent.execute(context)
            self.assertTrue(response.success)
        
        # Verify performance metrics
        stats = self.sql_agent.get_sql_statistics()
        self.assertEqual(stats["total_executions"], 5)
        self.assertEqual(stats["success_rate"], 1.0)
        self.assertEqual(stats["sql_generation_count"], 5)
        self.assertEqual(stats["successful_sql_count"], 5)
        self.assertEqual(stats["sql_success_rate"], 1.0)
        
        # Verify execution times were tracked
        self.assertEqual(len(self.sql_agent._execution_times), 5)
        self.assertGreater(stats["average_execution_time_ms"], 0)
    
    def test_global_function_integration(self):
        """Test global function integration"""
        with patch('app.agents.sql_agent_v2.get_sql_agent') as mock_get_agent:
            mock_agent = Mock()
            mock_response = AgentResponse(
                success=True,
                result={"sql": "SELECT * FROM table"},
                trace_id="test_trace"
            )
            mock_agent.generate_sql.return_value = mock_response
            mock_get_agent.return_value = mock_agent
            
            # Test global function
            response = generate_sql_with_agent(
                "Test question",
                language="tr",
                max_tokens=300,
                user_id="user123",
                session_id="session456"
            )
            
            # Verify function was called correctly
            mock_get_agent.assert_called_once()
            mock_agent.generate_sql.assert_called_once_with(
                "Test question",
                language="tr",
                max_tokens=300,
                user_id="user123",
                session_id="session456"
            )
            
            self.assertEqual(response, mock_response)
    
    @patch('app.agents.sql_agent_v2.get_connection')
    @patch('app.agents.sql_agent_v2.get_ner_enhanced_hybrid_schema_snippets')
    @patch.object(SQLAgent, 'llm_manager')
    def test_different_languages(self, mock_llm_manager, mock_schema, mock_conn):
        """Test agent with different languages"""
        # Mock database connection
        mock_conn.return_value.__enter__.return_value = Mock()
        
        # Mock schema and LLM
        mock_schema.return_value = "Test schema"
        mock_llm_manager.generate_response.return_value = {
            "content": "SELECT * FROM table",
            "usage": {"prompt_tokens": 100, "completion_tokens": 20, "total_tokens": 120}
        }
        
        # Test Turkish
        tr_context = AgentContext(question="Türkçe soru", language="tr")
        tr_response = self.sql_agent.execute(tr_context)
        self.assertTrue(tr_response.success)
        
        # Test English
        en_context = AgentContext(question="English question", language="en")
        en_response = self.sql_agent.execute(en_context)
        self.assertTrue(en_response.success)
        
        # Verify language was passed to schema retrieval
        self.assertEqual(mock_schema.call_count, 2)
        tr_call = mock_schema.call_args_list[0]
        en_call = mock_schema.call_args_list[1]
        
        self.assertEqual(tr_call[1]["language_code"], "tr")
        self.assertEqual(en_call[1]["language_code"], "en")
    
    @patch('app.agents.sql_agent_v2.get_connection')
    @patch('app.agents.sql_agent_v2.get_ner_enhanced_hybrid_schema_snippets')
    @patch.object(SQLAgent, 'llm_manager')
    def test_custom_configuration(self, mock_llm_manager, mock_schema, mock_conn):
        """Test agent with custom configuration"""
        # Create agent with custom config
        config = {
            "top_k": 5,
            "max_sql_length": 2000,
            "language": "en"
        }
        custom_agent = SQLAgent(config)
        
        # Mock database connection
        mock_conn.return_value.__enter__.return_value = Mock()
        
        # Mock schema and LLM
        mock_schema.return_value = "Test schema"
        mock_llm_manager.generate_response.return_value = {
            "content": "SELECT * FROM table",
            "usage": {"prompt_tokens": 100, "completion_tokens": 20, "total_tokens": 120}
        }
        
        # Test with custom agent
        context = AgentContext(question="Test question", language="en")
        response = custom_agent.execute(context)
        
        # Verify custom configuration was used
        self.assertTrue(response.success)
        mock_schema.assert_called_once()
        call_args = mock_schema.call_args
        self.assertEqual(call_args[1]["top_k"], 5)  # Custom top_k
        self.assertEqual(call_args[1]["language_code"], "en")  # Custom language


def run_tests():
    """Run all agent integration tests"""
    # Create test suite
    test_suite = unittest.TestSuite()
    
    # Add test cases
    test_suite.addTest(unittest.makeSuite(TestAgentIntegration))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)
    
    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_tests()
    if success:
        print("\n✅ All agent integration tests passed!")
    else:
        print("\n❌ Some agent integration tests failed!")
        exit(1)
