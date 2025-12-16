"""
Django management command to drop database schema(s).

This command drops database schemas if they exist.
Includes safety checks for protected schemas like 'public', 'pg_catalog', etc.
"""

import logging
from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from helpers.db.statements import (
    drop_schema_if_exists,
    drop_multiple_schemas,
    schema_exists,
    list_schemas,
    PROTECTED_SCHEMAS
)

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Drop database schema(s). Removes schema if it exists.'

    def add_arguments(self, parser):
        """
        Add command line arguments.
        """
        parser.add_argument(
            'schema_names',
            nargs='*',
            type=str,
            help='Name(s) of the schema(s) to drop.'
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
            '--force',
            action='store_true',
            help='Force drop of protected schemas (public, pg_catalog, etc.)'
        )
        
        parser.add_argument(
            '--restrict',
            action='store_true',
            help='Use RESTRICT instead of CASCADE (fails if schema has objects)'
        )
        
        parser.add_argument(
            '--confirm',
            action='store_true',
            help='Skip confirmation prompt (use with caution!)'
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
                    if schema in PROTECTED_SCHEMAS:
                        self.stdout.write(
                            self.style.WARNING(f"  🔒 {schema} (PROTECTED)")
                        )
                    else:
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

        # Get schema names to drop
        schema_names = options['schema_names']
        
        # If no schemas provided, show help
        if not schema_names:
            self.stdout.write(
                self.style.ERROR('\n❌ Error: No schema names provided.')
            )
            self.stdout.write(
                '\nUsage examples:'
                '\n  python manage.py drop_schema my_schema'
                '\n  python manage.py drop_schema schema1 schema2 schema3'
                '\n  python manage.py drop_schema old_schema --restrict'
                '\n  python manage.py drop_schema public --force --confirm'
                '\n  python manage.py drop_schema --list'
                '\n  python manage.py drop_schema --check my_schema'
            )
            raise CommandError('No schema names provided. Use --help for usage.')

        # Remove duplicates while preserving order
        schema_names = list(dict.fromkeys(schema_names))
        
        # Check for protected schemas
        protected_found = [name for name in schema_names if name in PROTECTED_SCHEMAS]
        if protected_found and not options['force']:
            self.stdout.write(
                self.style.ERROR(
                    f'\n🔒 Protected schemas detected: {", ".join(protected_found)}'
                )
            )
            self.stdout.write(
                self.style.WARNING(
                    '\nThese are critical system schemas. '
                    'Dropping them may cause database issues.'
                )
            )
            self.stdout.write(
                '\nUse --force flag if you really want to drop these schemas:'
                f'\n  python manage.py drop_schema {" ".join(schema_names)} --force --confirm'
            )
            raise CommandError('Cannot drop protected schemas without --force flag.')
        
        # Display warning
        cascade_mode = "RESTRICT" if options['restrict'] else "CASCADE"
        self.stdout.write(
            self.style.WARNING(
                f'\n⚠️  WARNING: You are about to DROP {len(schema_names)} schema(s)!'
            )
        )
        self.stdout.write(
            self.style.WARNING(
                f'   Mode: {cascade_mode}'
            )
        )
        
        if cascade_mode == "CASCADE":
            self.stdout.write(
                self.style.WARNING(
                    '   This will DELETE ALL OBJECTS (tables, views, functions, etc.) in the schema(s)!'
                )
            )
        
        self.stdout.write('\nSchemas to drop:')
        for schema_name in schema_names:
            if schema_name in PROTECTED_SCHEMAS:
                self.stdout.write(
                    self.style.ERROR(f"  🔒 {schema_name} (PROTECTED)")
                )
            else:
                self.stdout.write(f"  • {schema_name}")
        
        # Confirmation prompt
        if not options['confirm']:
            self.stdout.write(
                self.style.WARNING(
                    f'\nType "yes" to confirm, or "no" to cancel: '
                ),
                ending=''
            )
            confirmation = input()
            
            if confirmation.lower() != 'yes':
                self.stdout.write(
                    self.style.SUCCESS('\n✅ Operation cancelled. No schemas were dropped.')
                )
                return
        
        self.stdout.write(
            self.style.WARNING(f'\n🗑️  Dropping {len(schema_names)} schema(s)...\n')
        )

        # Determine cascade mode
        cascade = not options['restrict']
        force = options['force']

        # Drop schemas
        if len(schema_names) == 1:
            # Single schema
            schema_name = schema_names[0]
            self.stdout.write(f"Dropping schema: {schema_name}")
            
            success = drop_schema_if_exists(schema_name, cascade=cascade, force=force)
            
            if success:
                self.stdout.write(
                    self.style.SUCCESS(f"  ✅ Schema '{schema_name}' dropped successfully.")
                )
            else:
                self.stdout.write(
                    self.style.ERROR(f"  ❌ Failed to drop schema '{schema_name}'. Check logs for details.")
                )
                raise CommandError(f"Failed to drop schema '{schema_name}'")
        else:
            # Multiple schemas
            results = drop_multiple_schemas(schema_names, cascade=cascade, force=force)
            
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
                    f'\n📊 Summary: {success_count} dropped, {failure_count} failed'
                )
            )
            
            if failure_count > 0:
                raise CommandError(f'{failure_count} schema(s) failed to drop. Check logs for details.')
        
        self.stdout.write(
            self.style.SUCCESS('\n✨ Schema drop complete!\n')
        )
