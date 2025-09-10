"""
Data Extractors - Extract data from various sources
"""
import json
import zipfile
import pandas as pd
from pathlib import Path
from typing import List, Dict, Any, Iterator

class JSONExtractor:
    """Extract data from JSON files"""
    
    def __init__(self, data_dir: str):
        self.data_dir = Path(data_dir)
    
    def extract_all(self) -> Iterator[Dict[str, Any]]:
        """Extract all JSON files"""
        json_files = list(self.data_dir.glob("*.json"))
        
        for json_file in json_files:
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    data['_source_file'] = str(json_file)
                    yield data
            except Exception as e:
                print(f"❌ Error extracting {json_file}: {e}")
                continue

class ZIPExtractor:
    """Extract data from ZIP files"""
    
    def __init__(self, data_dir: str):
        self.data_dir = Path(data_dir)
    
    def extract_all(self) -> Iterator[Dict[str, Any]]:
        """Extract all CSV files from ZIP archives"""
        zip_files = list(self.data_dir.rglob("*.zip"))
        
        for zip_file in zip_files:
            try:
                with zipfile.ZipFile(zip_file, 'r') as zip_ref:
                    csv_files = [f for f in zip_ref.namelist() if f.lower().endswith('.csv')]
                    
                    for csv_file in csv_files:
                        try:
                            with zip_ref.open(csv_file) as csv_data:
                                df = pd.read_csv(csv_file)
                                
                                yield {
                                    'table_name': Path(csv_file).stem,
                                    'data': df,
                                    'source_file': str(zip_file),
                                    'csv_file': csv_file
                                }
                        except Exception as e:
                            print(f"❌ Error extracting {csv_file} from {zip_file}: {e}")
                            continue
                            
            except Exception as e:
                print(f"❌ Error processing ZIP {zip_file}: {e}")
                continue

class DataExtractor:
    """Main data extractor that combines all sources"""
    
    def __init__(self, data_dir: str):
        self.data_dir = data_dir
        self.json_extractor = JSONExtractor(data_dir)
        self.zip_extractor = ZIPExtractor(data_dir)
    
    def extract_all(self) -> Dict[str, List[Any]]:
        """Extract all data from all sources"""
        result = {
            'json_data': [],
            'csv_data': [],
            'raw_json_data': []
        }
        
        # Extract JSON data
        for json_data in self.json_extractor.extract_all():
            result['json_data'].append(json_data)
            
            # Also store raw JSON for backup
            result['raw_json_data'].append({
                'file_name': Path(json_data['_source_file']).name,
                'json_data': json.dumps(json_data, ensure_ascii=False, indent=2),
                'source_file': json_data['_source_file']
            })
        
        # Extract CSV data
        for csv_data in self.zip_extractor.extract_all():
            result['csv_data'].append(csv_data)
        
        return result
