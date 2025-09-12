"""
Structured JSON logging utility

Features:
- JSON formatted logs
- Trace ID support
- Performance metrics
- Error tracking
- Query logging
"""

import json
import logging
import time
from datetime import datetime
from typing import Dict, Any, Optional
from pathlib import Path
import uuid

class StructuredLogger:
    """Structured JSON logger for the application"""
    
    def __init__(self, log_file: str = "logs/app.log"):
        self.log_file = Path(log_file)
        self.log_file.parent.mkdir(exist_ok=True)
        
        # Setup logger
        self.logger = logging.getLogger("medical_querybot")
        self.logger.setLevel(logging.INFO)
        
        # Remove existing handlers
        for handler in self.logger.handlers[:]:
            self.logger.removeHandler(handler)
        
        # File handler (write plain message which we provide as JSON)
        file_handler = logging.FileHandler(self.log_file)
        file_handler.setLevel(logging.INFO)
        file_handler.setFormatter(logging.Formatter('%(message)s'))
        
        # Optional console handler (simple output)
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(logging.Formatter('%(message)s'))
        
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)
    
    def log_query_start(self, trace_id: str, question: str, user_id: Optional[str] = None) -> None:
        """Log query start"""
        log_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": "INFO",
            "event": "query_start",
            "trace_id": trace_id,
            "question": question,
            "user_id": user_id,
            "component": "query_pipeline"
        }
        self.logger.info(json.dumps(log_data))
    
    def log_query_end(self, trace_id: str, success: bool, execution_time_ms: int, 
                     rows_returned: int, error: Optional[str] = None) -> None:
        """Log query end"""
        log_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": "INFO" if success else "ERROR",
            "event": "query_end",
            "trace_id": trace_id,
            "success": success,
            "execution_time_ms": execution_time_ms,
            "rows_returned": rows_returned,
            "error": error,
            "component": "query_pipeline"
        }
        self.logger.info(json.dumps(log_data))
    
    def log_sql_generation(self, trace_id: str, question: str, sql: str, 
                          llm_mode: str, tokens_used: int, generation_time_ms: int) -> None:
        """Log SQL generation"""
        log_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": "INFO",
            "event": "sql_generation",
            "trace_id": trace_id,
            "question": question,
            "sql": sql,
            "llm_mode": llm_mode,
            "tokens_used": tokens_used,
            "generation_time_ms": generation_time_ms,
            "component": "sql_agent"
        }
        self.logger.info(json.dumps(log_data))
    
    def log_sql_execution(self, trace_id: str, sql: str, execution_time_ms: int, 
                         rows_returned: int, error: Optional[str] = None) -> None:
        """Log SQL execution"""
        log_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": "INFO" if not error else "ERROR",
            "event": "sql_execution",
            "trace_id": trace_id,
            "sql": sql,
            "execution_time_ms": execution_time_ms,
            "rows_returned": rows_returned,
            "error": error,
            "component": "sql_executor"
        }
        self.logger.info(json.dumps(log_data))
    
    def log_answer_summarization(self, trace_id: str, question: str, rows_count: int,
                                tokens_used: int, summarization_time_ms: int) -> None:
        """Log answer summarization"""
        log_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": "INFO",
            "event": "answer_summarization",
            "trace_id": trace_id,
            "question": question,
            "rows_count": rows_count,
            "tokens_used": tokens_used,
            "summarization_time_ms": summarization_time_ms,
            "component": "answer_summarizer"
        }
        self.logger.info(json.dumps(log_data))
    
    def log_security_event(self, trace_id: str, event_type: str, details: Dict[str, Any]) -> None:
        """Log security events"""
        log_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": "WARNING",
            "event": "security_event",
            "trace_id": trace_id,
            "event_type": event_type,
            "details": details,
            "component": "security"
        }
        self.logger.warning(json.dumps(log_data))
    
    def log_performance_metric(self, trace_id: str, metric_name: str, value: float, 
                              unit: str, metadata: Optional[Dict[str, Any]] = None) -> None:
        """Log performance metrics"""
        log_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": "INFO",
            "event": "performance_metric",
            "trace_id": trace_id,
            "metric_name": metric_name,
            "value": value,
            "unit": unit,
            "metadata": metadata or {},
            "component": "performance_monitor"
        }
        self.logger.info(json.dumps(log_data))
    
    def log_error(self, trace_id: str, error: Exception, context: Optional[Dict[str, Any]] = None) -> None:
        """Log errors with context"""
        log_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": "ERROR",
            "event": "error",
            "trace_id": trace_id,
            "error_type": type(error).__name__,
            "error_message": str(error),
            "context": context or {},
            "component": "error_handler"
        }
        self.logger.error(json.dumps(log_data))


class JSONFormatter(logging.Formatter):
    """Custom formatter for JSON logs"""
    
    def format(self, record):
        # If the record already has a JSON message, return it
        if hasattr(record, 'json_message'):
            return record.json_message
        
        # Otherwise, format as JSON
        log_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno
        }
        return json.dumps(log_data)


# Global logger instance
_structured_logger = None

def get_structured_logger() -> StructuredLogger:
    """Get the global structured logger instance"""
    global _structured_logger
    if _structured_logger is None:
        _structured_logger = StructuredLogger()
    return _structured_logger

def generate_trace_id() -> str:
    """Generate a unique trace ID"""
    return str(uuid.uuid4())

def log_query_pipeline_start(question: str, user_id: Optional[str] = None) -> str:
    """Start logging a query pipeline and return trace ID"""
    trace_id = generate_trace_id()
    logger = get_structured_logger()
    logger.log_query_start(trace_id, question, user_id)
    return trace_id

def log_query_pipeline_end(trace_id: str, success: bool, execution_time_ms: int, 
                          rows_returned: int, error: Optional[str] = None) -> None:
    """End logging a query pipeline"""
    logger = get_structured_logger()
    logger.log_query_end(trace_id, success, execution_time_ms, rows_returned, error)
