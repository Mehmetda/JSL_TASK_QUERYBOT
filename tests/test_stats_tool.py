"""
Test statistics tool functionality

Run:
  python tests/test_stats_tool.py
"""
import sys
import sqlite3
import tempfile
from pathlib import Path

# Add project root to Python path
CURRENT = Path(__file__).resolve().parent
PROJECT_ROOT = CURRENT.parent
sys.path.insert(0, str(PROJECT_ROOT))

from app.tools.stats_tool import StatsTool


def create_test_database():
    """Create a test database with sample data"""
    # Create in-memory database
    conn = sqlite3.connect(":memory:")
    cursor = conn.cursor()
    
    # Create test tables
    cursor.execute("""
        CREATE TABLE test_patients (
            id INTEGER PRIMARY KEY,
            age INTEGER,
            height REAL,
            weight REAL,
            name TEXT,
            is_active BOOLEAN
        )
    """)
    
    cursor.execute("""
        CREATE TABLE test_admissions (
            id INTEGER PRIMARY KEY,
            patient_id INTEGER,
            admission_time TEXT,
            discharge_time TEXT,
            length_of_stay INTEGER,
            cost REAL
        )
    """)
    
    # Insert test data
    patients_data = [
        (1, 25, 170.5, 65.2, "Alice", 1),
        (2, 30, 175.0, 70.1, "Bob", 1),
        (3, 45, 165.2, 80.5, "Charlie", 0),
        (4, 22, 180.0, 75.0, "David", 1),
        (5, 35, 168.5, 68.3, "Eve", 1),
        (6, 28, 172.0, 72.1, "Frank", 1),
        (7, 50, 160.0, 85.2, "Grace", 0),
        (8, 33, 178.5, 77.8, "Henry", 1)
    ]
    
    cursor.executemany(
        "INSERT INTO test_patients (id, age, height, weight, name, is_active) VALUES (?, ?, ?, ?, ?, ?)",
        patients_data
    )
    
    admissions_data = [
        (1, 1, "2024-01-01", "2024-01-03", 2, 1500.50),
        (2, 2, "2024-01-02", "2024-01-05", 3, 2200.75),
        (3, 3, "2024-01-03", "2024-01-07", 4, 3200.00),
        (4, 4, "2024-01-04", "2024-01-06", 2, 1800.25),
        (5, 5, "2024-01-05", "2024-01-08", 3, 2500.50),
        (6, 6, "2024-01-06", "2024-01-09", 3, 2100.75),
        (7, 7, "2024-01-07", "2024-01-12", 5, 4500.00),
        (8, 8, "2024-01-08", "2024-01-10", 2, 1900.25)
    ]
    
    cursor.executemany(
        "INSERT INTO test_admissions (id, patient_id, admission_time, discharge_time, length_of_stay, cost) VALUES (?, ?, ?, ?, ?, ?)",
        admissions_data
    )
    
    conn.commit()
    return conn


def test_column_stats():
    """Test basic column statistics"""
    print("Testing column statistics...")
    
    try:
        conn = create_test_database()
        stats_tool = StatsTool(conn)
        
        # Test age column stats
        age_stats = stats_tool.get_column_stats("test_patients", "age")
        
        assert age_stats["is_numeric"] == True
        assert age_stats["count"] == 8
        assert age_stats["min"] == 22
        assert age_stats["max"] == 50
        assert age_stats["avg"] == 33.5
        assert age_stats["sum"] == 268
        print("✅ Age column statistics work")
        
        # Test height column stats
        height_stats = stats_tool.get_column_stats("test_patients", "height")
        
        assert height_stats["is_numeric"] == True
        assert height_stats["count"] == 8
        assert height_stats["min"] == 160.0
        assert height_stats["max"] == 180.0
        assert height_stats["avg"] == 171.2125
        print("✅ Height column statistics work")
        
        # Test non-numeric column
        name_stats = stats_tool.get_column_stats("test_patients", "name")
        assert name_stats["is_numeric"] == False
        assert "error" in name_stats
        print("✅ Non-numeric column detection works")
        
        # Test quartiles
        assert "quartiles" in age_stats
        quartiles = age_stats["quartiles"]
        assert quartiles["q1"] is not None
        assert quartiles["q2"] is not None  # Median
        assert quartiles["q3"] is not None
        print("✅ Quartiles calculation works")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Column stats test failed: {e}")
        return False


