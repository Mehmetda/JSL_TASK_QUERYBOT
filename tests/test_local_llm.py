"""
Test script for local LLM integration
"""
import sys
import os
from pathlib import Path

# Add project root to Python path
CURRENT = Path(__file__).resolve().parent
PROJECT_ROOT = CURRENT.parent
sys.path.insert(0, str(PROJECT_ROOT))

from app.llm import get_local_llm_client, initialize_llm
from app.llm.llm_manager import get_llm_manager
from app.utils import check_internet_connection, check_openai_availability
from config import get_model_name, get_embedding_model

def test_llm_initialization():
    """Test LLM initialization"""
    print("Testing LLM initialization...")
    try:
        client = initialize_llm()
        print(f"LLM initialized successfully with model: {get_model_name()}")
        return True
    except Exception as e:
        print(f"LLM initialization failed: {e}")
        return False

def test_llm_generation():
    """Test LLM text generation"""
    print("\nTesting LLM text generation...")
    try:
        client = get_local_llm_client()
        
        # Test simple generation
        messages = [
            {"role": "system", "content": "Sen yardımcı bir asistansın."},
            {"role": "user", "content": "Merhaba, nasılsın?"}
        ]
        
        response = client.generate_response(messages, max_tokens=50, temperature=0.1)
        print(f"LLM generation successful")
        print(f"Response: {response['content'][:100]}...")
        print(f"Token usage: {response['usage']}")
        return True
        
    except Exception as e:
        print(f"LLM generation failed: {e}")
        return False

def test_embedding():
    """Test embedding generation"""
    print("\nTesting embedding generation...")
    try:
        from sentence_transformers import SentenceTransformer
        
        model_name = get_embedding_model()
        model = SentenceTransformer(model_name)
        
        texts = ["Bu bir test metnidir", "Another test text"]
        embeddings = model.encode(texts)
        
        print(f"Embedding generation successful")
        print(f"Model: {model_name}")
        print(f"Embedding shape: {embeddings.shape}")
        return True
        
    except Exception as e:
        print(f"Embedding generation failed: {e}")
        return False

def test_llm_manager():
    """Test LLM manager functionality"""
    print("\nTesting LLM manager...")
    try:
        manager = get_llm_manager()
        
        # Test available modes
        modes = manager.get_available_modes()
        print(f"Available modes: {modes}")
        
        # Test status
        status = manager.get_status()
        print(f"Manager status: {status}")
        
        # Test mode switching
        manager.set_mode("local")
        print(f"Mode set to: {manager.get_current_mode()}")
        
        return True
        
    except Exception as e:
        print(f"LLM manager test failed: {e}")
        return False

def test_connectivity():
    """Test internet and OpenAI connectivity"""
    print("\nTesting connectivity...")
    try:
        internet = check_internet_connection()
        openai = check_openai_availability()
        
        print(f"Internet available: {internet}")
        print(f"OpenAI available: {openai}")
        
        return True
        
    except Exception as e:
        print(f"Connectivity test failed: {e}")
        return False

def test_sql_agent():
    """Test SQL agent with local LLM"""
    print("\nTesting SQL agent...")
    try:
        from app.agents.sql_agent import generate_sql
        from app.db.connection import get_connection
        
        conn = get_connection()
        question = "Kaç tane hasta var?"
        
        sql = generate_sql(question, conn)
        print(f"SQL generation successful")
        print(f"Question: {question}")
        print(f"Generated SQL: {sql}")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"SQL agent test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("Starting Local LLM Integration Tests")
    print("=" * 50)
    
    tests = [
        test_llm_initialization,
        test_llm_generation,
        test_embedding,
        test_llm_manager,
        test_connectivity,
        test_sql_agent
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
        print("-" * 30)
    
    print(f"\nTest Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("All tests passed! Local LLM integration is working correctly.")
    else:
        print("Some tests failed. Check the error messages above.")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
