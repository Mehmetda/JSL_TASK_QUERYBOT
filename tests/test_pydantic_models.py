"""
Test Pydantic models

Run:
  python tests/test_pydantic_models.py
"""
import sys
from pathlib import Path

# Add project root to Python path
CURRENT = Path(__file__).resolve().parent
PROJECT_ROOT = CURRENT.parent
sys.path.insert(0, str(PROJECT_ROOT))

from app.models.query_models import (
    QueryRequest, QueryResponse, QueryMetadata, 
    DatabaseInfo, ValidationInfo, PerformanceInfo,
    LLMInfo, SecurityInfo, QueryType, ComplexityLevel,
    ValidationStatus, LLMMode
)
from app.models.llm_models import LLMRequest, LLMResponse, LLMUsage, Message, MessageRole
from app.models.database_models import TableInfo, ColumnInfo, SchemaInfo, ColumnType


def test_query_models():
    """Test query-related models"""
    print("Testing query models...")
    
    try:
        # Test QueryRequest
        request = QueryRequest(
            question="Kaç tane hasta var?",
            user_id="user123",
            session_id="session456",
            trace_id="trace789",
            llm_mode=LLMMode.AUTO
        )
        assert request.question == "Kaç tane hasta var?"
        assert request.user_id == "user123"
        print("✅ QueryRequest model works")
        
        # Test ValidationInfo
        validation = ValidationInfo(
            is_valid=True,
            error=None,
            sql_safety=ValidationStatus.PASSED,
            retried=False
        )
        assert validation.is_valid == True
        print("✅ ValidationInfo model works")
        
        # Test DatabaseInfo
        db_info = DatabaseInfo(
            tables_used=["json_patients"],
            query_type=QueryType.COUNT_QUERY,
            complexity=ComplexityLevel.SIMPLE,
            relevant_schema="Table: json_patients"
        )
        assert db_info.query_type == QueryType.COUNT_QUERY
        print("✅ DatabaseInfo model works")
        
        # Test PerformanceInfo
        perf_info = PerformanceInfo(
            rows_returned=1,
            columns_returned=1,
            data_size_estimate="6 characters",
            execution_ms=10,
            tokens={"sql_generation": 50, "answer_summarization": 100}
        )
        assert perf_info.total_tokens == 150
        print("✅ PerformanceInfo model works")
        
        # Test QueryMetadata
        metadata = QueryMetadata(
            results={"row_count": 1},
            validation=validation,
            database=db_info,
            performance=perf_info,
            llm=LLMInfo(
                selected_mode=LLMMode.LOCAL,
                effective_mode=LLMMode.LOCAL,
                model_used="local-llm",
                total_tokens=150
            )
        )
        assert metadata.validation.is_valid == True
        print("✅ QueryMetadata model works")
        
        # Test QueryResponse
        response = QueryResponse(
            sql="SELECT COUNT(*) FROM json_patients",
            answer="1 hasta bulunmaktadır.",
            meta=metadata
        )
        assert response.success == True
        print("✅ QueryResponse model works")
        
        return True
        
    except Exception as e:
        print(f"❌ Query models test failed: {e}")
        return False


def test_llm_models():
    """Test LLM-related models"""
    print("\nTesting LLM models...")
    
    try:
        # Test Message
        message = Message(
            role=MessageRole.USER,
            content="Merhaba, nasılsın?"
        )
        assert message.role == MessageRole.USER
        print("✅ Message model works")
        
        # Test LLMUsage
        usage = LLMUsage(
            prompt_tokens=100,
            completion_tokens=50,
            total_tokens=150
        )
        assert usage.total_tokens == 150
        print("✅ LLMUsage model works")
        
        # Test LLMRequest
        request = LLMRequest(
            messages=[message],
            model="local-llm",
            max_tokens=300,
            temperature=0.1
        )
        assert len(request.messages) == 1
        print("✅ LLMRequest model works")
        
        # Test LLMResponse
        response = LLMResponse(
            content="Merhaba! Ben iyiyim, teşekkürler.",
            usage=usage,
            model_used="local-llm"
        )
        assert response.content.startswith("Merhaba")
        print("✅ LLMResponse model works")
        
        return True
        
    except Exception as e:
        print(f"❌ LLM models test failed: {e}")
        return False


def test_database_models():
    """Test database-related models"""
    print("\nTesting database models...")
    
    try:
        # Test ColumnInfo
        column = ColumnInfo(
            name="patient_id",
            type=ColumnType.INTEGER,
            is_primary_key=True,
            is_nullable=False
        )
        assert column.is_primary_key == True
        print("✅ ColumnInfo model works")
        
        # Test TableInfo
        table = TableInfo(
            name="json_patients",
            columns=[column],
            row_count=100,
            description="Patient information table"
        )
        assert table.row_count == 100
        print("✅ TableInfo model works")
        
        # Test SchemaInfo
        schema = SchemaInfo(
            tables=[table],
            total_tables=1,
            total_columns=1
        )
        assert schema.total_tables == 1
        print("✅ SchemaInfo model works")
        
        return True
        
    except Exception as e:
        print(f"❌ Database models test failed: {e}")
        return False


def test_model_serialization():
    """Test model serialization to JSON"""
    print("\nTesting model serialization...")
    
    try:
        # Test QueryRequest serialization
        request = QueryRequest(question="Test question")
        json_data = request.model_dump()
        assert "question" in json_data
        print("✅ QueryRequest serialization works")
        
        # Test QueryResponse serialization
        validation = ValidationInfo(is_valid=True, sql_safety=ValidationStatus.PASSED)
        db_info = DatabaseInfo(query_type=QueryType.SELECT_QUERY, complexity=ComplexityLevel.SIMPLE)
        perf_info = PerformanceInfo(rows_returned=1, columns_returned=1, data_size_estimate="test", execution_ms=10)
        metadata = QueryMetadata(validation=validation, database=db_info, performance=perf_info)
        
        response = QueryResponse(
            sql="SELECT * FROM test",
            answer="Test answer",
            meta=metadata
        )
        
        json_data = response.model_dump()
        assert "sql" in json_data
        assert "answer" in json_data
        assert "meta" in json_data
        print("✅ QueryResponse serialization works")
        
        return True
        
    except Exception as e:
        print(f"❌ Model serialization test failed: {e}")
        return False


def main():
    """Run all Pydantic model tests"""
    print("🚀 Starting Pydantic Models Tests")
    print("=" * 50)
    
    tests = [
        test_query_models,
        test_llm_models,
        test_database_models,
        test_model_serialization
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
        except Exception as e:
            print(f"❌ Test failed: {e}")
        print("-" * 30)
    
    print(f"\n📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All Pydantic model tests passed!")
    else:
        print("⚠️  Some tests failed. Check the error messages above.")
    
    return passed == total


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
