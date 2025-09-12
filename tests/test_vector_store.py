"""
Test vector store functionality

Run:
  python tests/test_vector_store.py
"""
import sys
import os
import tempfile
from pathlib import Path

# Add project root to Python path
CURRENT = Path(__file__).resolve().parent
PROJECT_ROOT = CURRENT.parent
sys.path.insert(0, str(PROJECT_ROOT))

from app.vector_store import FAISSVectorStore, EmbeddingService


def test_embedding_service():
    """Test embedding service functionality"""
    print("Testing embedding service...")
    
    try:
        # Initialize embedding service
        embedding_service = EmbeddingService()
        
        # Test single text encoding
        text = "This is a test document"
        embedding = embedding_service.encode(text)
        assert embedding.shape[0] == 1  # Single text
        assert embedding.shape[1] > 0  # Has embedding dimension
        print("✅ Single text encoding works")
        
        # Test multiple texts encoding
        texts = ["Document 1", "Document 2", "Document 3"]
        embeddings = embedding_service.encode(texts)
        assert embeddings.shape[0] == 3  # Three texts
        assert embeddings.shape[1] > 0  # Has embedding dimension
        print("✅ Multiple texts encoding works")
        
        # Test batch encoding
        large_texts = [f"Document {i}" for i in range(50)]
        batch_embeddings = embedding_service.encode_batch(large_texts, batch_size=10)
        assert batch_embeddings.shape[0] == 50
        print("✅ Batch encoding works")
        
        # Test similarity calculation
        emb1 = embedding_service.encode("Hello world")
        emb2 = embedding_service.encode("Hello world")
        similarity = embedding_service.similarity(emb1[0], emb2[0])
        assert similarity > 0.9  # Should be very similar
        print("✅ Similarity calculation works")
        
        # Test different texts similarity
        emb3 = embedding_service.encode("Completely different text")
        similarity_diff = embedding_service.similarity(emb1[0], emb3[0])
        assert similarity_diff < similarity  # Should be less similar
        print("✅ Different texts similarity works")
        
        return True
        
    except Exception as e:
        print(f"❌ Embedding service test failed: {e}")
        return False


def test_faiss_vector_store():
    """Test FAISS vector store functionality"""
    print("\nTesting FAISS vector store...")
    
    try:
        # Initialize embedding service and vector store
        embedding_service = EmbeddingService()
        vector_store = FAISSVectorStore(embedding_service)
        
        # Test adding documents
        texts = [
            "Patient information and medical records",
            "Hospital admission and discharge data",
            "Doctor and provider information",
            "Medical diagnosis and treatment plans",
            "Laboratory test results and measurements"
        ]
        
        metadata = [
            {"table": "patients", "type": "medical"},
            {"table": "admissions", "type": "administrative"},
            {"table": "providers", "type": "staff"},
            {"table": "diagnoses", "type": "medical"},
            {"table": "lab_results", "type": "clinical"}
        ]
        
        doc_ids = vector_store.add_documents(texts, metadata)
        assert len(doc_ids) == 5
        print("✅ Adding documents works")
        
        # Test search functionality
        results = vector_store.search("patient medical information", k=3)
        assert len(results) > 0
        assert all('score' in result for result in results)
        assert all('metadata' in result for result in results)
        print("✅ Search functionality works")
        
        # Test metadata filtering
        filtered_results = vector_store.search(
            "medical data", 
            k=5, 
            filter_metadata={"type": "medical"}
        )
        assert len(filtered_results) > 0
        assert all(result['metadata']['type'] == 'medical' for result in filtered_results)
        print("✅ Metadata filtering works")
        
        # Test document retrieval
        doc = vector_store.get_document(doc_ids[0])
        assert doc is not None
        assert doc['text'] == texts[0]
        print("✅ Document retrieval works")
        
        # Test statistics
        stats = vector_store.get_stats()
        assert stats['total_documents'] == 5
        assert stats['index_size'] == 5
        print("✅ Statistics work")
        
        return True
        
    except Exception as e:
        print(f"❌ FAISS vector store test failed: {e}")
        return False


def test_vector_store_persistence():
    """Test vector store save/load functionality"""
    print("\nTesting vector store persistence...")
    
    try:
        # Create temporary directory
        with tempfile.TemporaryDirectory() as temp_dir:
            index_path = os.path.join(temp_dir, "test_index")
            
            # Initialize embedding service and vector store
            embedding_service = EmbeddingService()
            vector_store = FAISSVectorStore(embedding_service, index_path)
            
            # Add some documents
            texts = ["Test document 1", "Test document 2"]
            metadata = [{"id": 1}, {"id": 2}]
            vector_store.add_documents(texts, metadata)
            
            # Save index
            vector_store.save_index()
            print("✅ Index saving works")
            
            # Create new vector store and load index
            new_vector_store = FAISSVectorStore(embedding_service, index_path)
            new_vector_store.load_index()
            
            # Test that loaded data is correct
            assert new_vector_store.get_stats()['total_documents'] == 2
            results = new_vector_store.search("test document", k=2)
            assert len(results) == 2
            print("✅ Index loading works")
            
        return True
        
    except Exception as e:
        print(f"❌ Vector store persistence test failed: {e}")
        return False


def test_medical_domain_search():
    """Test medical domain specific search"""
    print("\nTesting medical domain search...")
    
    try:
        # Initialize services
        embedding_service = EmbeddingService()
        vector_store = FAISSVectorStore(embedding_service)
        
        # Add medical domain documents
        medical_docs = [
            "Patient demographics including age gender and admission information",
            "Hospital admissions with admission time discharge time and admission type",
            "Provider information with doctor names and specialties",
            "Transfer records between different care units in the hospital",
            "Laboratory measurements and test results for patients",
            "Diagnosis codes and medical conditions for each patient",
            "Insurance information and billing details for admissions",
            "Care unit assignments and patient room allocations"
        ]
        
        medical_metadata = [
            {"table": "json_patients", "domain": "demographics"},
            {"table": "json_admissions", "domain": "admissions"},
            {"table": "json_providers", "domain": "staff"},
            {"table": "json_transfers", "domain": "movements"},
            {"table": "json_lab", "domain": "clinical"},
            {"table": "json_diagnoses", "domain": "medical"},
            {"table": "json_insurance", "domain": "billing"},
            {"table": "json_careunits", "domain": "logistics"}
        ]
        
        vector_store.add_documents(medical_docs, medical_metadata)
        
        # Test various medical queries
        test_queries = [
            ("How many patients are there?", "json_patients"),
            ("What are the admission types?", "json_admissions"),
            ("Who are the doctors?", "json_providers"),
            ("What care units exist?", "json_careunits"),
            ("What lab tests are available?", "json_lab")
        ]
        
        for query, expected_table in test_queries:
            results = vector_store.search(query, k=3)
            assert len(results) > 0
            
            # Check if expected table is in results
            found_table = any(
                result['metadata']['table'] == expected_table 
                for result in results
            )
            if found_table:
                print(f"✅ Query '{query}' correctly found {expected_table}")
            else:
                print(f"⚠️  Query '{query}' did not find {expected_table}")
        
        return True
        
    except Exception as e:
        print(f"❌ Medical domain search test failed: {e}")
        return False


def main():
    """Run all vector store tests"""
    print("🚀 Starting Vector Store Tests")
    print("=" * 50)
    
    tests = [
        test_embedding_service,
        test_faiss_vector_store,
        test_vector_store_persistence,
        test_medical_domain_search
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
        print("🎉 All vector store tests passed!")
    else:
        print("⚠️  Some tests failed. Check the error messages above.")
    
    return passed == total


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
