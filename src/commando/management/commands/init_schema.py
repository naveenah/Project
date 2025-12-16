"""
Django management command to initialize database schema.

This command creates a database schema if it doesn't already exist.
Useful for setting up multi-tenant applications or organizing database objects.
"""

import logging
from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from helpers.db.statements import (
    create_schema_if_not_exists,
    create_multiple_schemas,
    schema_exists,
    list_schemas
)

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Initialize database schema(s). Creates schema if it does not exist.'

    def add_arguments(self, parser):
        """
        Add command line arguments.
        """
        parser.add_argument(
            'schema_names',
            nargs='*',
            type=str,
            help='Name(s) of the schema(s) to create. If not provided, uses default from settings.'
        )
        
        parser.add_argument(
            '--list',
            action='store_true',
            help='List all existing schemas in the database'
        )
        
        parser.add_argument(
            '--check',
            type=str,
            help='Check if a specific schema exists'
        )
        
        parser.add_argument(
            '--default',
            action='store_true',
            help='Create default application schemas'
        )

    def handle(self, *args, **options):
        """
        Execute the command.
        """
        # List schemas
        if options['list']:
            self.stdout.write(self.style.SUCCESS('\n📋 Listing all schemas:'))
            schemas = list_schemas()
            if schemas:
                for schema in schemas:
                    self.stdout.write(f"  • {schema}")
            else:
                self.stdout.write("  No schemas found or database doesn't support schemas.")
            return

        # Check if schema exists
        if options['check']:
            schema_name = options['check']
            self.stdout.write(f"\n🔍 Checking if schema '{schema_name}' exists...")
            exists = schema_exists(schema_name)
            if exists:
                self.stdout.write(self.style.SUCCESS(f"  ✅ Schema '{schema_name}' exists."))
            else:
                self.stdout.write(self.style.WARNING(f"  ❌ Schema '{schema_name}' does not exist."))
            return

        # Get schema names to create
        schema_names = options['schema_names']
        
        # Use default schemas if --default flag is set
        if options['default']:
            default_schemas = getattr(settings, 'DEFAULT_SCHEMAS', ['public', 'app_data'])
            schema_names.extend(default_schemas)
            self.stdout.write(
                self.style.WARNING(f"\n📦 Using default schemas: {', '.join(default_schemas)}")
            )
        
        # If no schemas provided, show help
        if not schema_names:
            self.stdout.write(
                self.style.ERROR('\n❌ Error: No schema names provided.')
            )
            self.stdout.write(
                '\nUsage examples:'
                '\n  python manage.py init_schema my_schema'
                '\n  python manage.py init_schema schema1 schema2 schema3'
                '\n  python manage.py init_schema --default'
                '\n  python manage.py init_schema --list'
                '\n  python manage.py init_schema --check my_schema'
            )
            raise CommandError('No schema names provided. Use --help for usage.')

        # Remove duplicates while preserving order
        schema_names = list(dict.fromkeys(schema_names))
        
        self.stdout.write(
            self.style.SUCCESS(f'\n🚀 Initializing {len(schema_names)} schema(s)...\n')
        )

        # Create schemas
        if len(schema_names) == 1:
            # Single schema
            schema_name = schema_names[0]
            self.stdout.write(f"Creating schema: {schema_name}")
            
            success = create_schema_if_not_exists(schema_name)
            
            if success:
                self.stdout.write(
                    self.style.SUCCESS(f"  ✅ Schema '{schema_name}' created successfully or already exists.")
                )
            else:
                self.stdout.write(
                    self.style.ERROR(f"  ❌ Failed to create schema '{schema_name}'. Check logs for details.")
                )
                raise CommandError(f"Failed to create schema '{schema_name}'")
        else:
            # Multiple schemas
            results = create_multiple_schemas(schema_names)
            
            success_count = sum(1 for success in results.values() if success)
            failure_count = len(results) - success_count
            
            for schema_name, success in results.items():
                if success:
                    self.stdout.write(
                        self.style.SUCCESS(f"  ✅ {schema_name}")
                    )
                else:
                    self.stdout.write(
                        self.style.ERROR(f"  ❌ {schema_name} (FAILED)")
                    )
            
            # Summary
            self.stdout.write(
                self.style.SUCCESS(
                    f'\n📊 Summary: {success_count} succeeded, {failure_count} failed'
                )
            )
            
            if failure_count > 0:
                raise CommandError(f'{failure_count} schema(s) failed to create. Check logs for details.')
        
        self.stdout.write(
            self.style.SUCCESS('\n✨ Schema initialization complete!\n')
        )
