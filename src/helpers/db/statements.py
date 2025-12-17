"""
Database SQL statements and utilities.

This module contains reusable SQL statements and functions for database operations.
"""
import logging
from django.db import connection

logger = logging.getLogger(__name__)


def create_schema_if_not_exists(schema_name):
    """
    Create a database schema if it doesn't already exist.
    
    This function executes a SQL statement to create a schema in PostgreSQL.
    It is safe to run multiple times as it uses CREATE SCHEMA IF NOT EXISTS.
    
    Args:
        schema_name (str): The name of the schema to create.
        
    Returns:
        bool: True if the operation was successful, False otherwise.
        
    Example:
        >>> create_schema_if_not_exists('my_app_schema')
        True
        
    Note:
        This function is designed for PostgreSQL. For SQLite (which doesn't 
        support schemas), it will log a warning and return True without error.
    """
    # Validate schema name to prevent SQL injection
    if not schema_name or not schema_name.replace('_', '').isalnum():
        logger.error(f"Invalid schema name: {schema_name}")
        return False
    
    # SQL statement to create schema if not exists
    sql_statement = f"CREATE SCHEMA IF NOT EXISTS {schema_name};"
    
    try:
        with connection.cursor() as cursor:
            # Check if we're using PostgreSQL
            db_vendor = connection.vendor
            
            if db_vendor == 'postgresql':
                logger.info(f"Creating schema '{schema_name}' if not exists...")
                cursor.execute(sql_statement)
                logger.info(f"Schema '{schema_name}' ready.")
                return True
            elif db_vendor == 'sqlite':
                logger.warning(
                    f"SQLite doesn't support schemas. Skipping schema '{schema_name}' creation."
                )
                return True
            else:
                logger.warning(
                    f"Database vendor '{db_vendor}' may not support schema creation. "
                    f"Attempting to create schema '{schema_name}'..."
                )
                cursor.execute(sql_statement)
                logger.info(f"Schema '{schema_name}' created or already exists.")
                return True
                
    except Exception as e:
        logger.error(
            f"Error creating schema '{schema_name}': {e}",
            exc_info=True
        )
        return False


# Raw SQL statements for reference
CREATE_SCHEMA_TEMPLATE = """
CREATE SCHEMA IF NOT EXISTS {schema_name};
"""

DROP_SCHEMA_TEMPLATE = """
DROP SCHEMA IF EXISTS {schema_name} CASCADE;
"""

SET_SEARCH_PATH_TEMPLATE = """
SET search_path TO {schema_name};
"""

# Protected schemas that should not be dropped
PROTECTED_SCHEMAS = ['public', 'pg_catalog', 'information_schema', 'pg_toast']


def drop_schema_if_exists(schema_name, cascade=True, force=False):
    """
    Drop a database schema if it exists.
    
    This function executes a SQL statement to drop a schema in PostgreSQL.
    By default, it uses CASCADE to drop all objects in the schema.
    
    Args:
        schema_name (str): The name of the schema to drop.
        cascade (bool): If True, drops all objects in the schema. Default True.
        force (bool): If True, allows dropping protected schemas. Default False.
        
    Returns:
        bool: True if the operation was successful, False otherwise.
        
    Example:
        >>> drop_schema_if_exists('old_schema')
        True
        
        >>> drop_schema_if_exists('public', force=True)
        True
        
    Warning:
        Using CASCADE will delete all tables, views, and other objects in the schema.
        Protected schemas (public, pg_catalog, etc.) require force=True.
    """
    # Validate schema name to prevent SQL injection
    if not schema_name or not schema_name.replace('_', '').isalnum():
        logger.error(f"Invalid schema name: {schema_name}")
        return False
    
    # Check if schema is protected
    if schema_name in PROTECTED_SCHEMAS and not force:
        logger.error(
            f"Cannot drop protected schema '{schema_name}'. "
            f"Use force=True to override this protection."
        )
        return False
    
    # Build SQL statement
    cascade_clause = "CASCADE" if cascade else "RESTRICT"
    sql_statement = f"DROP SCHEMA IF EXISTS {schema_name} {cascade_clause};"
    
    try:
        with connection.cursor() as cursor:
            # Check if we're using PostgreSQL
            db_vendor = connection.vendor
            
            if db_vendor == 'postgresql':
                logger.warning(
                    f"Dropping schema '{schema_name}' with {cascade_clause}..."
                )
                cursor.execute(sql_statement)
                logger.info(f"Schema '{schema_name}' dropped successfully.")
                return True
            elif db_vendor == 'sqlite':
                logger.warning(
                    f"SQLite doesn't support schemas. Skipping drop for '{schema_name}'."
                )
                return True
            else:
                logger.warning(
                    f"Database vendor '{db_vendor}' may not support schema dropping. "
                    f"Attempting to drop schema '{schema_name}'..."
                )
                cursor.execute(sql_statement)
                logger.info(f"Schema '{schema_name}' dropped.")
                return True
                
    except Exception as e:
        logger.error(
            f"Error dropping schema '{schema_name}': {e}",
            exc_info=True
        )
        return False


