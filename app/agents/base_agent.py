"""
Base Agent Class for Medical QueryBot

This module provides a base agent class that can be inherited by specific agent types.
It includes common functionality like logging, tracing, error handling, and LLM integration.
"""
import os
import time
import logging
from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass

# Configure logging
logger = logging.getLogger(__name__)


@dataclass
class AgentResponse:
    """Standard response format for all agents"""
    success: bool
    result: Any
    error: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    execution_time_ms: Optional[int] = None
    trace_id: Optional[str] = None


@dataclass
class AgentContext:
    """Context information passed to agents"""
    question: str
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    language: str = "en"
    max_tokens: int = 300
    temperature: float = 0.1
    additional_context: Optional[Dict[str, Any]] = None


class BaseAgent(ABC):
    """
    Base agent class that provides common functionality for all agents.
    
    This class includes:
    - Logging and tracing
    - Error handling
    - LLM integration
    - Response formatting
    - Performance monitoring
    """
    
    def __init__(self, agent_name: str, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the base agent
        
        Args:
            agent_name: Name of the agent (for logging and identification)
            config: Optional configuration dictionary
        """
        self.agent_name = agent_name
        self.config = config or {}
        self.logger = logging.getLogger(f"{__name__}.{agent_name}")
        
        # Initialize LLM manager
        self._llm_manager = None
        self._trace_manager = None
        self._structured_logger = None
        
        # Performance tracking
        self._execution_times = []
        self._success_count = 0
        self._error_count = 0
    
    @property
    def llm_manager(self):
        """Lazy load LLM manager"""
        if self._llm_manager is None:
            from app.llm.llm_manager import get_llm_manager
            self._llm_manager = get_llm_manager()
        return self._llm_manager
    
    @property
    def trace_manager(self):
        """Lazy load trace manager"""
        if self._trace_manager is None:
            from app.utils.tracing import get_trace_manager
            self._trace_manager = get_trace_manager()
        return self._trace_manager
    
    @property
    def structured_logger(self):
        """Lazy load structured logger"""
        if self._structured_logger is None:
            from app.utils.logger import get_structured_logger
            self._structured_logger = get_structured_logger()
        return self._structured_logger
    
    def generate_trace_id(self) -> str:
        """Generate a unique trace ID for this execution"""
        return f"{self.agent_name}_{int(time.time() * 1000)}"
    
    def log_execution_start(self, trace_id: str, context: AgentContext) -> None:
        """Log the start of agent execution"""
        self.logger.info(f"Starting {self.agent_name} execution", extra={
            "trace_id": trace_id,
            "question": context.question,
            "language": context.language
        })
    
    def log_execution_end(self, trace_id: str, success: bool, execution_time_ms: int) -> None:
        """Log the end of agent execution"""
        status = "SUCCESS" if success else "FAILED"
        self.logger.info(f"Completed {self.agent_name} execution", extra={
            "trace_id": trace_id,
            "status": status,
            "execution_time_ms": execution_time_ms
        })
    
    def log_error(self, trace_id: str, error: Exception, context: AgentContext) -> None:
        """Log an error during execution"""
        self.logger.error(f"Error in {self.agent_name}", extra={
            "trace_id": trace_id,
            "error": str(error),
            "question": context.question
        }, exc_info=True)
    
    def update_performance_metrics(self, execution_time_ms: int, success: bool) -> None:
        """Update performance metrics"""
        self._execution_times.append(execution_time_ms)
        if success:
            self._success_count += 1
        else:
            self._error_count += 1
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """Get performance statistics"""
        if not self._execution_times:
            return {
                "total_executions": 0,
                "success_rate": 0.0,
                "average_execution_time_ms": 0.0,
                "min_execution_time_ms": 0.0,
                "max_execution_time_ms": 0.0
            }
        
        total_executions = self._success_count + self._error_count
        success_rate = self._success_count / total_executions if total_executions > 0 else 0.0
        
        return {
            "total_executions": total_executions,
            "success_rate": success_rate,
            "average_execution_time_ms": sum(self._execution_times) / len(self._execution_times),
            "min_execution_time_ms": min(self._execution_times),
            "max_execution_time_ms": max(self._execution_times)
        }
    
    def execute(self, context: AgentContext) -> AgentResponse:
        """
        Main execution method that handles common functionality
        
        Args:
            context: Agent context containing question and parameters
            
        Returns:
            AgentResponse with result or error
        """
        trace_id = self.generate_trace_id()
        start_time = time.perf_counter()
        
        try:
            # Log execution start
            self.log_execution_start(trace_id, context)
            
            # Execute the specific agent logic
            result = self._execute_agent_logic(context, trace_id)
            
            # Calculate execution time
            execution_time_ms = int((time.perf_counter() - start_time) * 1000)
            
            # Log successful execution
            self.log_execution_end(trace_id, True, execution_time_ms)
            self.update_performance_metrics(execution_time_ms, True)
            
            # Return successful response
            return AgentResponse(
                success=True,
                result=result,
                metadata={
                    "agent_name": self.agent_name,
                    "execution_time_ms": execution_time_ms,
                    "trace_id": trace_id
                },
                execution_time_ms=execution_time_ms,
                trace_id=trace_id
            )
            
        except Exception as e:
            # Calculate execution time
            execution_time_ms = int((time.perf_counter() - start_time) * 1000)
            
            # Log error
            self.log_error(trace_id, e, context)
            self.log_execution_end(trace_id, False, execution_time_ms)
            self.update_performance_metrics(execution_time_ms, False)
            
            # Return error response
            return AgentResponse(
                success=False,
                result=None,
                error=str(e),
                metadata={
                    "agent_name": self.agent_name,
                    "execution_time_ms": execution_time_ms,
                    "trace_id": trace_id
                },
                execution_time_ms=execution_time_ms,
                trace_id=trace_id
            )
    
    @abstractmethod
    def _execute_agent_logic(self, context: AgentContext, trace_id: str) -> Any:
        """
        Abstract method that must be implemented by subclasses
        
        Args:
            context: Agent context
            trace_id: Trace ID for this execution
            
        Returns:
            The result of the agent's specific logic
        """
        pass
    
    def validate_context(self, context: AgentContext) -> bool:
        """
        Validate the agent context
        
        Args:
            context: Agent context to validate
            
        Returns:
            True if valid, False otherwise
        """
        if not context.question or not context.question.strip():
            self.logger.warning("Empty question provided")
            return False
        
        if context.max_tokens <= 0:
            self.logger.warning("Invalid max_tokens value")
            return False
        
        if not 0 <= context.temperature <= 2:
            self.logger.warning("Invalid temperature value")
            return False
        
        return True
    
    def get_agent_info(self) -> Dict[str, Any]:
        """Get information about this agent"""
        return {
            "agent_name": self.agent_name,
            "config": self.config,
            "performance_stats": self.get_performance_stats()
        }
