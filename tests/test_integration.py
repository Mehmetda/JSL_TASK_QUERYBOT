"""
Integration tests for the complete pipeline

Run:
  python tests/test_integration.py
"""
import sys
from pathlib import Path

# Add project root to Python path
CURRENT = Path(__file__).resolve().parent
PROJECT_ROOT = CURRENT.parent
sys.path.insert(0, str(PROJECT_ROOT))

from app.main import run_query_pipeline
from app.llm.llm_manager import get_llm_manager


def test_complete_pipeline():
    """Test the complete query pipeline"""
    print("Testing complete pipeline...")
    
    test_questions = [
        "Kaç tane hasta var?",
        "Cinsiyete göre hasta dağılımı nedir?",
        "En çok hasta kabul eden doktorlar kimler?",
        "Yatış tiplerine göre dağılım nedir?"
    ]
    
    manager = get_llm_manager()
    
    for question in test_questions:
        print(f"\nQuestion: {question}")
        
        try:
            result = run_query_pipeline(question)
            
            # Check basic structure
            assert "sql" in result
            assert "answer" in result
            assert "meta" in result
            
            # Check SQL is generated
            assert result["sql"].strip() != ""
            
            # Check metadata structure
            meta = result["meta"]
            assert "validation" in meta
            assert "database" in meta
            assert "performance" in meta
            
            print(f"SQL: {result['sql']}")
            print(f"Answer: {result['answer'][:100]}...")
            print(f"Tables used: {meta['database'].get('tables_used', [])}")
            print(f"LLM mode: {manager.get_effective_mode()}")
            
        except Exception as e:
            print(f"Pipeline failed for question '{question}': {e}")
            return False
    
    return True


def test_data_modification_blocking():
    """Test that data modification queries are blocked"""
    print("\nTesting data modification blocking...")
    
    dangerous_questions = [
        "Hasta tablosunu sil",
        "Yeni hasta ekle",
        "Hasta bilgilerini güncelle",
        "Tabloyu temizle"
    ]
    
    for question in dangerous_questions:
        print(f"Testing: {question}")
        
        try:
            result = run_query_pipeline(question)
            
            # Should be blocked
            assert "VERİ DEĞİŞTİRME İŞLEMİ YASAK" in result["sql"]
            assert "Bu işleme izin verilmiyor" in result["answer"]
            assert result["meta"]["validation"]["sql_safety"] == "BLOCKED_DATA_MODIFICATION"
            
            print("Correctly blocked")
            
        except Exception as e:
            print(f"Blocking failed for '{question}': {e}")
            return False
    
    return True


def test_llm_mode_switching():
    """Test LLM mode switching during pipeline execution"""
    print("\nTesting LLM mode switching...")
    
    manager = get_llm_manager()
    original_mode = manager.get_current_mode()
    
    try:
        # Test different modes
        for mode in manager.get_available_modes():
            if mode == "auto":
                continue  # Skip auto mode
                
            manager.set_mode(mode)
            print(f"Testing mode: {mode}")
            
            result = run_query_pipeline("Kaç tane hasta var?")
            
            # Should work regardless of mode
            assert result["sql"].strip() != ""
            assert result["answer"].strip() != ""
            
            print(f"Mode '{mode}' works")
        
        # Restore original mode
        manager.set_mode(original_mode)
        
    except Exception as e:
        print(f"LLM mode switching failed: {e}")
        return False
    
    return True


def main():
    """Run all integration tests"""
    print("Starting Integration Tests")
    print("=" * 50)
    
    tests = [
        test_complete_pipeline,
        test_data_modification_blocking,
        test_llm_mode_switching
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
    
    print(f"\nTest Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("All integration tests passed!")
    else:
        print("Some tests failed. Check the error messages above.")
    
    return passed == total


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
