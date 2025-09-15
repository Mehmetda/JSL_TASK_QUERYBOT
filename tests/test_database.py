#!/usr/bin/env python3
"""
Test script to verify MIMIC-IV data in SQLite database
"""
import sqlite3
import json
from pathlib import Path

def test_database():
    """Test the SQLite database and show data"""
    db_path = "app/db/demo.sqlite"
    
    if not Path(db_path).exists():
        print("❌ Database file not found!")
        return
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        print("🔍 Database Test Results")
        print("=" * 50)
        
        # 1. List all tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        print(f"\n📋 Tables in database ({len(tables)}):")
        for table in tables:
            print(f"  - {table[0]}")
        
        # 2. Check data counts
        print(f"\n📊 Data counts:")
        for table in tables:
            table_name = table[0]
            if table_name != 'sqlite_sequence':
                cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
                count = cursor.fetchone()[0]
                print(f"  - {table_name}: {count} records")
        
        # 3. Sample data from key tables
        print(f"\n🔍 Sample data:")
        
        # Patients sample
        cursor.execute("SELECT * FROM json_patients LIMIT 3")
        patients = cursor.fetchall()
        print(f"\n👥 Sample patients ({len(patients)}):")
        for i, patient in enumerate(patients, 1):
            print(f"  Patient {i}: {patient}")
        
        # Admissions sample
        cursor.execute("SELECT * FROM json_admissions LIMIT 3")
        admissions = cursor.fetchall()
        print(f"\n🏥 Sample admissions ({len(admissions)}):")
        for i, admission in enumerate(admissions, 1):
            print(f"  Admission {i}: {admission}")
        
        # 4. Test a simple query
        print(f"\n🔍 Test query: Count unique patients")
        cursor.execute("SELECT COUNT(DISTINCT subject_id) FROM json_admissions")
        unique_patients = cursor.fetchone()[0]
        print(f"  Unique patients in admissions: {unique_patients}")
        
        # 5. Check raw JSON data
        cursor.execute("SELECT COUNT(*) FROM raw_json_data")
        raw_count = cursor.fetchone()[0]
        print(f"\n📄 Raw JSON files loaded: {raw_count}")
        
        conn.close()
        print(f"\n✅ Database test completed successfully!")
        
    except Exception as e:
        print(f"❌ Error testing database: {e}")

if __name__ == "__main__":
    test_database()
