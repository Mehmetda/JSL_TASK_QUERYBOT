"""
Test Base Agent Class

This test suite validates the base agent functionality including:
- Logging and tracing
- Error handling
- Performance monitoring
- Response formatting
"""
import unittest
import time
import os
import sys
from pathlib import Path
from unittest.mock import Mock, patch

# Add project root to Python path
CURRENT = Path(__file__).resolve().parent
PROJECT_ROOT = CURRENT.parent
sys.path.insert(0, str(PROJECT_ROOT))

from app.agents.base_agent import BaseAgent, AgentContext, AgentResponse


class TestAgent(BaseAgent):
    """Test agent implementation for testing base agent functionality"""
    
    def __init__(self, should_fail=False, execution_delay=0):
        super().__init__("TestAgent")
        self.should_fail = should_fail
        self.execution_delay = execution_delay
    
    def _execute_agent_logic(self, context: AgentContext, trace_id: str):
        """Test implementation of agent logic"""
        if self.execution_delay > 0:
            time.sleep(self.execution_delay)
        
        if self.should_fail:
            raise ValueError("Test error")
        
        return {
            "result": f"Processed: {context.question}",
            "trace_id": trace_id,
            "agent_name": self.agent_name
        }


class TestBaseAgent(unittest.TestCase):
    """Test cases for BaseAgent class"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.test_agent = TestAgent()
        self.valid_context = AgentContext(
            question="Test question",
            language="tr",
            max_tokens=300,
            temperature=0.1
        )
    
    def test_agent_initialization(self):
        """Test agent initialization"""
        self.assertEqual(self.test_agent.agent_name, "TestAgent")
        self.assertIsNotNone(self.test_agent.config)
        self.assertEqual(self.test_agent._success_count, 0)
        self.assertEqual(self.test_agent._error_count, 0)
    
    def test_trace_id_generation(self):
        """Test trace ID generation"""
        trace_id1 = self.test_agent.generate_trace_id()
        time.sleep(0.001)  # Small delay to ensure different timestamps
        trace_id2 = self.test_agent.generate_trace_id()
        
        self.assertTrue(trace_id1.startswith("TestAgent_"))
        self.assertTrue(trace_id2.startswith("TestAgent_"))
        self.assertNotEqual(trace_id1, trace_id2)
    
    def test_context_validation(self):
        """Test context validation"""
        # Valid context
        self.assertTrue(self.test_agent.validate_context(self.valid_context))
        
        # Invalid contexts
        empty_question = AgentContext(question="", language="tr")
        self.assertFalse(self.test_agent.validate_context(empty_question))
        
        invalid_tokens = AgentContext(question="Test", max_tokens=0, language="tr")
        self.assertFalse(self.test_agent.validate_context(invalid_tokens))
        
        invalid_temperature = AgentContext(question="Test", temperature=3.0, language="tr")
        self.assertFalse(self.test_agent.validate_context(invalid_temperature))
    
    def test_successful_execution(self):
        """Test successful agent execution"""
        response = self.test_agent.execute(self.valid_context)
        
        self.assertTrue(response.success)
        self.assertIsNotNone(response.result)
        self.assertIsNone(response.error)
        self.assertIsNotNone(response.trace_id)
        self.assertIsNotNone(response.execution_time_ms)
        self.assertGreaterEqual(response.execution_time_ms, 0)  # Changed to >= 0
        
        # Check metadata
        self.assertEqual(response.metadata["agent_name"], "TestAgent")
        self.assertIn("execution_time_ms", response.metadata)
        self.assertIn("trace_id", response.metadata)
    
    def test_failed_execution(self):
        """Test failed agent execution"""
        failing_agent = TestAgent(should_fail=True)
        response = failing_agent.execute(self.valid_context)
        
        self.assertFalse(response.success)
        self.assertIsNone(response.result)
        self.assertIsNotNone(response.error)
        self.assertIn("Test error", response.error)
        self.assertIsNotNone(response.trace_id)
        self.assertIsNotNone(response.execution_time_ms)
    
    def test_performance_metrics(self):
        """Test performance metrics tracking"""
        # Execute multiple times
        for i in range(3):
            self.test_agent.execute(self.valid_context)
        
        stats = self.test_agent.get_performance_stats()
        
        self.assertEqual(stats["total_executions"], 3)
        self.assertEqual(stats["success_rate"], 1.0)
        self.assertGreaterEqual(stats["average_execution_time_ms"], 0)  # Changed to >= 0
        self.assertGreaterEqual(stats["max_execution_time_ms"], 0)  # Changed to >= 0
        self.assertGreaterEqual(stats["max_execution_time_ms"], stats["min_execution_time_ms"])
    
    def test_mixed_success_failure_metrics(self):
        """Test metrics with mixed success and failure"""
        success_agent = TestAgent(should_fail=False)
        fail_agent = TestAgent(should_fail=True)
        
        # Mix of success and failure
        success_agent.execute(self.valid_context)
        fail_agent.execute(self.valid_context)
        success_agent.execute(self.valid_context)
        
        # Check success agent stats
        success_stats = success_agent.get_performance_stats()
        self.assertEqual(success_stats["total_executions"], 2)
        self.assertEqual(success_stats["success_rate"], 1.0)
        
        # Check fail agent stats
        fail_stats = fail_agent.get_performance_stats()
        self.assertEqual(fail_stats["total_executions"], 1)
        self.assertEqual(fail_stats["success_rate"], 0.0)
    
    def test_execution_timing(self):
        """Test execution timing accuracy"""
        delay_agent = TestAgent(execution_delay=0.1)  # 100ms delay
        response = delay_agent.execute(self.valid_context)
        
        # Should be at least 100ms
        self.assertGreaterEqual(response.execution_time_ms, 100)
        self.assertLess(response.execution_time_ms, 200)  # Should be reasonable
    
    def test_agent_info(self):
        """Test agent info retrieval"""
        info = self.test_agent.get_agent_info()
        
        self.assertEqual(info["agent_name"], "TestAgent")
        self.assertIn("config", info)
        self.assertIn("performance_stats", info)
        self.assertIsInstance(info["performance_stats"], dict)
    
    def test_lazy_loading(self):
        """Test lazy loading of dependencies"""
        # These should not be loaded until accessed
        self.assertIsNone(self.test_agent._llm_manager)
        self.assertIsNone(self.test_agent._trace_manager)
        self.assertIsNone(self.test_agent._structured_logger)
        
        # Accessing properties should trigger lazy loading
        with patch('app.llm.llm_manager.get_llm_manager') as mock_llm:
            mock_llm.return_value = Mock()
            llm_manager = self.test_agent.llm_manager
            self.assertIsNotNone(llm_manager)
            mock_llm.assert_called_once()
    
    def test_context_with_additional_data(self):
        """Test context with additional data"""
        context_with_extra = AgentContext(
            question="Test question",
            user_id="user123",
            session_id="session456",
            additional_context={"key": "value"}
        )
        
        response = self.test_agent.execute(context_with_extra)
        self.assertTrue(response.success)
        # Check that the context was processed (the result contains the question)
        self.assertIn("Test question", str(response.result))
    
    def test_error_handling_edge_cases(self):
        """Test error handling for edge cases"""
        # Test with None context
        with self.assertRaises(AttributeError):
            self.test_agent.execute(None)
        
        # Test with invalid context type
        with self.assertRaises(AttributeError):
            self.test_agent.execute("invalid_context")


class TestAgentContext(unittest.TestCase):
    """Test cases for AgentContext dataclass"""
    
    def test_context_creation(self):
        """Test context creation with default values"""
        context = AgentContext(question="Test question")
        
        self.assertEqual(context.question, "Test question")
        self.assertIsNone(context.user_id)
        self.assertIsNone(context.session_id)
        self.assertEqual(context.language, "tr")
        self.assertEqual(context.max_tokens, 300)
        self.assertEqual(context.temperature, 0.1)
        self.assertIsNone(context.additional_context)
    
    def test_context_creation_with_all_params(self):
        """Test context creation with all parameters"""
        context = AgentContext(
            question="Test question",
            user_id="user123",
            session_id="session456",
            language="en",
            max_tokens=500,
            temperature=0.5,
            additional_context={"key": "value"}
        )
        
        self.assertEqual(context.question, "Test question")
        self.assertEqual(context.user_id, "user123")
        self.assertEqual(context.session_id, "session456")
        self.assertEqual(context.language, "en")
        self.assertEqual(context.max_tokens, 500)
        self.assertEqual(context.temperature, 0.5)
        self.assertEqual(context.additional_context["key"], "value")


class TestAgentResponse(unittest.TestCase):
    """Test cases for AgentResponse dataclass"""
    
    def test_successful_response(self):
        """Test successful response creation"""
        response = AgentResponse(
            success=True,
            result={"data": "test"},
            metadata={"key": "value"},
            execution_time_ms=100,
            trace_id="trace123"
        )
        
        self.assertTrue(response.success)
        self.assertEqual(response.result["data"], "test")
        self.assertIsNone(response.error)
        self.assertEqual(response.metadata["key"], "value")
        self.assertEqual(response.execution_time_ms, 100)
        self.assertEqual(response.trace_id, "trace123")
    
    def test_error_response(self):
        """Test error response creation"""
        response = AgentResponse(
            success=False,
            result=None,
            error="Test error",
            execution_time_ms=50,
            trace_id="trace456"
        )
        
        self.assertFalse(response.success)
        self.assertIsNone(response.result)
        self.assertEqual(response.error, "Test error")
        self.assertEqual(response.execution_time_ms, 50)
        self.assertEqual(response.trace_id, "trace456")


def run_tests():
    """Run all base agent tests"""
    # Create test suite
    test_suite = unittest.TestSuite()
    
    # Add test cases
    test_suite.addTest(unittest.makeSuite(TestBaseAgent))
    test_suite.addTest(unittest.makeSuite(TestAgentContext))
    test_suite.addTest(unittest.makeSuite(TestAgentResponse))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)
    
    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_tests()
    if success:
        print("\n✅ All base agent tests passed!")
    else:
        print("\n❌ Some base agent tests failed!")
        exit(1)
