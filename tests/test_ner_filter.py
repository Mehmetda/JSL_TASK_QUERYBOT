"""
Test NER filter functionality

Run:
  python tests/test_ner_filter.py
"""
import sys
from pathlib import Path

# Add project root to Python path
CURRENT = Path(__file__).resolve().parent
PROJECT_ROOT = CURRENT.parent
sys.path.insert(0, str(PROJECT_ROOT))

from app.tools.ner_filter import SpaCyNERProvider, build_system_context_block


def test_ner_provider_initialization():
    """Test NER provider initialization"""
    print("Testing NER provider initialization...")
    
    try:
        # Test Turkish provider
        ner_tr = SpaCyNERProvider(language_code="tr")
        print("✅ Turkish NER provider initialized")
        
        # Test English provider
        ner_en = SpaCyNERProvider(language_code="en")
        print("✅ English NER provider initialized")
        
        return True
    except Exception as e:
        print(f"❌ NER provider initialization failed: {e}")
        return False


def test_entity_extraction():
    """Test entity extraction"""
    print("\nTesting entity extraction...")
    
    try:
        ner = SpaCyNERProvider(language_code="tr")
        
        test_texts = [
            "Ahmet Yılmaz 25 yaşında bir hasta",
            "Dr. Mehmet Öz tarafından tedavi edildi",
            "İstanbul Üniversitesi Hastanesi'nde yatış"
        ]
        
        for text in test_texts:
            entities = ner.extract_entities(text)
            print(f"Text: {text}")
            print(f"Entities: {entities}")
            print("-" * 40)
        
        return True
    except Exception as e:
        print(f"❌ Entity extraction failed: {e}")
        return False


def test_filter_and_deidentify():
    """Test filtering and de-identification"""
    print("\nTesting filter and de-identification...")
    
    try:
        ner = SpaCyNERProvider(language_code="tr")
        
        test_text = "Ahmet Yılmaz (ahmet@email.com) 25 yaşında hasta. Dr. Mehmet Öz tarafından tedavi edildi."
        
        result = ner.filter_and_deidentify(test_text)
        
        print(f"Original: {test_text}")
        print(f"Sanitized: {result.sanitized_text}")
        print(f"Desired entities: {result.desired_entities}")
        
        return True
    except Exception as e:
        print(f"❌ Filter and de-identification failed: {e}")
        return False


def test_system_context_block():
    """Test system context block building"""
    print("\nTesting system context block building...")
    
    try:
        # Mock entities
        entities = [
            {"label": "DOMAIN_TERM", "value": "hasta"},
            {"label": "SUBJECT_ID", "value": "12345"},
            {"label": "PERSON", "value": "Dr. Ahmet"},
            {"label": "DATE", "value": "2024-01-01"}
        ]
        
        context_block = build_system_context_block(entities)
        print(f"Context block:\n{context_block}")
        
        return True
    except Exception as e:
        print(f"❌ System context block building failed: {e}")
        return False


def main():
    """Run all NER filter tests"""
    print("🚀 Starting NER Filter Tests")
    print("=" * 50)
    
    tests = [
        test_ner_provider_initialization,
        test_entity_extraction,
        test_filter_and_deidentify,
        test_system_context_block
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
        print("🎉 All NER filter tests passed!")
    else:
        print("⚠️  Some tests failed. Check the error messages above.")
    
    return passed == total


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
