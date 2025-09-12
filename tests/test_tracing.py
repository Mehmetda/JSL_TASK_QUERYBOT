"""
Test distributed tracing functionality

Run:
  python tests/test_tracing.py
"""
import sys
from pathlib import Path
import time
import tempfile
import os

# Add project root to Python path
CURRENT = Path(__file__).resolve().parent
PROJECT_ROOT = CURRENT.parent
sys.path.insert(0, str(PROJECT_ROOT))

from app.utils.tracing import (
    TraceManager, get_trace_manager, start_trace, end_trace, 
    get_current_trace_id, add_trace_metadata, trace_function, with_trace
)


def test_trace_manager_creation():
    """Test trace manager creation"""
    print("Testing trace manager creation...")
    
    try:
        manager = TraceManager()
        assert manager is not None
        assert isinstance(manager.active_traces, dict)
        assert len(manager.active_traces) == 0
        print("✅ Trace manager created successfully")
        
    except Exception as e:
        print(f"❌ Trace manager creation failed: {e}")
        return False
    
    return True


def test_trace_lifecycle():
    """Test trace start and end"""
    print("Testing trace lifecycle...")
    
    try:
        manager = TraceManager()
        
        # Start trace
        trace_id = manager.start_trace(user_id="test_user", metadata={"test": "data"})
        assert trace_id is not None
        assert trace_id in manager.active_traces
        
        # Check trace info
        trace_info = manager.get_trace_info(trace_id)
        assert trace_info is not None
        assert trace_info.user_id == "test_user"
        assert trace_info.metadata["test"] == "data"
        
        # End trace
        summary = manager.end_trace(trace_id)
        assert summary is not None
        assert summary["trace_id"] == trace_id
        assert summary["user_id"] == "test_user"
        assert summary["duration_ms"] > 0
        assert trace_id not in manager.active_traces
        
        print("✅ Trace lifecycle works")
        
    except Exception as e:
        print(f"❌ Trace lifecycle failed: {e}")
        return False
    
    return True


def test_trace_metadata():
    """Test trace metadata management"""
    print("Testing trace metadata...")
    
    try:
        manager = TraceManager()
        trace_id = manager.start_trace()
        
        # Add metadata
        assert manager.add_metadata(trace_id, "key1", "value1") == True
        assert manager.add_metadata(trace_id, "key2", 42) == True
        
        # Check metadata
        trace_info = manager.get_trace_info(trace_id)
        assert trace_info.metadata["key1"] == "value1"
        assert trace_info.metadata["key2"] == 42
        
        # Test invalid trace ID
        assert manager.add_metadata("invalid_id", "key", "value") == False
        
        manager.end_trace(trace_id)
        print("✅ Trace metadata works")
        
    except Exception as e:
        print(f"❌ Trace metadata failed: {e}")
        return False
    
    return True


def test_global_functions():
    """Test global trace functions"""
    print("Testing global trace functions...")
    
    try:
        # Test global manager
        manager = get_trace_manager()
        assert manager is not None
        
        # Test start/end trace
        trace_id = start_trace(user_id="global_user")
        assert trace_id is not None
        assert get_current_trace_id() == trace_id
        
        # Test metadata
        assert add_trace_metadata("global_key", "global_value") == True
        
        # Test end trace
        summary = end_trace(trace_id)
        assert summary is not None
        assert get_current_trace_id() is None
        
        print("✅ Global trace functions work")
        
    except Exception as e:
        print(f"❌ Global trace functions failed: {e}")
        return False
    
    return True


def test_trace_decorator():
    """Test trace function decorator"""
    print("Testing trace decorator...")
    
    try:
        @trace_function
        def test_function(x, y):
            time.sleep(0.01)  # Small delay
            return x + y
        
        # Call function
        result = test_function(5, 3)
        assert result == 8
        
        # Check that trace was created and ended
        manager = get_trace_manager()
        assert len(manager.active_traces) == 0  # Should be cleaned up
        
        print("✅ Trace decorator works")
        
    except Exception as e:
        print(f"❌ Trace decorator failed: {e}")
        return False
    
    return True


def test_trace_context_manager():
    """Test trace context manager"""
    print("Testing trace context manager...")
    
    try:
        with with_trace(user_id="context_user", metadata={"context": "test"}) as trace_id:
            assert trace_id is not None
            assert get_current_trace_id() == trace_id
            
            # Add metadata
            add_trace_metadata("context_key", "context_value")
            
            # Check trace info
            manager = get_trace_manager()
            trace_info = manager.get_trace_info(trace_id)
            assert trace_info.user_id == "context_user"
            assert trace_info.metadata["context"] == "test"
            assert trace_info.metadata["context_key"] == "context_value"
        
        # Trace should be ended after context
        assert get_current_trace_id() is None
        manager = get_trace_manager()
        assert trace_id not in manager.active_traces
        
        print("✅ Trace context manager works")
        
    except Exception as e:
        print(f"❌ Trace context manager failed: {e}")
        return False
    
    return True


def test_trace_cleanup():
    """Test trace cleanup functionality"""
    print("Testing trace cleanup...")
    
    try:
        manager = TraceManager()
        
        # Create some traces
        trace1 = manager.start_trace()
        trace2 = manager.start_trace()
        
        # Manually set old start time for trace1
        manager.active_traces[trace1].start_time = time.perf_counter() - 3700  # 1 hour + 100 seconds ago
        
        # Cleanup expired traces (older than 1 hour)
        cleaned = manager.cleanup_expired_traces(max_age_seconds=3600)
        assert cleaned == 1
        assert trace1 not in manager.active_traces
        assert trace2 in manager.active_traces
        
        # Clean up remaining trace
        manager.end_trace(trace2)
        
        print("✅ Trace cleanup works")
        
    except Exception as e:
        print(f"❌ Trace cleanup failed: {e}")
        return False
    
    return True


def test_trace_error_handling():
    """Test trace error handling"""
    print("Testing trace error handling...")
    
    try:
        @trace_function
        def error_function():
            raise ValueError("Test error")
        
        # Call function that raises error
        try:
            error_function()
        except ValueError:
            pass  # Expected
        
        # Check that trace was still cleaned up
        manager = get_trace_manager()
        assert len(manager.active_traces) == 0
        
        print("✅ Trace error handling works")
        
    except Exception as e:
        print(f"❌ Trace error handling failed: {e}")
        return False
    
    return True


def main():
    """Run all tracing tests"""
    print("🧪 Testing Distributed Tracing")
    print("=" * 50)
    
    tests = [
        test_trace_manager_creation,
        test_trace_lifecycle,
        test_trace_metadata,
        test_global_functions,
        test_trace_decorator,
        test_trace_context_manager,
        test_trace_cleanup,
        test_trace_error_handling
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
        print()
    
    print("=" * 50)
    print(f"📊 Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tracing tests passed!")
        return True
    else:
        print("❌ Some tests failed")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
