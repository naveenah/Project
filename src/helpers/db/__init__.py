"""
Database helper utilities.

This module provides database-related helper functions and SQL statements.
"""

from .statements import (
    create_schema_if_not_exists,
    drop_schema_if_exists,
    set_active_schema,
    get_active_schema,
    set_search_path,
    reset_search_path,
    schema_exists,
    list_schemas,
    PROTECTED_SCHEMAS
)

__all__ = [
    'create_schema_if_not_exists',
    'drop_schema_if_exists',
    'set_active_schema',
    'get_active_schema',
    'set_search_path',
    'reset_search_path',
    'schema_exists',
    'list_schemas',
    'PROTECTED_SCHEMAS'
]
