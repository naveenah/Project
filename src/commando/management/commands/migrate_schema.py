"""
Django management command to migrate a specific schema.

This command creates a schema (if it doesn't exist), activates it,
and runs Django migrations on that schema.
Useful for multi-tenant applications where each tenant has their own schema.
"""

import logging
from django.core.management import call_command
from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from genapp.installed import _CUSTOMER_INSTALLED_APPS
from helpers.db.statements import (
    create_schema_if_not_exists,
    set_active_schema,
    get_active_schema,
    reset_search_path,
    schema_exists,
    list_schemas,
    PROTECTED_SCHEMAS
)

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Create schema, activate it, and run migrations on the specified schema.'

    def add_arguments(self, parser):
        """
        Add command line arguments.
        """
        parser.add_argument(
            'schema_name',
            nargs='?',
            type=str,
            help='Name of the schema to migrate. If not provided, shows current schema.'
        )
        
        parser.add_argument(
            '--list',
            action='store_true',
            help='List all existing schemas in the database'
        )
        
        parser.add_argument(
            '--current',
            action='store_true',
            help='Show the current active schema'
        )
        
        parser.add_argument(
            '--check',
            type=str,
            help='Check if a specific schema exists'
        )
        
        parser.add_argument(
            '--no-create',
            action='store_true',
            help='Do not create schema if it does not exist (only activate and migrate)'
        )
        
        parser.add_argument(
            '--no-migrate',
            action='store_true',
            help='Only create and activate schema, do not run migrations'
        )
        
        parser.add_argument(
            '--fake',
            action='store_true',
            help='Mark migrations as run without actually running them'
        )
        
        parser.add_argument(
            '--app',
            type=str,
            help='Run migrations only for the specified app'
        )
        
        parser.add_argument(
            '--all',
            action='store_true',
            help='Migrate all schemas including public and sub-schemas'
        )

    def handle_migrate_all(self, options):
        """
        Migrate all schemas in the database.
        """
        self.stdout.write(
            self.style.SUCCESS('\n🚀 Migrating ALL schemas in database\n')
        )
        
        # Get all schemas
        all_schemas = list_schemas()
        
        if not all_schemas:
            self.stdout.write(
                self.style.WARNING('⚠️  No schemas found or database does not support schemas.\n')
            )
            return
        
        # Filter out system schemas we shouldn't migrate
        system_schemas = ['pg_toast', 'pg_catalog', 'information_schema']
        schemas_to_migrate = [s for s in all_schemas if s not in system_schemas]
        
        if not schemas_to_migrate:
            self.stdout.write(
                self.style.WARNING('⚠️  No user schemas found to migrate.\n')
            )
            return
        
        self.stdout.write(f'📋 Found {len(schemas_to_migrate)} schema(s) to migrate:\n')
        for schema in schemas_to_migrate:
            self.stdout.write(f'  • {schema}')
        self.stdout.write('')
        
        # Store original schema
        original_schema = get_active_schema()
        
        # Track results
        results = {
            'success': [],
            'failed': [],
            'skipped': []
        }
        
        # Migrate each schema
        for idx, schema_name in enumerate(schemas_to_migrate, 1):
            self.stdout.write(
                self.style.SUCCESS(f'\n{"="*60}')
            )
            self.stdout.write(
                self.style.SUCCESS(f'[{idx}/{len(schemas_to_migrate)}] Processing schema: {schema_name}')
            )
            self.stdout.write(
                self.style.SUCCESS(f'{"="*60}\n')
            )
            
            try:
                # Activate schema
                self.stdout.write(f'🔄 Activating schema: {schema_name}')
                success = set_active_schema(schema_name)
                
                if not success:
                    self.stdout.write(
                        self.style.ERROR(f'  ❌ Failed to activate schema: {schema_name}')
                    )
                    results['failed'].append(schema_name)
                    continue
                
                self.stdout.write(
                    self.style.SUCCESS(f'  ✅ Schema activated: {schema_name}\n')
                )
                
                # Run migrations if not disabled
                if not options['no_migrate']:
                    self.stdout.write(f'🔧 Running migrations on schema: {schema_name}\n')
                    
                    # Build migrate command options
                    migrate_options = {
                        'verbosity': options.get('verbosity', 1),
                        'interactive': False,
                    }
                    
                    if options['fake']:
                        migrate_options['fake'] = True
                        self.stdout.write(
                            self.style.WARNING('  ⚠️  Running in FAKE mode\n')
                        )
                    
                    if options['app']:
                        # Migrate specific app
                        app_label = options['app']
                        self.stdout.write(f'  Migrating app: {app_label}')
                        call_command('migrate', app_label, **migrate_options)
                    else:
                        # Migrate only customer apps
                        for app in _CUSTOMER_INSTALLED_APPS:
                            # Extract app name from dotted path (e.g., 'ai_agent_gateway.apps.AgentGatewayConfig' -> 'ai_agent_gateway')
                            app_label = app.split('.')[0]
                            try:
                                call_command('migrate', app_label, **migrate_options)
                            except Exception as e:
                                self.stdout.write(
                                    self.style.WARNING(f'  ⚠️  Skipped {app_label}: {e}')
                                )
                    
                    self.stdout.write(
                        self.style.SUCCESS(f'\n  ✅ Migrations completed for: {schema_name}')
                    )
                else:
                    self.stdout.write(
                        self.style.WARNING('  ⚠️  Skipped migrations (--no-migrate flag)')
                    )
                
                results['success'].append(schema_name)
                
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'\n  ❌ Error processing schema {schema_name}: {e}')
                )
                results['failed'].append(schema_name)
                logger.error(f"Failed to migrate schema {schema_name}: {e}", exc_info=True)
        
        # Restore original schema
        self.stdout.write(
            self.style.SUCCESS(f'\n{"="*60}')
        )
        self.stdout.write('🔙 Restoring original schema...')
        
        if original_schema:
            reset_success = set_active_schema(original_schema)
            if reset_success:
                self.stdout.write(
                    self.style.SUCCESS(f'  ✅ Restored to schema: {original_schema}')
                )
            else:
                self.stdout.write(
                    self.style.WARNING(f'  ⚠️  Could not restore to original schema: {original_schema}')
                )
        else:
            self.stdout.write(
                self.style.WARNING('  ⚠️  Original schema unknown, using default')
            )
            reset_search_path()
        
        # Print summary
        self.stdout.write(
            self.style.SUCCESS(f'\n{"="*60}')
        )
        self.stdout.write(
            self.style.SUCCESS('✨ MIGRATION SUMMARY')
        )
        self.stdout.write(
            self.style.SUCCESS(f'{"="*60}\n')
        )
        
        self.stdout.write(f'📊 Total schemas processed: {len(schemas_to_migrate)}')
        
        if results['success']:
            self.stdout.write(
                self.style.SUCCESS(f'  ✅ Successful: {len(results["success"])}')
            )
            for schema in results['success']:
                self.stdout.write(f'     • {schema}')
        
        if results['failed']:
            self.stdout.write(
                self.style.ERROR(f'  ❌ Failed: {len(results["failed"])}')
            )
            for schema in results['failed']:
                self.stdout.write(f'     • {schema}')
        
        if results['skipped']:
            self.stdout.write(
                self.style.WARNING(f'  ⚠️  Skipped: {len(results["skipped"])}')
            )
            for schema in results['skipped']:
                self.stdout.write(f'     • {schema}')
        
        self.stdout.write(f'\n  Current schema: {get_active_schema()}')
        self.stdout.write('')
        
        # Exit with error code if any failed
        if results['failed']:
            raise CommandError(
                f"Failed to migrate {len(results['failed'])} schema(s). See output above for details."
            )

    def handle(self, *args, **options):
        """
        Execute the command.
        """
        # Migrate all schemas
        if options['all']:
            self.handle_migrate_all(options)
            return
        
        # List schemas
        if options['list']:
            self.stdout.write(self.style.SUCCESS('\n📋 Listing all schemas:'))
            schemas = list_schemas()
            if schemas:
                current_schema = get_active_schema()
                for schema in schemas:
                    if schema == current_schema:
                        self.stdout.write(
                            self.style.SUCCESS(f"  ✅ {schema} (ACTIVE)")
                        )
                    else:
                        self.stdout.write(f"  • {schema}")
            else:
                self.stdout.write("  No schemas found or database doesn't support schemas.")
            return

        # Show current schema
        if options['current']:
            current = get_active_schema()
            if current:
                self.stdout.write(
                    self.style.SUCCESS(f'\n✅ Current active schema: {current}\n')
                )
            else:
                self.stdout.write(
                    self.style.WARNING('\n⚠️  Could not determine current schema.\n')
                )
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

        # Get schema name
        schema_name = options.get('schema_name')
        
        # If no schema provided, show current and exit
        if not schema_name:
            current = get_active_schema()
            if current:
                self.stdout.write(
                    self.style.SUCCESS(f'\n✅ Current active schema: {current}')
                )
                self.stdout.write(
                    '\nTo migrate a schema, provide its name:'
                    '\n  python manage.py migrate_schema my_schema'
                )
            else:
                self.stdout.write(
                    self.style.ERROR('\n❌ Error: No schema name provided.')
                )
                self.stdout.write(
                    '\nUsage examples:'
                    '\n  python manage.py migrate_schema my_schema'
                    '\n  python manage.py migrate_schema tenant1 --app myapp'
                    '\n  python manage.py migrate_schema new_schema --no-migrate'
                    '\n  python manage.py migrate_schema --current'
                    '\n  python manage.py migrate_schema --list'
                )
            return

        self.stdout.write(
            self.style.SUCCESS(f'\n🚀 Migrating schema: {schema_name}\n')
        )

        # Step 1: Create schema if needed
        if not options['no_create']:
            self.stdout.write('📦 Step 1: Creating schema...')
            
            if schema_exists(schema_name):
                self.stdout.write(
                    self.style.WARNING(f"  ⚠️  Schema '{schema_name}' already exists. Skipping creation.")
                )
            else:
                success = create_schema_if_not_exists(schema_name)
                
                if success:
                    self.stdout.write(
                        self.style.SUCCESS(f"  ✅ Schema '{schema_name}' created successfully.")
                    )
                else:
                    self.stdout.write(
                        self.style.ERROR(f"  ❌ Failed to create schema '{schema_name}'.")
                    )
                    raise CommandError(f"Failed to create schema '{schema_name}'")
        else:
            # Check if schema exists when --no-create is used
            if not schema_exists(schema_name):
                self.stdout.write(
                    self.style.ERROR(f"  ❌ Schema '{schema_name}' does not exist and --no-create flag was used.")
                )
                raise CommandError(f"Schema '{schema_name}' does not exist. Remove --no-create flag to create it.")

        # Step 2: Activate schema
        self.stdout.write('\n🔄 Step 2: Activating schema...')
        
        # Store current schema to restore later
        original_schema = get_active_schema()
        
        success = set_active_schema(schema_name)
        
        if success:
            self.stdout.write(
                self.style.SUCCESS(f"  ✅ Schema '{schema_name}' activated.")
            )
        else:
            self.stdout.write(
                self.style.ERROR(f"  ❌ Failed to activate schema '{schema_name}'.")
            )
            raise CommandError(f"Failed to activate schema '{schema_name}'")

        # Step 3: Run migrations
        if not options['no_migrate']:
            self.stdout.write('\n🔧 Step 3: Running migrations...\n')
            
            try:
                # Build migrate command options
                migrate_options = {
                    'verbosity': options.get('verbosity', 1),
                    'interactive': False,
                }
                
                if options['fake']:
                    migrate_options['fake'] = True
                    self.stdout.write(
                        self.style.WARNING('  ⚠️  Running in FAKE mode (marking migrations as run)\n')
                    )
                
                if options['app']:
                    # Migrate specific app
                    app_label = options['app']
                    self.stdout.write(f"  Running migrations for app: {app_label}")
                    call_command('migrate', app_label, **migrate_options)
                else:
                    # Migrate only customer apps
                    for app in _CUSTOMER_INSTALLED_APPS:
                        # Extract app name from dotted path (e.g., 'ai_agent_gateway.apps.AgentGatewayConfig' -> 'ai_agent_gateway')
                        app_label = app.split('.')[0]
                        try:
                            call_command('migrate', app_label, **migrate_options)
                        except Exception as e:
                            self.stdout.write(
                                self.style.WARNING(f'  ⚠️  Skipped {app_label}: {e}')
                            )
                
                self.stdout.write(
                    self.style.SUCCESS(f'\n  ✅ Migrations completed for schema: {schema_name}')
                )
                
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'\n  ❌ Error running migrations: {e}')
                )
                # Restore original schema before raising error
                if original_schema:
                    reset_search_path()
                raise CommandError(f"Migration failed: {e}")
        else:
            self.stdout.write(
                self.style.WARNING('\n⚠️  Step 3: Skipped migrations (--no-migrate flag used)')
            )

        # Step 4: Restore original schema
        self.stdout.write('\n🔙 Step 4: Restoring original schema...')
        
        if original_schema:
            reset_success = set_active_schema(original_schema)
            if reset_success:
                self.stdout.write(
                    self.style.SUCCESS(f"  ✅ Restored to schema: {original_schema}")
                )
            else:
                self.stdout.write(
                    self.style.WARNING(f"  ⚠️  Could not restore to original schema: {original_schema}")
                )
        else:
            self.stdout.write(
                self.style.WARNING('  ⚠️  Original schema unknown, using default (public)')
            )
            reset_search_path()

        # Summary
        self.stdout.write(
            self.style.SUCCESS(f'\n✨ Schema migration complete for: {schema_name}\n')
        )
        
        # Show what was done
        self.stdout.write('📊 Summary:')
        if not options['no_create']:
            self.stdout.write(f"  • Schema created/verified: {schema_name}")
        self.stdout.write(f"  • Schema activated: {schema_name}")
        if not options['no_migrate']:
            if options['app']:
                self.stdout.write(f"  • Migrations run for app: {options['app']}")
            else:
                self.stdout.write('  • Migrations run: All apps')
        self.stdout.write(f"  • Current schema: {get_active_schema()}")
        self.stdout.write('')
