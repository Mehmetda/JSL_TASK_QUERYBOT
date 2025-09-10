"""
Run ETL Pipeline
"""
import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from etl.pipeline import run_etl_pipeline
from etl.config import config
from etl.utils import cleanup_database, test_database_connection, get_table_counts

def main():
    """Main function to run ETL pipeline"""
    print("🚀 Medical QueryBot ETL Pipeline")
    print("=" * 60)
    
    # Validate configuration
    if not config.validate():
        print("❌ Configuration validation failed!")
        return
    
    # Clean up existing database
    print("\n🧹 Cleaning up existing database...")
    cleanup_database(str(config.get_db_path()))
    
    # Run ETL pipeline
    print("\n🔄 Running ETL pipeline...")
    result = run_etl_pipeline(
        data_dir=str(config.get_data_dir()),
        db_path=str(config.get_db_path())
    )
    
    if result['status'] == 'success':
        print("\n🎉 ETL Pipeline completed successfully!")
        
        # Test database connection
        print("\n🔍 Testing database connection...")
        if test_database_connection(str(config.get_db_path())):
            print("✅ Database connection successful")
            
            # Show final summary
            print("\n📊 Final Database Summary:")
            counts = get_table_counts(str(config.get_db_path()))
            for table, count in counts.items():
                print(f"  - {table}: {count} records")
        else:
            print("❌ Database connection failed")
    else:
        print(f"\n💥 ETL Pipeline failed: {result['error']}")

if __name__ == "__main__":
    main()