def test_filtered_stats():
    """Test statistics with WHERE clause"""
    print("\nTesting filtered statistics...")
    
    try:
        conn = create_test_database()
        stats_tool = StatsTool(conn)
        
        # Test age stats for active patients only
        active_age_stats = stats_tool.get_column_stats(
            "test_patients", 
            "age", 
            where_clause="is_active = 1"
        )
        
        assert active_age_stats["is_numeric"] == True
        assert active_age_stats["count"] == 6  # Only active patients
        assert active_age_stats["min"] == 22
        assert active_age_stats["max"] == 35
        print("✅ Filtered statistics work")
        
        # Test cost stats for admissions with length > 3 days
        long_stay_stats = stats_tool.get_column_stats(
            "test_admissions",
            "cost",
            where_clause="length_of_stay > 3"
        )
        
        assert long_stay_stats["is_numeric"] == True
        assert long_stay_stats["count"] == 2  # Only long stays
        print("✅ Complex filtered statistics work")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Filtered stats test failed: {e}")
        return False


def test_numeric_columns_detection():
    """Test numeric columns detection"""
    print("\nTesting numeric columns detection...")
    
    try:
        conn = create_test_database()
        stats_tool = StatsTool(conn)
        
        # Test patients table
        numeric_cols = stats_tool.get_table_numeric_columns("test_patients")
        expected_cols = ["id", "age", "height", "weight", "is_active"]
        
        for col in expected_cols:
            assert col in numeric_cols, f"Column {col} should be detected as numeric"
        assert "name" not in numeric_cols, "Name column should not be detected as numeric"
        print("✅ Numeric columns detection works")
        
        # Test admissions table
        admission_cols = stats_tool.get_table_numeric_columns("test_admissions")
        expected_admission_cols = ["id", "patient_id", "length_of_stay", "cost"]
        
        for col in expected_admission_cols:
            assert col in admission_cols, f"Column {col} should be detected as numeric"
        print("✅ Multiple table numeric detection works")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Numeric columns detection test failed: {e}")
        return False


def test_table_analysis():
    """Test full table analysis"""
    print("\nTesting table analysis...")
    
    try:
        conn = create_test_database()
        stats_tool = StatsTool(conn)
        
        # Analyze patients table
        analysis = stats_tool.analyze_table_numeric_data("test_patients")
        
        assert analysis["table"] == "test_patients"
        assert "numeric_columns" in analysis
        assert "column_stats" in analysis
        assert len(analysis["numeric_columns"]) > 0
        print("✅ Table analysis works")
        
        # Check that all numeric columns have stats
        for col in analysis["numeric_columns"]:
            assert col in analysis["column_stats"]
            col_stats = analysis["column_stats"][col]
            assert col_stats["is_numeric"] == True
        print("✅ All numeric columns have stats")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Table analysis test failed: {e}")
        return False


def test_stats_formatting():
    """Test statistics formatting"""
    print("\nTesting statistics formatting...")
    
    try:
        conn = create_test_database()
        stats_tool = StatsTool(conn)
        
        # Get stats for age column
        age_stats = stats_tool.get_column_stats("test_patients", "age")
        
        # Format stats
        formatted = stats_tool.format_stats_summary(age_stats)
        
        assert "Count:" in formatted
        assert "Min:" in formatted
        assert "Max:" in formatted
        assert "Average:" in formatted
        assert "Range:" in formatted
        assert "Median:" in formatted
        print("✅ Statistics formatting works")
        
        # Test error formatting
        error_stats = {"error": "Test error", "is_numeric": False}
        error_formatted = stats_tool.format_stats_summary(error_stats)
        assert "Error:" in error_formatted
        print("✅ Error formatting works")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Stats formatting test failed: {e}")
        return False


def test_edge_cases():
    """Test edge cases"""
    print("\nTesting edge cases...")
    
    try:
        conn = create_test_database()
        stats_tool = StatsTool(conn)
        
        # Test empty table
        cursor = conn.cursor()
        cursor.execute("CREATE TABLE empty_table (id INTEGER, value REAL)")
        
        empty_stats = stats_tool.get_column_stats("empty_table", "value")
        assert empty_stats["count"] == 0
        print("✅ Empty table handling works")
        
        # Test non-existent table
        try:
            stats_tool.get_column_stats("non_existent", "value")
            assert False, "Should have raised an exception"
        except:
            print("✅ Non-existent table error handling works")
        
        # Test non-existent column
        try:
            stats_tool.get_column_stats("test_patients", "non_existent")
            assert False, "Should have raised an exception"
        except:
            print("✅ Non-existent column error handling works")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Edge cases test failed: {e}")
        return False


def main():
    """Run all stats tool tests"""
    print("🚀 Starting Stats Tool Tests")
    print("=" * 50)
    
    tests = [
        test_column_stats,
        test_filtered_stats,
        test_numeric_columns_detection,
        test_table_analysis,
        test_stats_formatting,
        test_edge_cases
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
        print("🎉 All stats tool tests passed!")
    else:
        print("⚠️  Some tests failed. Check the error messages above.")
    
    return passed == total


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
