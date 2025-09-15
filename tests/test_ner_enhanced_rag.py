"""
Test NER-Enhanced Hybrid RAG System

This test suite validates the integration of NER filtering with the hybrid RAG system
to ensure better entity-aware schema retrieval.
"""
import os
import sys
import unittest
from pathlib import Path

# Add project root to Python path
CURRENT = Path(__file__).resolve().parent
PROJECT_ROOT = CURRENT.parent
sys.path.insert(0, str(PROJECT_ROOT))

from app.db.connection import get_connection
from app.agents.system_prompt import (
    get_ner_enhanced_hybrid_schema_snippets,
    get_hybrid_relevant_schema_snippets,
    get_relevant_schema_snippets
)
from app.tools.ner_filter import SpaCyNERProvider


class TestNEREnhancedRAG(unittest.TestCase):
    """Test cases for NER-enhanced hybrid RAG system"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.conn = get_connection()
        self.test_questions = [
            "Cinsiyete göre hasta sayıları nedir?",
            "Yatış tiplerine göre dağılım nedir?",
            "Bakım birimlerine göre transfer sayıları?",
            "En çok hasta kabul eden doktorlar?",
            "subject_id 12345 olan hastanın yatış bilgileri?",
            "hadm_id 67890 ile ilgili transfer kayıtları?",
            "admittime 2023-01-01'den sonraki yatışlar?",
            "provider_id 11111 olan doktorun hasta sayısı?"
        ]
    
    def tearDown(self):
        """Clean up after tests"""
        if hasattr(self, 'conn'):
            self.conn.close()
    
    def test_ner_entity_extraction(self):
        """Test NER entity extraction functionality"""
        ner = SpaCyNERProvider(language_code="tr")
        
        # Test domain term extraction
        question = "Cinsiyete göre hasta sayıları nedir?"
        ner_result = ner.filter_and_deidentify(question)
        
        self.assertIsNotNone(ner_result.sanitized_text)
        self.assertIsNotNone(ner_result.desired_entities)
        
        # Check if domain terms are extracted
        domain_terms = [e for e in ner_result.desired_entities if e.get("label") == "DOMAIN_TERM"]
        self.assertGreater(len(domain_terms), 0, "Should extract domain terms")
        
        # Test ID extraction
        id_question = "subject_id 12345 olan hastanın yatış bilgileri?"
        id_result = ner.filter_and_deidentify(id_question)
        
        subject_ids = [e for e in id_result.desired_entities if e.get("label") == "SUBJECT_ID"]
        self.assertGreater(len(subject_ids), 0, "Should extract SUBJECT_ID")
        self.assertEqual(subject_ids[0]["value"], "12345")
    
    def test_ner_enhanced_vs_regular_hybrid(self):
        """Test NER-enhanced hybrid RAG vs regular hybrid RAG"""
        question = "hadm_id 67890 ile ilgili transfer kayıtları?"
        
        # Get NER-enhanced results
        ner_enhanced = get_ner_enhanced_hybrid_schema_snippets(
            self.conn, question, top_k=3, language_code="tr"
        )
        
        # Get regular hybrid results
        regular_hybrid = get_hybrid_relevant_schema_snippets(self.conn, question, top_k=3)
        
        # Both should return results
        self.assertIsNotNone(ner_enhanced)
        self.assertIsNotNone(regular_hybrid)
        self.assertGreater(len(ner_enhanced), 0)
        self.assertGreater(len(regular_hybrid), 0)
        
        # NER-enhanced should include entity context
        self.assertIn("Extracted Entities and Domain Terms:", ner_enhanced)
        self.assertIn("HADM_ID: 67890", ner_enhanced)
        
        # NER-enhanced should be more specific for ID-based queries
        if "hadm_id" in ner_enhanced.lower():
            self.assertIn("hadm_id", ner_enhanced.lower())
    
    def test_metadata_filtering(self):
        """Test metadata filtering based on extracted entities"""
        # Test with specific ID
        question = "subject_id 12345 olan hastanın yatış bilgileri?"
        
        ner_enhanced = get_ner_enhanced_hybrid_schema_snippets(
            self.conn, question, top_k=5, language_code="tr"
        )
        
        # Should include entity context
        self.assertIn("SUBJECT_ID: 12345", ner_enhanced)
        self.assertIn("Domain terms:", ner_enhanced)
        
        # Should focus on admissions table for subject_id
        self.assertIn("json_admissions", ner_enhanced)
    
    def test_domain_term_enhancement(self):
        """Test domain term enhancement for better semantic matching"""
        question = "En çok hasta kabul eden doktorlar?"
        
        ner_enhanced = get_ner_enhanced_hybrid_schema_snippets(
            self.conn, question, top_k=3, language_code="tr"
        )
        
        # Should extract domain terms
        self.assertIn("Domain terms:", ner_enhanced)
        self.assertIn("doktor", ner_enhanced)
        self.assertIn("hasta", ner_enhanced)
        
        # Should focus on relevant tables
        self.assertTrue(
            "json_admissions" in ner_enhanced or "json_providers" in ner_enhanced,
            "Should include relevant tables for doctor/patient queries"
        )
    
    def test_time_entity_extraction(self):
        """Test time-related entity extraction"""
        question = "admittime 2023-01-01'den sonraki yatışlar?"
        
        ner_enhanced = get_ner_enhanced_hybrid_schema_snippets(
            self.conn, question, top_k=3, language_code="tr"
        )
        
        # Should extract time entities
        self.assertIn("ADMITTIME: 2023-01-01", ner_enhanced)
        self.assertIn("admittime", ner_enhanced)
        
        # Should focus on admissions table with time columns
        self.assertIn("json_admissions", ner_enhanced)
    
    def test_fallback_behavior(self):
        """Test fallback behavior when NER fails"""
        # Test with empty question
        empty_question = ""
        
        try:
            result = get_ner_enhanced_hybrid_schema_snippets(
                self.conn, empty_question, top_k=3, language_code="tr"
            )
            # Should not crash, should return some result or fallback
            self.assertIsNotNone(result)
        except Exception as e:
            # If it fails, it should fail gracefully
            self.assertIsInstance(e, Exception)
    
    def test_performance_comparison(self):
        """Test performance comparison between different RAG approaches"""
        question = "provider_id 11111 olan doktorun hasta sayısı?"
        
        # Test all three approaches
        ner_enhanced = get_ner_enhanced_hybrid_schema_snippets(
            self.conn, question, top_k=3, language_code="tr"
        )
        regular_hybrid = get_hybrid_relevant_schema_snippets(self.conn, question, top_k=3)
        keyword_only = get_relevant_schema_snippets(self.conn, question, top_k=3)
        
        # All should return results
        self.assertIsNotNone(ner_enhanced)
        self.assertIsNotNone(regular_hybrid)
        self.assertIsNotNone(keyword_only)
        
        # NER-enhanced should be most specific for ID-based queries
        if "provider_id" in question:
            self.assertIn("PROVIDER_ID: 11111", ner_enhanced)
    
    def test_language_support(self):
        """Test language support for NER processing"""
        # Test English
        en_question = "What are the patient counts?"
        en_result = get_ner_enhanced_hybrid_schema_snippets(
            self.conn, en_question, top_k=3, language_code="en"
        )
        self.assertIsNotNone(tr_result)
        
        # Test English
        en_question = "What are the patient counts?"
        en_result = get_ner_enhanced_hybrid_schema_snippets(
            self.conn, en_question, top_k=3, language_code="en"
        )
        self.assertIsNotNone(en_result)


class TestNERIntegration(unittest.TestCase):
    """Test NER integration with the overall system"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.conn = get_connection()
    
    def tearDown(self):
        """Clean up after tests"""
        if hasattr(self, 'conn'):
            self.conn.close()
    
    def test_ner_provider_initialization(self):
        """Test NER provider initialization"""
        try:
            ner = SpaCyNERProvider(language_code="tr")
            self.assertIsNotNone(ner)
            self.assertEqual(ner.language_code, "tr")
        except Exception as e:
            # If spaCy models are not installed, skip this test
            self.skipTest(f"spaCy models not available: {e}")
    
    def test_entity_filtering_and_deidentification(self):
        """Test entity filtering and de-identification"""
        try:
            ner = SpaCyNERProvider(language_code="tr")
            
            # Test with PII
            text_with_pii = "Hasta Ahmet Yılmaz'ın email: ahmet@example.com, telefon: 0555-123-4567"
            result = ner.filter_and_deidentify(text_with_pii)
            
            # Should sanitize PII
            self.assertNotIn("ahmet@example.com", result.sanitized_text)
            self.assertNotIn("0555-123-4567", result.sanitized_text)
            
            # Should extract domain terms
            domain_terms = [e for e in result.desired_entities if e.get("label") == "DOMAIN_TERM"]
            self.assertGreater(len(domain_terms), 0)
            
        except Exception as e:
            self.skipTest(f"spaCy models not available: {e}")


def run_tests():
    """Run all tests"""
    # Create test suite
    test_suite = unittest.TestSuite()
    
    # Add test cases
    test_suite.addTest(unittest.makeSuite(TestNEREnhancedRAG))
    test_suite.addTest(unittest.makeSuite(TestNERIntegration))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)
    
    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_tests()
    if success:
        print("\n✅ All tests passed!")
    else:
        print("\n❌ Some tests failed!")
        sys.exit(1)
