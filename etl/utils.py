"""
ETL Utilities
"""
import sqlite3
import json
from pathlib import Path
from typing import Dict, List, Any

def test_database_connection(db_path: str) -> bool:
    """Test database connection"""
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT 1")
        conn.close()
        return True
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False

def get_database_schema(db_path: str) -> Dict[str, List[str]]:
    """Get database schema information"""
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Get all tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        
        schema = {}
        for table in tables:
            table_name = table[0]
            cursor.execute(f"PRAGMA table_info({table_name})")
            columns = cursor.fetchall()
            schema[table_name] = [col[1] for col in columns]
        
        conn.close()
        return schema
    except Exception as e:
        print(f"❌ Error getting schema: {e}")
        return {}

def get_table_counts(db_path: str) -> Dict[str, int]:
    """Get record counts for all tables"""
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        
        counts = {}
        for table in tables:
            table_name = table[0]
            cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
            count = cursor.fetchone()[0]
            counts[table_name] = count
        
        conn.close()
        return counts
    except Exception as e:
        print(f"❌ Error getting counts: {e}")
        return {}

def validate_data_integrity(db_path: str) -> Dict[str, Any]:
    """Validate data integrity"""
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        validation_results = {
            'foreign_keys': {},
            'null_values': {},
            'duplicates': {}
        }
        
        # Check foreign key relationships
        cursor.execute("""
            SELECT COUNT(*) FROM admissions a 
            LEFT JOIN patients p ON a.subject_id = p.subject_id 
            WHERE p.subject_id IS NULL
        """)
        validation_results['foreign_keys']['admissions_patients'] = cursor.fetchone()[0]
        
        cursor.execute("""
            SELECT COUNT(*) FROM transfers t 
            LEFT JOIN patients p ON t.subject_id = p.subject_id 
            WHERE p.subject_id IS NULL
        """)
        validation_results['foreign_keys']['transfers_patients'] = cursor.fetchone()[0]
        
        # Check for null values in key fields
        cursor.execute("SELECT COUNT(*) FROM patients WHERE subject_id IS NULL")
        validation_results['null_values']['patients_subject_id'] = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM admissions WHERE hadm_id IS NULL")
        validation_results['null_values']['admissions_hadm_id'] = cursor.fetchone()[0]
        
        # Check for duplicates
        cursor.execute("SELECT COUNT(*) FROM (SELECT subject_id FROM patients GROUP BY subject_id HAVING COUNT(*) > 1)")
        validation_results['duplicates']['patients_subject_id'] = cursor.fetchone()[0]
        
        conn.close()
        return validation_results
    except Exception as e:
        print(f"❌ Error validating data: {e}")
        return {}

def export_sample_data(db_path: str, output_dir: str = "etl/samples"):
    """Export sample data for inspection"""
    try:
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Get all tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        
        for table in tables:
            table_name = table[0]
            cursor.execute(f"SELECT * FROM {table_name} LIMIT 10")
            rows = cursor.fetchall()
            
            # Get column names
            cursor.execute(f"PRAGMA table_info({table_name})")
            columns = [col[1] for col in cursor.fetchall()]
            
            # Create sample data
            sample_data = {
                'table_name': table_name,
                'columns': columns,
                'sample_rows': rows,
                'total_rows': len(rows)
            }
            
            # Save to file
            sample_file = output_path / f"{table_name}_sample.json"
            with open(sample_file, 'w', encoding='utf-8') as f:
                json.dump(sample_data, f, indent=2, default=str)
            
            print(f"✅ Exported sample data for {table_name}")
        
        conn.close()
        print(f"✅ Sample data exported to {output_path}")
        
    except Exception as e:
        print(f"❌ Error exporting sample data: {e}")

def cleanup_database(db_path: str):
    """Clean up database (remove old data)"""
    try:
        if Path(db_path).exists():
            Path(db_path).unlink()
            print(f"✅ Removed existing database: {db_path}")
        
        # Remove journal files
        journal_files = [
            f"{db_path}-journal",
            f"{db_path}-wal",
            f"{db_path}-shm"
        ]
        
        for journal_file in journal_files:
            if Path(journal_file).exists():
                Path(journal_file).unlink()
                print(f"✅ Removed journal file: {journal_file}")
        
    except Exception as e:
        print(f"❌ Error cleaning up database: {e}")
