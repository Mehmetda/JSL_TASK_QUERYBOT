"""
Data Loaders - Load transformed data into database
"""
import sqlite3
from pathlib import Path
from typing import Dict, List, Any
import pandas as pd

class DatabaseLoader:
    """Load data into SQLite database"""
    
    def __init__(self, db_path: str):
        self.db_path = Path(db_path)
        self.conn = None
    
    def connect(self):
        """Connect to database"""
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(str(self.db_path))
        return self.conn
    
    def close(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()
    
    def create_tables(self):
        """Create normalized tables"""
        cursor = self.conn.cursor()
        
        # Drop existing tables
        tables_to_drop = [
            'patient_admissions', 'patient_transfers', 'patient_providers',
            'admissions', 'transfers', 'providers', 'patients', 'csv_data',
            'csv_tables', 'json_patients', 'json_providers', 'json_admissions', 
            'json_transfers', 'raw_json_data'
        ]
        
        for table in tables_to_drop:
            cursor.execute(f"DROP TABLE IF EXISTS {table}")
        
        # Create separate tables for each data type
        
        # 1. Raw JSON data table (for backup)
        cursor.execute("""
            CREATE TABLE raw_json_data (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                file_name TEXT,
                json_data TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # 2. JSON Patients table
        cursor.execute("""
            CREATE TABLE json_patients (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                subject_id INTEGER,
                gender TEXT,
                anchor_age INTEGER,
                anchor_year INTEGER,
                anchor_year_group TEXT,
                dod TEXT,
                source_file TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # 3. JSON Providers table
        cursor.execute("""
            CREATE TABLE json_providers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                provider_id TEXT,
                npi INTEGER,
                dea TEXT,
                source_file TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # 4. JSON Admissions table
        cursor.execute("""
            CREATE TABLE json_admissions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                hadm_id INTEGER,
                subject_id INTEGER,
                admittime TEXT,
                dischtime TEXT,
                deathtime TEXT,
                admission_type TEXT,
                admit_provider_id TEXT,
                admission_location TEXT,
                discharge_location TEXT,
                insurance TEXT,
                language TEXT,
                marital_status TEXT,
                race TEXT,
                edregtime TEXT,
                edouttime TEXT,
                hospital_expire_flag INTEGER,
                source_file TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # 5. JSON Transfers table
        cursor.execute("""
            CREATE TABLE json_transfers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                transfer_id INTEGER,
                subject_id INTEGER,
                hadm_id INTEGER,
                eventtype TEXT,
                careunit TEXT,
                intime TEXT,
                outtime TEXT,
                source_file TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # 6. CSV tables registry
        cursor.execute("""
            CREATE TABLE csv_tables (
                table_name TEXT PRIMARY KEY,
                description TEXT,
                source_file TEXT,
                row_count INTEGER,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        self.conn.commit()
        print("✅ Separate data tables created")
    
    def load_normalized_data(self, normalized_data: Dict[str, List[Dict]]):
        """Load normalized JSON data into separate tables"""
        cursor = self.conn.cursor()
        
        # Load patients into json_patients table
        if normalized_data.get('patients'):
            for patient in normalized_data['patients']:
                cursor.execute("""
                    INSERT INTO json_patients 
                    (subject_id, gender, anchor_age, anchor_year, anchor_year_group, dod, source_file)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    patient.get('subject_id'),
                    patient.get('gender'),
                    patient.get('anchor_age'),
                    patient.get('anchor_year'),
                    patient.get('anchor_year_group'),
                    patient.get('dod'),
                    patient.get('source_file')
                ))
            print(f"✅ Loaded {len(normalized_data['patients'])} patients into json_patients table")
        
        # Load providers into json_providers table
        if normalized_data.get('providers'):
            for provider in normalized_data['providers']:
                cursor.execute("""
                    INSERT INTO json_providers 
                    (provider_id, npi, dea, source_file)
                    VALUES (?, ?, ?, ?)
                """, (
                    provider.get('provider_id'),
                    provider.get('npi'),
                    provider.get('dea'),
                    provider.get('source_file')
                ))
            print(f"✅ Loaded {len(normalized_data['providers'])} providers into json_providers table")
        
        # Load admissions into json_admissions table
        if normalized_data.get('admissions'):
            for admission in normalized_data['admissions']:
                cursor.execute("""
                    INSERT INTO json_admissions 
                    (hadm_id, subject_id, admittime, dischtime, deathtime, 
                     admission_type, admit_provider_id, admission_location, 
                     discharge_location, insurance, language, marital_status, 
                     race, edregtime, edouttime, hospital_expire_flag, source_file)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    admission.get('hadm_id'),
                    admission.get('subject_id'),
                    admission.get('admittime'),
                    admission.get('dischtime'),
                    admission.get('deathtime'),
                    admission.get('admission_type'),
                    admission.get('admit_provider_id'),
                    admission.get('admission_location'),
                    admission.get('discharge_location'),
                    admission.get('insurance'),
                    admission.get('language'),
                    admission.get('marital_status'),
                    admission.get('race'),
                    admission.get('edregtime'),
                    admission.get('edouttime'),
                    admission.get('hospital_expire_flag'),
                    admission.get('source_file')
                ))
            print(f"✅ Loaded {len(normalized_data['admissions'])} admissions into json_admissions table")
        
        # Load transfers into json_transfers table
        if normalized_data.get('transfers'):
            for transfer in normalized_data['transfers']:
                cursor.execute("""
                    INSERT INTO json_transfers 
                    (transfer_id, subject_id, hadm_id, eventtype, careunit, intime, outtime, source_file)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    transfer.get('transfer_id'),
                    transfer.get('subject_id'),
                    transfer.get('hadm_id'),
                    transfer.get('eventtype'),
                    transfer.get('careunit'),
                    transfer.get('intime'),
                    transfer.get('outtime'),
                    transfer.get('source_file')
                ))
            print(f"✅ Loaded {len(normalized_data['transfers'])} transfers into json_transfers table")
        
        self.conn.commit()
        print("✅ All JSON data loaded into separate tables")
    
    def load_raw_json_data(self, raw_json_data: List[Dict]):
        """Load raw JSON data for backup"""
        cursor = self.conn.cursor()
        
        for raw_data in raw_json_data:
            cursor.execute("""
                INSERT INTO raw_json_data 
                (file_name, json_data)
                VALUES (?, ?)
            """, (
                raw_data.get('file_name'),
                raw_data.get('json_data')
            ))
        
        self.conn.commit()
        print(f"✅ Loaded {len(raw_json_data)} raw JSON files for backup")
    
    def load_csv_data(self, csv_data: List[Dict[str, Any]]):
        """Load CSV data into separate tables"""
        cursor = self.conn.cursor()
        
        for data in csv_data:
            table_name = data['table_name']
            df = data['data']
            source_file = data['source_file']
            
            print(f"📤 Loading {table_name} ({len(df)} rows)...")
            
            # Create table for CSV data
            self.create_csv_table(table_name, df)
            
            # Insert data
            row_count = self.insert_csv_data(table_name, df)
            
            # Register table
            cursor.execute("""
                INSERT OR REPLACE INTO csv_tables 
                (table_name, description, source_file, row_count)
                VALUES (?, ?, ?, ?)
                """, (table_name, f"Data from {source_file}", source_file, row_count))
            
            print(f"✅ Created table {table_name} with {row_count} rows")
        
        self.conn.commit()
        print("✅ All CSV data loaded into separate tables")
    
    def create_csv_table(self, table_name: str, df: pd.DataFrame):
        """Create table for CSV data"""
        cursor = self.conn.cursor()
        
        # Generate column definitions
        columns = []
        seen_columns = set()
        
        for col in df.columns:
            col_name = col.replace(' ', '_').replace('-', '_').lower()
            col_name = f"_{col_name}" if col_name in ['id', 'key', 'value'] else col_name
            
            # Skip duplicate columns
            if col_name in seen_columns:
                continue
            seen_columns.add(col_name)
            
            # Determine data type
            if df[col].dtype == 'int64':
                col_type = 'INTEGER'
            elif df[col].dtype == 'float64':
                col_type = 'REAL'
            else:
                col_type = 'TEXT'
            
            columns.append(f"{col_name} {col_type}")
        
        # Add metadata columns only if they don't exist
        if 'source_file' not in seen_columns:
            columns.append("source_file TEXT")
        if 'created_at' not in seen_columns:
            columns.append("created_at DATETIME DEFAULT CURRENT_TIMESTAMP")
        
        # Create table
        create_sql = f"""
            CREATE TABLE {table_name} (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                {', '.join(columns)}
            )
        """
        
        cursor.execute(create_sql)
    
    def insert_csv_data(self, table_name: str, df: pd.DataFrame) -> int:
        """Insert CSV data into table and return row count"""
        cursor = self.conn.cursor()
        row_count = 0
        
        for _, row in df.iterrows():
            # Prepare values
            values = []
            for col in df.columns:
                col_name = col.replace(' ', '_').replace('-', '_').lower()
                col_name = f"_{col_name}" if col_name in ['id', 'key', 'value'] else col_name
                values.append(row[col])
            
            # Create placeholders
            placeholders = ', '.join(['?' for _ in range(len(values))])
            
            # Insert
            insert_sql = f"INSERT INTO {table_name} VALUES (NULL, {placeholders})"
            cursor.execute(insert_sql, values)
            row_count += 1
        
        return row_count
    
    def get_summary(self) -> Dict[str, int]:
        """Get database summary"""
        cursor = self.conn.cursor()
        
        summary = {}
        
        # Get all tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        
        for table in tables:
            table_name = table[0]
            cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
            count = cursor.fetchone()[0]
            summary[table_name] = count
        
        return summary
