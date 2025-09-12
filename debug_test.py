"""
Debug test for LLM issues
"""
import sys
from pathlib import Path

# Add project root to Python path
CURRENT = Path(__file__).resolve().parent
PROJECT_ROOT = CURRENT
sys.path.insert(0, str(PROJECT_ROOT))

from app.main import run_query_pipeline

def test_simple_query():
    """Test a simple query"""
    print("Testing simple query...")
    
    try:
        result = run_query_pipeline("Kaç tane hasta var?")
        
        print("SQL:", result.get("sql", ""))
        print("Answer:", result.get("answer", ""))
        print("Answer length:", len(result.get("answer", "")))
        
        # Check if answer is empty
        if not result.get("answer", "").strip():
            print("❌ Answer is empty!")
        else:
            print("✅ Answer generated successfully")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_simple_query()
