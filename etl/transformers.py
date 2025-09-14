"""
Data Transformers - Transform and normalize data
"""
import pandas as pd
from typing import Dict, List, Any, Tuple
from datetime import datetime

class JSONNormalizer:
    """Normalize JSON data into relational structure"""
    
    def __init__(self):
        self.patients = []
        self.providers = []
        self.admissions = []
        self.transfers = []
    
    def normalize(self, json_data: Dict[str, Any]) -> Dict[str, List[Dict]]:
        """Normalize JSON data into separate entities"""
        source_file = json_data.get('_source_file', 'unknown')
        
        # Normalize patients
        if 'patients' in json_data and isinstance(json_data['patients'], list):
            for patient in json_data['patients']:
                normalized_patient = {
                    'subject_id': patient.get('subject_id'),
                    'gender': patient.get('gender'),
                    'anchor_age': patient.get('anchor_age'),
                    'anchor_year': patient.get('anchor_year'),
                    'anchor_year_group': patient.get('anchor_year_group'),
                    'dod': patient.get('dod'),
                    'source_file': source_file
                }
                self.patients.append(normalized_patient)
        
        # Normalize providers
        if 'provider' in json_data and isinstance(json_data['provider'], list):
            for provider in json_data['provider']:
                normalized_provider = {
                    'provider_id': provider.get('provider_id'),
                    'npi': provider.get('npi'),
                    'dea': provider.get('dea'),
                    'source_file': source_file
                }
                self.providers.append(normalized_provider)
        
        # Normalize admissions
        if 'admissions' in json_data and isinstance(json_data['admissions'], list):
            for admission in json_data['admissions']:
                normalized_admission = {
                    'hadm_id': admission.get('hadm_id'),
                    'subject_id': admission.get('subject_id'),
                    'admittime': admission.get('admittime'),
                    'dischtime': admission.get('dischtime'),
                    'deathtime': admission.get('deathtime'),
                    'admission_type': admission.get('admission_type'),
                    'admit_provider_id': admission.get('admit_provider_id'),
                    'admission_location': admission.get('admission_location'),
                    'discharge_location': admission.get('discharge_location'),
                    'insurance': admission.get('insurance'),
                    'language': admission.get('language'),
                    'marital_status': admission.get('marital_status'),
                    'race': admission.get('race'),
                    'edregtime': admission.get('edregtime'),
                    'edouttime': admission.get('edouttime'),
                    'hospital_expire_flag': admission.get('hospital_expire_flag'),
                    'source_file': source_file
                }
                self.admissions.append(normalized_admission)
        
        # Normalize transfers
        if 'transfers' in json_data and isinstance(json_data['transfers'], list):
            for transfer in json_data['transfers']:
                normalized_transfer = {
                    'transfer_id': transfer.get('transfer_id'),
                    'subject_id': transfer.get('subject_id'),
                    'hadm_id': transfer.get('hadm_id'),
                    'eventtype': transfer.get('eventtype'),
                    'careunit': transfer.get('careunit'),
                    'intime': transfer.get('intime'),
                    'outtime': transfer.get('outtime'),
                    'source_file': source_file
                }
                self.transfers.append(normalized_transfer)
        
        return {
            'patients': self.patients,
            'providers': self.providers,
            'admissions': self.admissions,
            'transfers': self.transfers
        }
    
    def get_normalized_data(self) -> Dict[str, List[Dict]]:
        """Get all normalized data"""
        return {
            'patients': self.patients,
            'providers': self.providers,
            'admissions': self.admissions,
            'transfers': self.transfers
        }

class CSVTransformer:
    """Transform CSV data for database storage"""
    
    def __init__(self):
        self.csv_tables = {}
    
    def transform(self, csv_data: Dict[str, Any]) -> Dict[str, Any]:
        """Transform CSV data"""
        table_name = csv_data['table_name']
        df = csv_data['data']
        source_file = csv_data['source_file']
        
        # Clean column names
        df.columns = [col.replace(' ', '_').replace('-', '_').lower() for col in df.columns]
        
        # Add metadata columns only if they don't exist
        if 'created_at' not in df.columns:
            df['created_at'] = datetime.now().isoformat()
        
        # Store transformed data
        self.csv_tables[table_name] = df
        
        return {
            'table_name': table_name,
            'data': df,
            'source_file': source_file
        }
    
    def get_transformed_data(self) -> Dict[str, pd.DataFrame]:
        """Get all transformed CSV data"""
        return self.csv_tables

class DataTransformer:
    """Main data transformer"""
    
    def __init__(self):
        self.json_normalizer = JSONNormalizer()
        self.csv_transformer = CSVTransformer()
    
    def transform_all(self, extracted_data: Dict[str, List[Any]]) -> Dict[str, Any]:
        """Transform all extracted data"""
        result = {
            'normalized_json': {},
            'transformed_csv': {}
        }
        
        # Transform JSON data
        for json_data in extracted_data['json_data']:
            normalized = self.json_normalizer.normalize(json_data)
        
        result['normalized_json'] = self.json_normalizer.get_normalized_data()
        
        # Transform CSV data
        for csv_data in extracted_data['csv_data']:
            transformed = self.csv_transformer.transform(csv_data)
            result['transformed_csv'][transformed['table_name']] = transformed
        
        return result
