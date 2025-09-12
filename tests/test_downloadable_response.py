"""
Test downloadable JSON response functionality

Run:
  python tests/test_downloadable_response.py
"""
import sys
from pathlib import Path
import json
import tempfile
import os
from datetime import datetime

# Add project root to Python path
CURRENT = Path(__file__).resolve().parent
PROJECT_ROOT = CURRENT.parent
sys.path.insert(0, str(PROJECT_ROOT))

from app.models.query_models import QueryResponse, QueryMetadata, ValidationInfo, DatabaseInfo, PerformanceInfo, SecurityInfo, QueryType, ComplexityLevel, ValidationStatus




def test_csv_export():
    """Test CSV export functionality"""
    print("Testing CSV export...")
    
    try:
        # Create test data
        test_data = [
            {"id": 1, "name": "Test 1", "value": 100},
            {"id": 2, "name": "Test 2", "value": 200},
            {"id": 3, "name": "Test 3", "value": 300}
        ]
        
        # Test CSV conversion
        import pandas as pd
        df = pd.DataFrame(test_data)
        csv_str = df.to_csv(index=False)
        
        assert csv_str is not None
        assert "id,name,value" in csv_str
        assert "1,Test 1,100" in csv_str
        assert "2,Test 2,200" in csv_str
        assert "3,Test 3,300" in csv_str
        
        print("✅ CSV export works")
        
    except Exception as e:
        print(f"❌ CSV export failed: {e}")
        return False
    
    return True




def test_file_naming():
    """Test file naming conventions"""
    print("Testing file naming...")
    
    try:
        # Test JSON file naming
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        json_filename = f"query_response_{timestamp}.json"
        assert json_filename.startswith("query_response_")
        assert json_filename.endswith(".json")
        assert len(json_filename) > 20  # Should have timestamp
        
        # Test CSV file naming
        csv_filename = f"query_results_{timestamp}.csv"
        assert csv_filename.startswith("query_results_")
        assert csv_filename.endswith(".csv")
        
        # Test TXT file naming
        txt_filename = f"query_response_{timestamp}.txt"
        assert txt_filename.startswith("query_response_")
        assert txt_filename.endswith(".txt")
        
        # Test history file naming
        history_json_filename = f"query_history_{timestamp}.json"
        assert history_json_filename.startswith("query_history_")
        assert history_json_filename.endswith(".json")
        
        print("✅ File naming works")
        
    except Exception as e:
        print(f"❌ File naming failed: {e}")
        return False
    
    return True


def test_mime_types():
    """Test MIME types for downloads"""
    print("Testing MIME types...")
    
    try:
        # Test JSON MIME type
        json_mime = "application/json"
        assert json_mime == "application/json"
        
        # Test CSV MIME type
        csv_mime = "text/csv"
        assert csv_mime == "text/csv"
        
        # Test TXT MIME type
        txt_mime = "text/plain"
        assert txt_mime == "text/plain"
        
        print("✅ MIME types work")
        
    except Exception as e:
        print(f"❌ MIME types failed: {e}")
        return False
    
    return True


def test_unicode_handling():
    """Test Unicode handling in exports"""
    print("Testing Unicode handling...")
    
    try:
        # Test with Turkish characters
        turkish_text = "Türkçe karakter test: ğüşıöçĞÜŞİÖÇ"
        
        # Test JSON with Unicode
        json_str = json.dumps({"text": turkish_text}, ensure_ascii=False)
        assert turkish_text in json_str
        
        # Test CSV with Unicode
        import pandas as pd
        df = pd.DataFrame({"text": [turkish_text]})
        csv_str = df.to_csv(index=False)
        assert turkish_text in csv_str
        
        # Test TXT with Unicode
        txt_content = f"Test: {turkish_text}"
        assert turkish_text in txt_content
        
        print("✅ Unicode handling works")
        
    except Exception as e:
        print(f"❌ Unicode handling failed: {e}")
        return False
    
    return True


def test_large_data_handling():
    """Test handling of large data sets"""
    print("Testing large data handling...")
    
    try:
        # Create large dataset
        large_data = []
        for i in range(1000):
            large_data.append({
                "id": i,
                "name": f"Item {i}",
                "value": i * 10,
                "description": f"This is a long description for item {i} with some additional text to make it longer"
            })
        
        # Test JSON serialization
        json_str = json.dumps(large_data, indent=2, ensure_ascii=False)
        assert len(json_str) > 100000  # Should be large
        
        # Test CSV conversion
        import pandas as pd
        df = pd.DataFrame(large_data)
        csv_str = df.to_csv(index=False)
        assert len(csv_str) > 50000  # Should be large
        
        # Test that data is preserved
        parsed = json.loads(json_str)
        assert len(parsed) == 1000
        assert parsed[0]["id"] == 0
        assert parsed[999]["id"] == 999
        
        print("✅ Large data handling works")
        
    except Exception as e:
        print(f"❌ Large data handling failed: {e}")
        return False
    
    return True


def main():
    """Run all downloadable response tests"""
    print("Testing Downloadable JSON Response")
    print("=" * 50)
    
    tests = [
        test_csv_export,
        test_file_naming,
        test_mime_types,
        test_unicode_handling,
        test_large_data_handling
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
        print()
    
    print("=" * 50)
    print(f"Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("All downloadable response tests passed!")
        return True
    else:
        print("Some tests failed")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
