"""
Test query history functionality

Run:
  python tests/test_query_history.py
"""
import sys
from pathlib import Path
import tempfile
import os
from datetime import datetime, timedelta

# Add project root to Python path
CURRENT = Path(__file__).resolve().parent
PROJECT_ROOT = CURRENT.parent
sys.path.insert(0, str(PROJECT_ROOT))

from app.history.query_history import QueryHistoryManager, QueryHistoryEntry
from app.models.query_models import QueryResponse, QueryRequest, QueryMetadata, ValidationInfo, DatabaseInfo, PerformanceInfo, SecurityInfo, QueryType, ComplexityLevel, ValidationStatus


def test_history_manager_creation():
    """Test history manager creation"""
    print("Testing history manager creation...")
    
    try:
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = os.path.join(temp_dir, "test_history.db")
            manager = QueryHistoryManager(db_path)
            
            assert manager is not None
            assert os.path.exists(db_path)
            print("✅ History manager created successfully")
            
    except Exception as e:
        print(f"❌ History manager creation failed: {e}")
        return False
    
    return True


def test_save_query():
    """Test saving queries to history"""
    print("Testing save query...")
    
    try:
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = os.path.join(temp_dir, "test_history.db")
            manager = QueryHistoryManager(db_path)
            
            # Create test query response
            query_response = QueryResponse(
                sql="SELECT * FROM test",
                answer="Test answer",
                meta=QueryMetadata(
                    results={"row_count": 1, "columns": ["id"]},
                    validation=ValidationInfo(
                        is_valid=True,
                        error=None,
                        sql_safety=ValidationStatus.PASSED,
                        retried=False
                    ),
                    database=DatabaseInfo(
                        tables_used=["test"],
                        query_type=QueryType.SELECT,
                        complexity=ComplexityLevel.SIMPLE
                    ),
                    performance=PerformanceInfo(
                        rows_returned=1,
                        columns_returned=1,
                        data_size_estimate="10 characters",
                        execution_ms=50
                    ),
                    security=SecurityInfo(
                        tables_accessed=["test"],
                        security_checks_passed=True,
                        blocked_operations=[]
                    )
                ),
                success=True,
                trace_id="test-trace-123"
            )
            
            # Create test request
            request = QueryRequest(
                question="Test question",
                user_id="test_user"
            )
            
            # Save query
            entry_id = manager.save_query(query_response, request)
            assert entry_id is not None
            assert entry_id > 0
            
            print("✅ Save query works")
            
    except Exception as e:
        print(f"❌ Save query failed: {e}")
        return False
    
    return True


def test_get_query_history():
    """Test retrieving query history"""
    print("Testing get query history...")
    
    try:
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = os.path.join(temp_dir, "test_history.db")
            manager = QueryHistoryManager(db_path)
            
            # Save multiple test queries
            for i in range(5):
                query_response = QueryResponse(
                    sql=f"SELECT * FROM test{i}",
                    answer=f"Test answer {i}",
                    meta=QueryMetadata(
                        results={"row_count": i, "columns": ["id"]},
                        validation=ValidationInfo(
                            is_valid=True,
                            error=None,
                            sql_safety=ValidationStatus.PASSED,
                            retried=False
                        ),
                        database=DatabaseInfo(
                            tables_used=[f"test{i}"],
                            query_type=QueryType.SELECT,
                            complexity=ComplexityLevel.SIMPLE
                        ),
                        performance=PerformanceInfo(
                            rows_returned=i,
                            columns_returned=1,
                            data_size_estimate="10 characters",
                            execution_ms=50 + i
                        ),
                        security=SecurityInfo(
                            tables_accessed=[f"test{i}"],
                            security_checks_passed=True,
                            blocked_operations=[]
                        )
                    ),
                    success=True,
                    trace_id=f"test-trace-{i}"
                )
                
                request = QueryRequest(
                    question=f"Test question {i}",
                    user_id="test_user"
                )
                
                manager.save_query(query_response, request)
            
            # Get history
            history = manager.get_query_history(limit=10)
            assert len(history) == 5
            assert all(isinstance(entry, QueryHistoryEntry) for entry in history)
            
            # Check ordering (should be newest first)
            assert history[0].question == "Test question 4"
            assert history[4].question == "Test question 0"
            
            print("✅ Get query history works")
            
    except Exception as e:
        print(f"❌ Get query history failed: {e}")
        return False
    
    return True


