"""
Security module for access control and validation
"""
from .table_allowlist import TableAllowlist, TableAllowlistManager

__all__ = ['TableAllowlist', 'TableAllowlistManager']