def drop_multiple_schemas(schema_names, cascade=True, force=False):
    """
    Drop multiple database schemas if they exist.
    
    Args:
        schema_names (list): List of schema names to drop.
        cascade (bool): If True, drops all objects in each schema. Default True.
        force (bool): If True, allows dropping protected schemas. Default False.
        
    Returns:
        dict: Dictionary with schema names as keys and success status as values.
        
    Example:
        >>> drop_multiple_schemas(['schema1', 'schema2', 'schema3'])
        {'schema1': True, 'schema2': True, 'schema3': False}
    """
    results = {}
    for schema_name in schema_names:
        results[schema_name] = drop_schema_if_exists(schema_name, cascade, force)
    return results


def set_active_schema(schema_name):
    """
    Set the active schema (search_path) for the current database session.
    
    This function sets the PostgreSQL search_path to the specified schema,
    making it the default schema for subsequent queries in the session.
    
    Args:
        schema_name (str): The name of the schema to activate.
        
    Returns:
        bool: True if the operation was successful, False otherwise.
        
    Example:
        >>> set_active_schema('my_app_schema')
        True
        
    Note:
        The search_path change only affects the current database connection.
        In Django, this typically affects the current request/thread.
    """
    # Validate schema name to prevent SQL injection
    if not schema_name or not schema_name.replace('_', '').isalnum():
        logger.error(f"Invalid schema name: {schema_name}")
        return False
    
    # SQL statement to set search_path
    sql_statement = f"SET search_path TO {schema_name};"
    
    try:
        with connection.cursor() as cursor:
            # Check if we're using PostgreSQL
            db_vendor = connection.vendor
            
            if db_vendor == 'postgresql':
                # First check if schema exists
                if not schema_exists(schema_name):
                    logger.error(f"Cannot set active schema. Schema '{schema_name}' does not exist.")
                    return False
                
                logger.info(f"Setting active schema to '{schema_name}'...")
                cursor.execute(sql_statement)
                logger.info(f"Active schema set to '{schema_name}'.")
                return True
            elif db_vendor == 'sqlite':
                logger.warning(
                    f"SQLite doesn't support schemas. Cannot set active schema '{schema_name}'."
                )
                return True
            else:
                logger.warning(
                    f"Database vendor '{db_vendor}' may not support search_path. "
                    f"Attempting to set active schema to '{schema_name}'..."
                )
                cursor.execute(sql_statement)
                logger.info(f"Active schema set to '{schema_name}'.")
                return True
                
    except Exception as e:
        logger.error(
            f"Error setting active schema to '{schema_name}': {e}",
            exc_info=True
        )
        return False


def get_active_schema():
    """
    Get the current active schema (search_path) for the database session.
    
    Returns:
        str or None: The current schema name, or None if unable to determine.
        
    Example:
        >>> get_active_schema()
        'public'
    """
    try:
        with connection.cursor() as cursor:
            db_vendor = connection.vendor
            
            if db_vendor == 'postgresql':
                cursor.execute("SHOW search_path;")
                result = cursor.fetchone()
                if result:
                    # search_path can be comma-separated, get the first one
                    search_path = result[0]
                    # Remove quotes and spaces, get first schema
                    schema = search_path.split(',')[0].strip().strip('"')
                    return schema
                return None
            elif db_vendor == 'sqlite':
                logger.info("SQLite doesn't support schemas, returning None")
                return None
            else:
                logger.warning(f"Getting active schema not implemented for {db_vendor}")
                return None
                
    except Exception as e:
        logger.error(f"Error getting active schema: {e}", exc_info=True)
        return None