def test_get_query_by_id():
    """Test getting query by ID"""
    print("Testing get query by ID...")
    
    try:
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = os.path.join(temp_dir, "test_history.db")
            manager = QueryHistoryManager(db_path)
            
            # Save a test query
            query_response = QueryResponse(
                sql="SELECT * FROM test",
                answer="Test answer",
                meta=QueryMetadata(
                    results={"row_count": 1, "columns": ["id"]},
                    validation=ValidationInfo(
                        is_valid=True,
                        error=None,
                        sql_safety=ValidationStatus.PASSED,
                        retried=False
                    ),
                    database=DatabaseInfo(
                        tables_used=["test"],
                        query_type=QueryType.SELECT,
                        complexity=ComplexityLevel.SIMPLE
                    ),
                    performance=PerformanceInfo(
                        rows_returned=1,
                        columns_returned=1,
                        data_size_estimate="10 characters",
                        execution_ms=50
                    ),
                    security=SecurityInfo(
                        tables_accessed=["test"],
                        security_checks_passed=True,
                        blocked_operations=[]
                    )
                ),
                success=True,
                trace_id="test-trace-123"
            )
            
            request = QueryRequest(question="Test question")
            entry_id = manager.save_query(query_response, request)
            
            # Get query by ID
            entry = manager.get_query_by_id(entry_id)
            assert entry is not None
            assert entry.id == entry_id
            assert entry.question == "Test question"
            assert entry.sql == "SELECT * FROM test"
            assert entry.answer == "Test answer"
            
            # Test non-existent ID
            non_existent = manager.get_query_by_id(99999)
            assert non_existent is None
            
            print("✅ Get query by ID works")
            
    except Exception as e:
        print(f"❌ Get query by ID failed: {e}")
        return False
    
    return True


def test_query_stats():
    """Test query statistics"""
    print("Testing query statistics...")
    
    try:
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = os.path.join(temp_dir, "test_history.db")
            manager = QueryHistoryManager(db_path)
            
            # Save test queries with different success rates
            for i in range(10):
                success = i < 8  # 80% success rate
                query_response = QueryResponse(
                    sql=f"SELECT * FROM test{i}",
                    answer=f"Test answer {i}",
                    meta=QueryMetadata(
                        results={"row_count": i, "columns": ["id"]},
                        validation=ValidationInfo(
                            is_valid=success,
                            error=None if success else "Test error",
                            sql_safety=ValidationStatus.PASSED if success else ValidationStatus.FAILED,
                            retried=False
                        ),
                        database=DatabaseInfo(
                            tables_used=[f"test{i}"],
                            query_type=QueryType.SELECT,
                            complexity=ComplexityLevel.SIMPLE
                        ),
                        performance=PerformanceInfo(
                            rows_returned=i,
                            columns_returned=1,
                            data_size_estimate="10 characters",
                            execution_ms=50 + i * 10
                        ),
                        security=SecurityInfo(
                            tables_accessed=[f"test{i}"],
                            security_checks_passed=True,
                            blocked_operations=[]
                        )
                    ),
                    success=success,
                    trace_id=f"test-trace-{i}",
                    error=None if success else f"Test error {i}"
                )
                
                request = QueryRequest(question=f"Test question {i}")
                manager.save_query(query_response, request)
            
            # Get stats
            stats = manager.get_query_stats(days=30)
            
            assert stats["total_queries"] == 10
            assert stats["successful_queries"] == 8
            assert stats["success_rate"] == 80.0
            assert stats["avg_execution_time_ms"] > 0
            assert stats["total_tokens_used"] >= 0
            assert "llm_mode_stats" in stats
            assert "daily_stats" in stats
            
            print("✅ Query statistics work")
            
    except Exception as e:
        print(f"❌ Query statistics failed: {e}")
        return False
    
    return True


