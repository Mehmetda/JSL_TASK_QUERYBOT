"""
ETL Pipeline - Main pipeline orchestrator
"""
import os
from pathlib import Path
from typing import Dict, Any
from .extractors import DataExtractor
from .transformers import DataTransformer
from .loaders import DatabaseLoader

class ETLPipeline:
    """Main ETL Pipeline"""
    
    def __init__(self, data_dir: str, db_path: str):
        self.data_dir = data_dir
        self.db_path = db_path
        self.extractor = DataExtractor(data_dir)
        self.transformer = DataTransformer()
        self.loader = DatabaseLoader(db_path)
    
    def run(self) -> Dict[str, Any]:
        """Run complete ETL pipeline"""
        print("🔄 Starting ETL Pipeline")
        print("=" * 60)
        
        try:
            # Connect to database
            self.loader.connect()
            
            # Create tables
            print("\n📋 Creating database tables...")
            self.loader.create_tables()
            
            # Extract data
            print("\n📥 Extracting data...")
            extracted_data = self.extractor.extract_all()
            print(f"  - JSON files: {len(extracted_data['json_data'])}")
            print(f"  - CSV files: {len(extracted_data['csv_data'])}")
            
            # Transform data
            print("\n🔄 Transforming data...")
            transformed_data = self.transformer.transform_all(extracted_data)
            
            # Load raw JSON data (backup)
            print("\n📤 Loading raw JSON data...")
            self.loader.load_raw_json_data(extracted_data['raw_json_data'])
            
            # Load normalized data
            print("\n📤 Loading normalized data...")
            self.loader.load_normalized_data(transformed_data['normalized_json'])
            
            # Load CSV data
            print("\n📤 Loading CSV data...")
            self.loader.load_csv_data(transformed_data['transformed_csv'])
            
            # Get summary
            print("\n📊 Database Summary:")
            summary = self.loader.get_summary()
            for table, count in summary.items():
                print(f"  - {table}: {count} records")
            
            print("\n✅ ETL Pipeline completed successfully!")
            
            return {
                'status': 'success',
                'summary': summary,
                'extracted': {
                    'json_files': len(extracted_data['json_data']),
                    'csv_files': len(extracted_data['csv_data'])
                }
            }
            
        except Exception as e:
            print(f"\n❌ ETL Pipeline failed: {e}")
            return {
                'status': 'error',
                'error': str(e)
            }
        finally:
            self.loader.close()

def run_etl_pipeline(data_dir: str = None, db_path: str = None) -> Dict[str, Any]:
    """Run ETL pipeline with default parameters"""
    if data_dir is None:
        data_dir = r"C:\Users\mehmet\Desktop\JSL_DATA"
    if db_path is None:
        db_path = "app/db/demo.sqlite"
    
    pipeline = ETLPipeline(data_dir, db_path)
    return pipeline.run()

if __name__ == "__main__":
    # Run ETL pipeline
    result = run_etl_pipeline()
    
    if result['status'] == 'success':
        print(f"\n🎉 ETL completed! Processed {result['extracted']['json_files']} JSON files and {result['extracted']['csv_files']} CSV files.")
    else:
        print(f"\n💥 ETL failed: {result['error']}")