def set_search_path(schema_names, include_public=True):
    """
    Set the search_path to multiple schemas in priority order.
    
    This allows queries to search multiple schemas in the specified order.
    
    Args:
        schema_names (list): List of schema names in priority order.
        include_public (bool): If True, includes 'public' schema at the end. Default True.
        
    Returns:
        bool: True if the operation was successful, False otherwise.
        
    Example:
        >>> set_search_path(['tenant1', 'shared'])
        True
        
        >>> set_search_path(['app_schema', 'public'], include_public=False)
        True
    """
    if not schema_names:
        logger.error("No schema names provided for search_path")
        return False
    
    # Validate all schema names
    for schema_name in schema_names:
        if not schema_name or not schema_name.replace('_', '').isalnum():
            logger.error(f"Invalid schema name in list: {schema_name}")
            return False
    
    # Build the search path
    search_path_list = schema_names.copy()
    if include_public and 'public' not in search_path_list:
        search_path_list.append('public')
    
    search_path_str = ', '.join(search_path_list)
    sql_statement = f"SET search_path TO {search_path_str};"
    
    try:
        with connection.cursor() as cursor:
            db_vendor = connection.vendor
            
            if db_vendor == 'postgresql':
                logger.info(f"Setting search_path to: {search_path_str}")
                cursor.execute(sql_statement)
                logger.info(f"Search path set successfully.")
                return True
            elif db_vendor == 'sqlite':
                logger.warning("SQLite doesn't support schemas.")
                return True
            else:
                logger.warning(
                    f"Search path setting may not be supported for {db_vendor}"
                )
                cursor.execute(sql_statement)
                return True
                
    except Exception as e:
        logger.error(
            f"Error setting search_path to '{search_path_str}': {e}",
            exc_info=True
        )
        return False


def reset_search_path():
    """
    Reset the search_path to the default (typically 'public').
    
    Returns:
        bool: True if the operation was successful, False otherwise.
        
    Example:
        >>> reset_search_path()
        True
    """
    return set_active_schema('public')

# Example: Create multiple schemas
def create_multiple_schemas(schema_names):
    """
    Create multiple database schemas if they don't already exist.
    
    Args:
        schema_names (list): List of schema names to create.
        
    Returns:
        dict: Dictionary with schema names as keys and success status as values.
        
    Example:
        >>> create_multiple_schemas(['schema1', 'schema2', 'schema3'])
        {'schema1': True, 'schema2': True, 'schema3': False}
    """
    results = {}
    for schema_name in schema_names:
        results[schema_name] = create_schema_if_not_exists(schema_name)
    return results


# Example: Check if schema exists
def schema_exists(schema_name):
    """
    Check if a schema exists in the database.
    
    Args:
        schema_name (str): The name of the schema to check.
        
    Returns:
        bool: True if schema exists, False otherwise.
        
    Example:
        >>> schema_exists('public')
        True
    """
    try:
        with connection.cursor() as cursor:
            db_vendor = connection.vendor
            
            if db_vendor == 'postgresql':
                cursor.execute(
                    """
                    SELECT schema_name 
                    FROM information_schema.schemata 
                    WHERE schema_name = %s;
                    """,
                    [schema_name]
                )
                result = cursor.fetchone()
                return result is not None
            elif db_vendor == 'sqlite':
                # SQLite doesn't have schemas
                return True
            else:
                logger.warning(f"Schema existence check not implemented for {db_vendor}")
                return False
                
    except Exception as e:
        logger.error(f"Error checking if schema '{schema_name}' exists: {e}", exc_info=True)
        return False


# Example: List all schemas
def list_schemas():
    """
    List all schemas in the database.
    
    Returns:
        list: List of schema names.
        
    Example:
        >>> list_schemas()
        ['public', 'my_app_schema', 'another_schema']
    """
    try:
        with connection.cursor() as cursor:
            db_vendor = connection.vendor
            
            if db_vendor == 'postgresql':
                cursor.execute(
                    """
                    SELECT schema_name 
                    FROM information_schema.schemata 
                    WHERE schema_name NOT IN ('pg_catalog', 'information_schema')
                    ORDER BY schema_name;
                    """
                )
                return [row[0] for row in cursor.fetchall()]
            elif db_vendor == 'sqlite':
                logger.info("SQLite doesn't support schemas")
                return []
            else:
                logger.warning(f"Schema listing not implemented for {db_vendor}")
                return []
                
    except Exception as e:
        logger.error(f"Error listing schemas: {e}", exc_info=True)
        return []