def test_delete_query():
    """Test deleting queries"""
    print("Testing delete query...")
    
    try:
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = os.path.join(temp_dir, "test_history.db")
            manager = QueryHistoryManager(db_path)
            
            # Save a test query
            query_response = QueryResponse(
                sql="SELECT * FROM test",
                answer="Test answer",
                meta=QueryMetadata(
                    results={"row_count": 1, "columns": ["id"]},
                    validation=ValidationInfo(
                        is_valid=True,
                        error=None,
                        sql_safety=ValidationStatus.PASSED,
                        retried=False
                    ),
                    database=DatabaseInfo(
                        tables_used=["test"],
                        query_type=QueryType.SELECT,
                        complexity=ComplexityLevel.SIMPLE
                    ),
                    performance=PerformanceInfo(
                        rows_returned=1,
                        columns_returned=1,
                        data_size_estimate="10 characters",
                        execution_ms=50
                    ),
                    security=SecurityInfo(
                        tables_accessed=["test"],
                        security_checks_passed=True,
                        blocked_operations=[]
                    )
                ),
                success=True,
                trace_id="test-trace-123"
            )
            
            request = QueryRequest(question="Test question")
            entry_id = manager.save_query(query_response, request)
            
            # Verify query exists
            entry = manager.get_query_by_id(entry_id)
            assert entry is not None
            
            # Delete query
            deleted = manager.delete_query(entry_id)
            assert deleted == True
            
            # Verify query is deleted
            entry = manager.get_query_by_id(entry_id)
            assert entry is None
            
            # Test deleting non-existent query
            deleted = manager.delete_query(99999)
            assert deleted == False
            
            print("✅ Delete query works")
            
    except Exception as e:
        print(f"❌ Delete query failed: {e}")
        return False
    
    return True


def test_export_history():
    """Test exporting query history"""
    print("Testing export history...")
    
    try:
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = os.path.join(temp_dir, "test_history.db")
            manager = QueryHistoryManager(db_path)
            
            # Save test queries
            for i in range(3):
                query_response = QueryResponse(
                    sql=f"SELECT * FROM test{i}",
                    answer=f"Test answer {i}",
                    meta=QueryMetadata(
                        results={"row_count": i, "columns": ["id"]},
                        validation=ValidationInfo(
                            is_valid=True,
                            error=None,
                            sql_safety=ValidationStatus.PASSED,
                            retried=False
                        ),
                        database=DatabaseInfo(
                            tables_used=[f"test{i}"],
                            query_type=QueryType.SELECT,
                            complexity=ComplexityLevel.SIMPLE
                        ),
                        performance=PerformanceInfo(
                            rows_returned=i,
                            columns_returned=1,
                            data_size_estimate="10 characters",
                            execution_ms=50
                        ),
                        security=SecurityInfo(
                            tables_accessed=[f"test{i}"],
                            security_checks_passed=True,
                            blocked_operations=[]
                        )
                    ),
                    success=True,
                    trace_id=f"test-trace-{i}"
                )
                
                request = QueryRequest(question=f"Test question {i}")
                manager.save_query(query_response, request)
            
            # Export as JSON
            json_export = manager.export_history(format="json")
            assert json_export is not None
            assert "Test question" in json_export
            
            # Export as CSV
            csv_export = manager.export_history(format="csv")
            assert csv_export is not None
            assert "Test question" in csv_export
            
            print("✅ Export history works")
            
    except Exception as e:
        print(f"❌ Export history failed: {e}")
        return False
    
    return True


def main():
    """Run all query history tests"""
    print("🧪 Testing Query History")
    print("=" * 50)
    
    tests = [
        test_history_manager_creation,
        test_save_query,
        test_get_query_history,
        test_get_query_by_id,
        test_query_stats,
        test_delete_query,
        test_export_history
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
        print("🎉 All query history tests passed!")
        return True
    else:
        print("❌ Some tests failed")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
