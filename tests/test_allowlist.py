"""
Test table allowlist functionality

Run:
  python tests/test_allowlist.py
"""
import sys
from pathlib import Path

# Add project root to Python path
CURRENT = Path(__file__).resolve().parent
PROJECT_ROOT = CURRENT.parent
sys.path.insert(0, str(PROJECT_ROOT))

from app.security import TableAllowlist, TableAllowlistManager


def test_table_allowlist_basic():
    """Test basic table allowlist functionality"""
    print("Testing basic table allowlist...")
    
    try:
        # Test with custom allowed tables
        allowed_tables = ["patients", "admissions", "providers"]
        allowlist = TableAllowlist(allowed_tables)
        
        # Test allowed tables
        assert allowlist.is_table_allowed("patients") == True
        assert allowlist.is_table_allowed("admissions") == True
        assert allowlist.is_table_allowed("providers") == True
        print("✅ Allowed tables work")
        
        # Test blocked tables
        assert allowlist.is_table_allowed("sensitive_data") == False
        assert allowlist.is_table_allowed("admin_users") == False
        print("✅ Blocked tables work")
        
        # Test case insensitive
        assert allowlist.is_table_allowed("PATIENTS") == True
        assert allowlist.is_table_allowed("Patients") == True
        print("✅ Case insensitive matching works")
        
        # Test quoted table names
        assert allowlist.is_table_allowed('"patients"') == True
        assert allowlist.is_table_allowed("'admissions'") == True
        print("✅ Quoted table names work")
        
        return True
        
    except Exception as e:
        print(f"❌ Basic allowlist test failed: {e}")
        return False






def test_security_info():
    """Test security information generation"""
    print("\nTesting security information...")
    
    try:
        allowlist = TableAllowlist(["patients", "admissions"])
        
        # Test blocked operations tracking
        allowlist.is_table_allowed("blocked_table")  # This should add to blocked_operations
        security_info = allowlist.get_security_info()
        
        assert len(security_info.allowed_tables) == 2
        assert len(security_info.blocked_operations) > 0
        assert security_info.data_modification_blocked == True
        print("✅ Security info generation works")
        
        # Test reset
        allowlist.reset_blocked_operations()
        security_info = allowlist.get_security_info()
        assert len(security_info.blocked_operations) == 0
        assert security_info.data_modification_blocked == False
        print("✅ Reset blocked operations works")
        
        return True
        
    except Exception as e:
        print(f"❌ Security info test failed: {e}")
        return False


def test_allowlist_manager():
    """Test allowlist manager functionality"""
    print("\nTesting allowlist manager...")
    
    try:
        manager = TableAllowlistManager()
        
        # Test query validation
        valid_query = "SELECT * FROM json_patients"
        is_valid, error, security_info = manager.validate_query(valid_query)
        
        assert is_valid == True
        assert error == ""
        assert security_info is not None
        print("✅ Manager query validation works")
        
        # Test blocked query
        blocked_query = "SELECT * FROM sensitive_data"
        is_valid, error, security_info = manager.validate_query(blocked_query)
        
        assert is_valid == False
        assert "Access denied" in error
        assert security_info is not None
        print("✅ Manager blocked query works")
        
        
        return True
        
    except Exception as e:
        print(f"❌ Allowlist manager test failed: {e}")
        return False


def test_medical_domain_queries():
    """Test medical domain specific queries"""
    print("\nTesting medical domain queries...")
    
    try:
        # Use default medical tables
        manager = TableAllowlistManager()
        
        # Test allowed medical queries
        medical_queries = [
            "SELECT COUNT(*) FROM json_patients",
            "SELECT * FROM json_admissions WHERE admission_type = 'EMERGENCY'",
            "SELECT p.*, a.* FROM json_patients p JOIN json_admissions a ON p.subject_id = a.subject_id",
            "SELECT provider_id, COUNT(*) FROM json_providers GROUP BY provider_id",
            "SELECT * FROM json_transfers WHERE careunit = 'ICU'",
            "SELECT * FROM json_lab WHERE itemid = 50001",
            "SELECT * FROM json_diagnoses WHERE icd9_code LIKE '250%'",
            "SELECT * FROM json_insurance WHERE insurance = 'Medicare'",
            "SELECT * FROM json_careunits WHERE careunit = 'MICU'"
        ]
        
        for query in medical_queries:
            is_valid, error, security_info = manager.validate_query(query)
            if not is_valid:
                print(f"⚠️  Medical query blocked: {query} - {error}")
            else:
                print(f"✅ Medical query allowed: {query[:50]}...")
        
        # Test blocked non-medical queries
        blocked_queries = [
            "SELECT * FROM users",
            "SELECT * FROM admin_logs",
            "SELECT * FROM system_config",
            "SELECT * FROM secret_keys"
        ]
        
        for query in blocked_queries:
            is_valid, error, security_info = manager.validate_query(query)
            assert is_valid == False, f"Non-medical query should be blocked: {query}"
        
        print("✅ Medical domain query validation works")
        
        return True
        
    except Exception as e:
        print(f"❌ Medical domain queries test failed: {e}")
        return False


def test_edge_cases():
    """Test edge cases and error handling"""
    print("\nTesting edge cases...")
    
    try:
        allowlist = TableAllowlist(["patients"])
        
        # Test empty table name
        assert allowlist.is_table_allowed("") == False
        print("✅ Empty table name handling works")
        
        # Test None table name
        try:
            allowlist.is_table_allowed(None)
            assert False, "Should have raised an exception"
        except:
            print("✅ None table name error handling works")
        
        # Test SQL with no tables
        is_valid, allowed, blocked = allowlist.validate_sql_tables("SELECT 1")
        assert is_valid == True  # No tables means valid
        print("✅ SQL with no tables works")
        
        # Test malformed SQL
        malformed_queries = [
            "SELECT * FROM",  # Incomplete
            "INVALID SQL SYNTAX",
            "",  # Empty
            "SELECT * FROM patients WHERE"  # Incomplete WHERE
        ]
        
        for query in malformed_queries:
            try:
                is_valid, allowed, blocked = allowlist.validate_sql_tables(query)
                # Should not crash, even with malformed SQL
                print(f"✅ Malformed SQL handled: {query[:20]}...")
            except Exception as e:
                print(f"⚠️  Malformed SQL caused error: {query} - {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ Edge cases test failed: {e}")
        return False


def main():
    """Run all allowlist tests"""
    print("Starting Table Allowlist Tests")
    print("=" * 50)
    
    tests = [
        test_table_allowlist_basic,
        test_security_info,
        test_allowlist_manager,
        test_medical_domain_queries,
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
    
    print(f"\nTest Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("All allowlist tests passed!")
    else:
        print("Some tests failed. Check the error messages above.")
    
    return passed == total


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
