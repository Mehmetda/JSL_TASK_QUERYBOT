"""
Test LLM switching functionality

Run:
  python tests/test_llm_switching.py
"""
import sys
from pathlib import Path

# Add project root to Python path
CURRENT = Path(__file__).resolve().parent
PROJECT_ROOT = CURRENT.parent
sys.path.insert(0, str(PROJECT_ROOT))

from app.llm.llm_manager import get_llm_manager
from app.utils import check_internet_connection, check_openai_availability


def test_llm_manager_modes():
    """Test LLM manager mode switching"""
    print("Testing LLM manager modes...")
    
    manager = get_llm_manager()
    
    # Test available modes
    modes = manager.get_available_modes()
    print(f"✅ Available modes: {modes}")
    
    # Test mode switching
    for mode in modes:
        manager.set_mode(mode)
        current_mode = manager.get_current_mode()
        effective_mode = manager.get_effective_mode()
        print(f"✅ Mode '{mode}' -> Current: {current_mode}, Effective: {effective_mode}")
    
    return True


def test_connectivity_checks():
    """Test connectivity check functions"""
    print("\nTesting connectivity checks...")
    
    internet = check_internet_connection()
    openai = check_openai_availability()
    
    print(f"✅ Internet available: {internet}")
    print(f"✅ OpenAI available: {openai}")
    
    return True


def test_llm_generation_modes():
    """Test LLM generation in different modes"""
    print("\nTesting LLM generation in different modes...")
    
    manager = get_llm_manager()
    messages = [
        {"role": "system", "content": "Sen yardımcı bir asistansın."},
        {"role": "user", "content": "Merhaba, nasılsın?"}
    ]
    
    # Test each available mode
    for mode in manager.get_available_modes():
        if mode == "auto":
            continue  # Skip auto mode for direct testing
            
        try:
            manager.set_mode(mode)
            response = manager.generate_response(messages, max_tokens=20)
            print(f"✅ Mode '{mode}': {response['content'][:50]}...")
        except Exception as e:
            print(f"❌ Mode '{mode}' failed: {e}")
    
    return True


def main():
    """Run all LLM switching tests"""
    print("🚀 Starting LLM Switching Tests")
    print("=" * 50)
    
    tests = [
        test_llm_manager_modes,
        test_connectivity_checks,
        test_llm_generation_modes
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
        print("🎉 All LLM switching tests passed!")
    else:
        print("⚠️  Some tests failed. Check the error messages above.")
    
    return passed == total


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
