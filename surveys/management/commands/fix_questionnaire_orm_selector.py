from django.core.management.base import BaseCommand
from django.db import models, connection
from surveys.models import Questionnaire
from surveys.data.selector_data import (
    QUESTIONNAIRE_CATEGORIES,
    QUESTIONNAIRE_TYPES,
    QUESTIONNAIRE_STATUSES
)

class Command(BaseCommand):
    help = 'Fix questionnaire ORM selector by adding choices to model fields and updating database values'

    def handle(self, *args, **options):
        # First, ensure the model has the proper choices
        self.add_choices_to_model()

        # Then, update any invalid values in the database
        self.update_invalid_values()

        self.stdout.write(self.style.SUCCESS('Successfully fixed questionnaire ORM selector'))

    def add_choices_to_model(self):
        """Add choices to the model fields"""
        # Add category choices
        if not hasattr(Questionnaire, 'CATEGORY_CHOICES'):
            Questionnaire.CATEGORY_CHOICES = QUESTIONNAIRE_CATEGORIES
            self.stdout.write(self.style.SUCCESS('Added CATEGORY_CHOICES to Questionnaire model'))

        # Add type choices
        if not hasattr(Questionnaire, 'TYPE_CHOICES'):
            Questionnaire.TYPE_CHOICES = QUESTIONNAIRE_TYPES
            self.stdout.write(self.style.SUCCESS('Added TYPE_CHOICES to Questionnaire model'))

        # Add status choices
        if not hasattr(Questionnaire, 'STATUS_CHOICES'):
            Questionnaire.STATUS_CHOICES = QUESTIONNAIRE_STATUSES
            self.stdout.write(self.style.SUCCESS('Added STATUS_CHOICES to Questionnaire model'))

        # Update field choices if they exist
        try:
            category_field = Questionnaire._meta.get_field('category')
            if not category_field.choices:
                category_field.choices = QUESTIONNAIRE_CATEGORIES
                self.stdout.write(self.style.SUCCESS('Updated category field choices'))
        except models.FieldDoesNotExist:
            self.stdout.write(self.style.WARNING('Category field not found'))

        try:
            type_field = Questionnaire._meta.get_field('type')
            if not type_field.choices:
                type_field.choices = QUESTIONNAIRE_TYPES
                self.stdout.write(self.style.SUCCESS('Updated type field choices'))
        except models.FieldDoesNotExist:
            self.stdout.write(self.style.WARNING('Type field not found'))

        try:
            status_field = Questionnaire._meta.get_field('status')
            if not status_field.choices:
                status_field.choices = QUESTIONNAIRE_STATUSES
                self.stdout.write(self.style.SUCCESS('Updated status field choices'))
        except models.FieldDoesNotExist:
            self.stdout.write(self.style.WARNING('Status field not found'))

    def update_invalid_values(self):
        """Update invalid values in the database"""
        # Get valid values
        valid_categories = [code for code, _ in QUESTIONNAIRE_CATEGORIES]
        valid_types = [code for code, _ in QUESTIONNAIRE_TYPES]
        valid_statuses = [code for code, _ in QUESTIONNAIRE_STATUSES]

        # Set default values
        default_category = valid_categories[0] if valid_categories else 'general'
        default_type = valid_types[0] if valid_types else 'standard'
        default_status = valid_statuses[0] if valid_statuses else 'draft'

        # Update questionnaires with invalid or empty category values
        category_updates = 0
        for questionnaire in Questionnaire.objects.filter(
            models.Q(category__isnull=True) |
            ~models.Q(category__in=valid_categories)
        ):
            questionnaire.category = default_category
            questionnaire.save(update_fields=['category'])
            category_updates += 1

        # Update questionnaires with invalid or empty type values
        type_updates = 0
        for questionnaire in Questionnaire.objects.filter(
            models.Q(type__isnull=True) |
            ~models.Q(type__in=valid_types)
        ):
            questionnaire.type = default_type
            questionnaire.save(update_fields=['type'])
            type_updates += 1

        # Update questionnaires with invalid or empty status values
        status_updates = 0
        for questionnaire in Questionnaire.objects.filter(
            models.Q(status__isnull=True) |
            ~models.Q(status__in=valid_statuses)
        ):
            questionnaire.status = default_status
            questionnaire.save(update_fields=['status'])
            status_updates += 1

        self.stdout.write(self.style.SUCCESS(
            f'Updated questionnaires: {category_updates} categories, {type_updates} types, {status_updates} statuses'
        ))

        # Also update the database schema if needed
        self.ensure_field_constraints()

    def ensure_field_constraints(self):
        """Ensure the database fields have the proper constraints"""
        # Get the database engine
        db_engine = connection.vendor

        # SQLite doesn't support check constraints in the same way as PostgreSQL
        # For SQLite, we'll skip this step
        if db_engine == 'sqlite':
            self.stdout.write(self.style.WARNING(
                'SQLite database detected. Skipping constraint checks. '
                'Constraints will be enforced by the Django ORM.'
            ))
            return

        # For PostgreSQL, we can add check constraints
        if db_engine == 'postgresql':
            valid_categories = [code for code, _ in QUESTIONNAIRE_CATEGORIES]
            valid_types = [code for code, _ in QUESTIONNAIRE_TYPES]
            valid_statuses = [code for code, _ in QUESTIONNAIRE_STATUSES]

            with connection.cursor() as cursor:
                # Check if the category field has a check constraint
                cursor.execute("""
                    SELECT COUNT(*) FROM information_schema.check_constraints
                    WHERE constraint_schema = 'public'
                    AND check_clause LIKE '%category%'
                    AND constraint_name LIKE '%surveys_questionnaire%'
                """)
                has_category_constraint = cursor.fetchone()[0] > 0

                # Check if the type field has a check constraint
                cursor.execute("""
                    SELECT COUNT(*) FROM information_schema.check_constraints
                    WHERE constraint_schema = 'public'
                    AND check_clause LIKE '%type%'
                    AND constraint_name LIKE '%surveys_questionnaire%'
                """)
                has_type_constraint = cursor.fetchone()[0] > 0

                # Check if the status field has a check constraint
                cursor.execute("""
                    SELECT COUNT(*) FROM information_schema.check_constraints
                    WHERE constraint_schema = 'public'
                    AND check_clause LIKE '%status%'
                    AND constraint_name LIKE '%surveys_questionnaire%'
                """)
                has_status_constraint = cursor.fetchone()[0] > 0

                # Add constraints if needed
                if not has_category_constraint and valid_categories:
                    try:
                        values_str = "', '".join(valid_categories)
                        cursor.execute(f"""
                            ALTER TABLE surveys_questionnaire
                            ADD CONSTRAINT surveys_questionnaire_category_check
                            CHECK (category IS NULL OR category IN ('{values_str}'))
                        """)
                        self.stdout.write(self.style.SUCCESS('Added category constraint to database'))
                    except Exception as e:
                        self.stdout.write(self.style.ERROR(f'Error adding category constraint: {e}'))

                if not has_type_constraint and valid_types:
                    try:
                        values_str = "', '".join(valid_types)
                        cursor.execute(f"""
                            ALTER TABLE surveys_questionnaire
                            ADD CONSTRAINT surveys_questionnaire_type_check
                            CHECK (type IS NULL OR type IN ('{values_str}'))
                        """)
                        self.stdout.write(self.style.SUCCESS('Added type constraint to database'))
                    except Exception as e:
                        self.stdout.write(self.style.ERROR(f'Error adding type constraint: {e}'))

                if not has_status_constraint and valid_statuses:
                    try:
                        values_str = "', '".join(valid_statuses)
                        cursor.execute(f"""
                            ALTER TABLE surveys_questionnaire
                            ADD CONSTRAINT surveys_questionnaire_status_check
                            CHECK (status IS NULL OR status IN ('{values_str}'))
                        """)
                        self.stdout.write(self.style.SUCCESS('Added status constraint to database'))
                    except Exception as e:
                        self.stdout.write(self.style.ERROR(f'Error adding status constraint: {e}'))
        else:
            self.stdout.write(self.style.WARNING(
                f'Database engine {db_engine} not supported for adding constraints. '
                'Constraints will be enforced by the Django ORM.'
            ))
