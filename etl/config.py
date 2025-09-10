"""
ETL Configuration
"""
import os
from pathlib import Path

class ETLConfig:
    """ETL Configuration class"""
    
    def __init__(self):
        self.data_dir = os.getenv("DATA_DIR", r"C:\Users\mehmet\Desktop\JSL_DATA")
        self.db_path = os.getenv("DB_PATH", "app/db/demo.sqlite")
        self.batch_size = int(os.getenv("BATCH_SIZE", "1000"))
        self.verbose = os.getenv("VERBOSE", "true").lower() == "true"
    
    def get_data_dir(self) -> Path:
        """Get data directory path"""
        return Path(self.data_dir)
    
    def get_db_path(self) -> Path:
        """Get database path"""
        return Path(self.db_path)
    
    def validate(self) -> bool:
        """Validate configuration"""
        data_dir = self.get_data_dir()
        if not data_dir.exists():
            print(f"❌ Data directory not found: {data_dir}")
            return False
        
        # Check if data directory has files
        json_files = list(data_dir.glob("*.json"))
        zip_files = list(data_dir.rglob("*.zip"))
        
        if not json_files and not zip_files:
            print(f"❌ No JSON or ZIP files found in: {data_dir}")
            return False
        
        print(f"✅ Configuration valid:")
        print(f"  - Data directory: {data_dir}")
        print(f"  - Database path: {self.get_db_path()}")
        print(f"  - JSON files: {len(json_files)}")
        print(f"  - ZIP files: {len(zip_files)}")
        
        return True

# Default configuration
config = ETLConfig()
