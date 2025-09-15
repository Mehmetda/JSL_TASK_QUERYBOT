"""
Table allowlist security module
"""
import os
from typing import List, Set, Optional
import logging
from app.models.query_models import SecurityInfo

logger = logging.getLogger(__name__)


class TableAllowlist:
    """Manages table access permissions"""
    
    def __init__(self, allowed_tables: Optional[List[str]] = None):
        """
        Initialize table allowlist
        
        Args:
            allowed_tables: List of allowed table names. If None, loads from config
        """
        self.allowed_tables = set(allowed_tables or self._load_from_config())
        self.blocked_operations = set()
        
        logger.info(f"Table allowlist initialized with {len(self.allowed_tables)} tables")

        # Common alias → canonical table mapping to reduce false blocks
        # Example: "admissions" → "json_admissions"
        self._generic_to_canonical = {
            "patients": "json_patients",
            "patient": "json_patients",
            "admissions": "json_admissions",
            "admission": "json_admissions",
            "providers": "json_providers",
            "provider": "json_providers",
            "transfers": "json_transfers",
            "transfer": "json_transfers",
            "lab": "json_lab",
            "labs": "json_lab",
            "diagnoses": "json_diagnoses",
            "diagnosis": "json_diagnoses",
            "insurance": "json_insurance",
            "careunits": "json_careunits",
            "careunit": "json_careunits",
        }

        # Common typos → canonical table mapping (defensive normalization)
        # Example: "json_admissionss" → "json_admissions"
        self._typo_to_canonical = {
            "json_admission": "json_admissions",
            "json_admissionss": "json_admissions",
            "json_patientss": "json_patients",
            "json_patient": "json_patients",
            "json_provider": "json_providers",
            "json_transfer": "json_transfers",
            "json_careunit": "json_careunits",
            "json_labs": "json_lab",
            "json_diagnosis": "json_diagnoses",
            "json_insurances": "json_insurance",
        }
    
    def _load_from_config(self) -> List[str]:
        """Load allowed tables from configuration"""
        try:
            # Load from environment variable
            env_tables = os.getenv("ALLOWED_TABLES", "")
            if env_tables:
                return [table.strip() for table in env_tables.split(",") if table.strip()]
            
            # Default allowed tables for medical domain
            return [
                "json_patients",
                "json_admissions", 
                "json_providers",
                "json_transfers",
                "json_lab",
                "json_diagnoses",
                "json_insurance",
                "json_careunits"
            ]
            
        except Exception as e:
            logger.error(f"Error loading table allowlist from config: {e}")
            return []
    
    def is_table_allowed(self, table_name: str) -> bool:
        """
        Check if a table is allowed
        
        Args:
            table_name: Name of the table to check
            
        Returns:
            True if table is allowed, False otherwise
        """
        # Normalize table name (remove quotes, convert to lowercase)
        normalized_name = table_name.strip().strip('"').strip("'").lower()
        # First, fix common typos
        normalized_name = self._typo_to_canonical.get(normalized_name, normalized_name)
        # Then, map common generic names to canonical allowed table names
        canonical_name = self._generic_to_canonical.get(normalized_name, normalized_name)
        
        # Check if table is in allowlist
        is_allowed = canonical_name in self.allowed_tables
        
        if not is_allowed:
            # Provide suggestion if a canonical mapping exists but is not allowed
            if normalized_name != canonical_name:
                logger.warning(
                    f"Access denied to table: {table_name}. Did you mean '{canonical_name}'?"
                )
            else:
                logger.warning(f"Access denied to table: {table_name}")
            self.blocked_operations.add(f"table_access:{table_name}")
        
        return is_allowed
    
    def get_allowed_tables(self) -> List[str]:
        """Get list of allowed tables"""
        return sorted(list(self.allowed_tables))
    
    
    def validate_sql_tables(self, sql_query: str) -> tuple[bool, List[str], List[str]]:
        """
        Validate that all tables in SQL query are allowed
        
        Args:
            sql_query: SQL query to validate
            
        Returns:
            Tuple of (is_valid, allowed_tables, blocked_tables)
        """
        try:
            # Extract table names from SQL query
            tables = self._extract_tables_from_sql(sql_query)
            
            allowed_tables = []
            blocked_tables = []
            
            for table in tables:
                if self.is_table_allowed(table):
                    allowed_tables.append(table)
                else:
                    blocked_tables.append(table)
            
            is_valid = len(blocked_tables) == 0
            
            if not is_valid:
                logger.warning(f"SQL query blocked due to unauthorized tables: {blocked_tables}")
                self.blocked_operations.add(f"sql_query_blocked:{','.join(blocked_tables)}")
            
            return is_valid, allowed_tables, blocked_tables
            
        except Exception as e:
            logger.error(f"Error validating SQL tables: {e}")
            return False, [], []
    
    def _extract_tables_from_sql(self, sql_query: str) -> List[str]:
        """Extract table names from SQL query"""
        import re
        
        # Convert to uppercase for consistent matching
        sql_upper = sql_query.upper()
        
        # Find table names after FROM and JOIN keywords
        table_patterns = [
            r'FROM\s+(\w+)',
            r'JOIN\s+(\w+)',
            r'UPDATE\s+(\w+)',
            r'INTO\s+(\w+)',
            r'TABLE\s+(\w+)'
        ]
        
        tables = set()
        for pattern in table_patterns:
            matches = re.findall(pattern, sql_upper)
            tables.update(matches)
        
        return list(tables)
    
    def get_security_info(self) -> SecurityInfo:
        """Get security information"""
        return SecurityInfo(
            allowed_tables=self.get_allowed_tables(),
            blocked_operations=list(self.blocked_operations),
            data_modification_blocked=len(self.blocked_operations) > 0
        )
    
    def reset_blocked_operations(self):
        """Reset blocked operations counter"""
        self.blocked_operations.clear()
        logger.info("Blocked operations counter reset")
    
    def is_data_modification_blocked(self) -> bool:
        """Check if data modification is blocked"""
        return len(self.blocked_operations) > 0


class TableAllowlistManager:
    """Manager for table allowlist operations"""
    
    def __init__(self):
        self.allowlist = TableAllowlist()
    
    def validate_query(self, sql_query: str) -> tuple[bool, str, SecurityInfo]:
        """
        Validate a SQL query against allowlist
        
        Args:
            sql_query: SQL query to validate
            
        Returns:
            Tuple of (is_valid, error_message, security_info)
        """
        is_valid, allowed_tables, blocked_tables = self.allowlist.validate_sql_tables(sql_query)
        
        if is_valid:
            error_message = ""
        else:
            # Try to include suggestions for common aliases
            suggestions = []
            for t in blocked_tables:
                n = t.strip().strip('"').strip("'").lower()
                sugg = (
                    self.allowlist._typo_to_canonical.get(n)
                    or self.allowlist._generic_to_canonical.get(n)
                )
                if sugg:
                    suggestions.append(f"{t}→{sugg}")
            suggestion_text = f" Suggestions: {', '.join(suggestions)}." if suggestions else ""
            error_message = (
                f"Access denied to tables: {', '.join(blocked_tables)}. "
                f"Allowed tables: {', '.join(self.allowlist.get_allowed_tables())}." + suggestion_text
            )
        
        security_info = self.allowlist.get_security_info()
        
        return is_valid, error_message, security_info
    
    def get_allowed_tables(self) -> List[str]:
        """Get allowed tables"""
        return self.allowlist.get_allowed_tables()
    
    
    def get_security_info(self) -> SecurityInfo:
        """Get security information"""
        return self.allowlist.get_security_info()
