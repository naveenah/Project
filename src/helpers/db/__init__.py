"""
Database helper utilities.

This module provides database-related helper functions and SQL statements.
"""

from .statements import (
    create_schema_if_not_exists,
    drop_schema_if_exists,
    schema_exists,
    list_schemas,
    PROTECTED_SCHEMAS
)

__all__ = [
    'create_schema_if_not_exists',
    'drop_schema_if_exists',
    'schema_exists',
    'list_schemas',
    'PROTECTED_SCHEMAS'
]
