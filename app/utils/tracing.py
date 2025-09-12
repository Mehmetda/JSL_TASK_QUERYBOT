"""
Distributed tracing utilities

Features:
- Trace ID generation and management
- Context propagation
- Performance tracking
- Request correlation
"""

import uuid
import time
from typing import Optional, Dict, Any
from contextvars import ContextVar
from dataclasses import dataclass
from datetime import datetime

# Context variable for trace ID
trace_context: ContextVar[Optional[str]] = ContextVar('trace_id', default=None)

@dataclass
class TraceInfo:
    """Trace information container"""
    trace_id: str
    start_time: float
    parent_trace_id: Optional[str] = None
    user_id: Optional[str] = None
    request_id: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

class TraceManager:
    """Manages distributed tracing"""
    
    def __init__(self):
        self.active_traces: Dict[str, TraceInfo] = {}
    
    def start_trace(self, 
                   trace_id: Optional[str] = None,
                   parent_trace_id: Optional[str] = None,
                   user_id: Optional[str] = None,
                   request_id: Optional[str] = None,
                   metadata: Optional[Dict[str, Any]] = None) -> str:
        """Start a new trace"""
        if trace_id is None:
            trace_id = self.generate_trace_id()
        
        trace_info = TraceInfo(
            trace_id=trace_id,
            start_time=time.perf_counter(),
            parent_trace_id=parent_trace_id,
            user_id=user_id,
            request_id=request_id,
            metadata=metadata or {}
        )
        
        self.active_traces[trace_id] = trace_info
        trace_context.set(trace_id)
        
        return trace_id
    
    def end_trace(self, trace_id: str) -> Optional[Dict[str, Any]]:
        """End a trace and return summary"""
        if trace_id not in self.active_traces:
            return None
        
        trace_info = self.active_traces[trace_id]
        duration_ms = (time.perf_counter() - trace_info.start_time) * 1000
        
        summary = {
            "trace_id": trace_id,
            "duration_ms": duration_ms,
            "parent_trace_id": trace_info.parent_trace_id,
            "user_id": trace_info.user_id,
            "request_id": trace_info.request_id,
            "metadata": trace_info.metadata,
            "start_time": datetime.fromtimestamp(trace_info.start_time).isoformat(),
            "end_time": datetime.now().isoformat()
        }
        
        del self.active_traces[trace_id]
        
        # Clear context if this was the current trace
        if trace_context.get() == trace_id:
            trace_context.set(None)
        
        return summary
    
    def get_current_trace_id(self) -> Optional[str]:
        """Get current trace ID from context"""
        return trace_context.get()
    
    def get_trace_info(self, trace_id: str) -> Optional[TraceInfo]:
        """Get trace information"""
        return self.active_traces.get(trace_id)
    
    def add_metadata(self, trace_id: str, key: str, value: Any) -> bool:
        """Add metadata to a trace"""
        if trace_id not in self.active_traces:
            return False
        
        if self.active_traces[trace_id].metadata is None:
            self.active_traces[trace_id].metadata = {}
        
        self.active_traces[trace_id].metadata[key] = value
        return True
    
    def generate_trace_id(self) -> str:
        """Generate a new trace ID"""
        return str(uuid.uuid4())
    
    def get_all_traces(self) -> Dict[str, TraceInfo]:
        """Get all active traces"""
        return self.active_traces.copy()
    
    def cleanup_expired_traces(self, max_age_seconds: int = 3600) -> int:
        """Clean up traces older than max_age_seconds"""
        current_time = time.perf_counter()
        expired_traces = []
        
        for trace_id, trace_info in self.active_traces.items():
            if current_time - trace_info.start_time > max_age_seconds:
                expired_traces.append(trace_id)
        
        for trace_id in expired_traces:
            del self.active_traces[trace_id]
        
        return len(expired_traces)


# Global trace manager instance
_trace_manager = None

def get_trace_manager() -> TraceManager:
    """Get the global trace manager instance"""
    global _trace_manager
    if _trace_manager is None:
        _trace_manager = TraceManager()
    return _trace_manager

def start_trace(trace_id: Optional[str] = None, **kwargs) -> str:
    """Start a new trace"""
    manager = get_trace_manager()
    return manager.start_trace(trace_id, **kwargs)

def end_trace(trace_id: str) -> Optional[Dict[str, Any]]:
    """End a trace"""
    manager = get_trace_manager()
    return manager.end_trace(trace_id)

def get_current_trace_id() -> Optional[str]:
    """Get current trace ID"""
    manager = get_trace_manager()
    return manager.get_current_trace_id()

def add_trace_metadata(key: str, value: Any, trace_id: Optional[str] = None) -> bool:
    """Add metadata to current or specified trace"""
    manager = get_trace_manager()
    
    if trace_id is None:
        trace_id = get_current_trace_id()
    
    if trace_id is None:
        return False
    
    return manager.add_metadata(trace_id, key, value)

def trace_function(func):
    """Decorator to automatically trace function execution"""
    def wrapper(*args, **kwargs):
        # Start trace
        trace_id = start_trace()
        
        try:
            # Add function info to metadata
            add_trace_metadata("function", func.__name__)
            add_trace_metadata("module", func.__module__)
            
            # Execute function
            result = func(*args, **kwargs)
            
            # Add result info to metadata
            add_trace_metadata("success", True)
            if hasattr(result, '__len__'):
                add_trace_metadata("result_length", len(result))
            
            return result
            
        except Exception as e:
            # Add error info to metadata
            add_trace_metadata("success", False)
            add_trace_metadata("error", str(e))
            add_trace_metadata("error_type", type(e).__name__)
            raise
            
        finally:
            # End trace
            end_trace(trace_id)
    
    return wrapper

def with_trace(trace_id: Optional[str] = None, **kwargs):
    """Context manager for tracing"""
    class TraceContext:
        def __init__(self, trace_id, **kwargs):
            self.trace_id = trace_id
            self.kwargs = kwargs
        
        def __enter__(self):
            self.trace_id = start_trace(self.trace_id, **self.kwargs)
            return self.trace_id
        
        def __exit__(self, exc_type, exc_val, exc_tb):
            if self.trace_id:
                end_trace(self.trace_id)
    
    return TraceContext(trace_id, **kwargs)
